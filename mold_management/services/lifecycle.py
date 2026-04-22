from __future__ import annotations

from functools import lru_cache

import frappe
from frappe import _

from mold_management.constants import (
	MOLD_STATUS_ACTIVE,
	MOLD_STATUS_ISSUED,
	MOLD_STATUS_OUTSOURCED,
	MOLD_STATUS_PENDING_ASSET_LINK,
	MOLD_STATUS_SCRAPPED,
	MOLD_STATUS_UNDER_EXTERNAL_MAINTENANCE,
	MOLD_STATUS_UNDER_MAINTENANCE,
	LIFECYCLE_DATETIME_FIELDS,
	OUTSOURCE_TYPE_EXTERNAL_MAINTENANCE,
)
from mold_management.services.storage import sync_mold_storage_location
from mold_management.services.versioning import normalize_version, version_sort_key


def handle_asset_change(doc, method=None):
	mold_name = _get_mold_name_from_asset(doc)
	if mold_name:
		sync_mold_lifecycle(mold_name)


def handle_asset_movement_change(doc, method=None):
	for row in doc.get("assets", []):
		mold_name = _get_mold_name_from_asset(row.asset)
		if not mold_name:
			continue

		if doc.docstatus == 1 and doc.purpose == "Receipt":
			frappe.db.set_value("Asset", row.asset, "custodian", None, update_modified=False)

		sync_mold_lifecycle(mold_name)


def handle_asset_repair_change(doc, method=None):
	mold_name = _get_mold_name_from_asset(doc.asset)
	if mold_name:
		sync_mold_lifecycle(mold_name)


def handle_asset_maintenance_log_change(doc, method=None):
	asset_name = frappe.db.get_value("Asset Maintenance", doc.asset_maintenance, "asset_name")
	mold_name = _get_mold_name_from_asset(asset_name)
	if mold_name:
		sync_mold_lifecycle(mold_name)


def sync_mold_lifecycle(mold_name: str):
	mold = frappe.get_doc("Mold", mold_name)
	asset_name = mold.linked_asset or frappe.db.get_value("Asset", {"custom_mold_management_mold": mold_name}, "name")
	asset = frappe.get_doc("Asset", asset_name) if asset_name else None

	values = {
		"status": _get_mold_status(mold_name, asset),
		"linked_asset": asset.name if asset else None,
		"current_version": _get_current_version(mold),
		"current_location": asset.location if asset else None,
		"current_warehouse": _get_current_warehouse(asset.name if asset else None) if asset else None,
		"current_storage_bin": _get_current_storage_bin(asset.name if asset else None) if asset else None,
	}
	values.update(_get_current_transaction_fields(mold_name, asset.name if asset else None))
	values.update(_get_recent_activity_dates(mold_name, asset.name if asset else None))

	if not values.get("current_warehouse"):
		values["current_warehouse"] = mold.default_warehouse
	if not values.get("current_location"):
		values["current_location"] = mold.default_location
	if not values.get("current_storage_bin"):
		values["current_storage_bin"] = mold.default_storage_bin

	values["current_holder_summary"] = _get_current_holder_summary(
		mold_name=mold_name,
		asset=asset,
		current_warehouse=values.get("current_warehouse"),
		current_location=values.get("current_location"),
		current_storage_bin=values.get("current_storage_bin"),
	)

	if asset and not mold.linked_asset:
		values["linked_asset"] = asset.name

	cleaned_values = sanitize_lifecycle_values(values)
	frappe.db.set_value("Mold", mold_name, cleaned_values, update_modified=False)
	sync_mold_storage_location(mold_name, cleaned_values)


def _get_mold_name_from_asset(asset_or_name) -> str | None:
	if not asset_or_name:
		return None

	if hasattr(asset_or_name, "doctype"):
		return getattr(asset_or_name, "custom_mold_management_mold", None)

	return frappe.db.get_value("Asset", asset_or_name, "custom_mold_management_mold")


def _get_mold_status(mold_name: str, asset) -> str:
	if not asset:
		return MOLD_STATUS_PENDING_ASSET_LINK

	if asset and asset.journal_entry_for_scrap:
		return MOLD_STATUS_SCRAPPED

	if _has_open_outsource(mold_name, OUTSOURCE_TYPE_EXTERNAL_MAINTENANCE):
		return MOLD_STATUS_UNDER_EXTERNAL_MAINTENANCE

	if _has_open_outsource(mold_name):
		return MOLD_STATUS_OUTSOURCED

	if asset and _has_pending_repair(asset.name):
		return MOLD_STATUS_UNDER_MAINTENANCE

	if asset and _has_open_maintenance(asset.name):
		return MOLD_STATUS_UNDER_MAINTENANCE

	if asset and asset.custodian:
		return MOLD_STATUS_ISSUED

	return MOLD_STATUS_ACTIVE


def _has_open_outsource(mold_name: str, outsource_type: str | None = None) -> bool:
	filters = {"mold": mold_name, "docstatus": 1, "outsource_status": "Open"}
	if outsource_type:
		filters["outsource_type"] = outsource_type
	return bool(frappe.db.exists("Mold Outsource", filters))


def _has_pending_repair(asset_name: str) -> bool:
	return bool(
		frappe.db.exists(
			"Asset Repair",
			{"asset": asset_name, "repair_status": "Pending", "docstatus": 1},
		)
	)


def _has_open_maintenance(asset_name: str) -> bool:
	return bool(
		frappe.db.sql(
			"""
			select aml.name
			from `tabAsset Maintenance Log` aml
			join `tabAsset Maintenance` am on am.name = aml.asset_maintenance
			where am.asset_name = %(asset)s
				and aml.docstatus = 1
				and aml.maintenance_status in ('Planned', 'Overdue')
			limit 1
			""",
			{"asset": asset_name},
		)
	)


def _get_current_warehouse(asset_name: str | None) -> str:
	if not asset_name or not _has_asset_movement_item_column("custom_mold_management_target_warehouse"):
		return ""

	value = frappe.db.sql(
		"""
		select ifnull(asm_item.custom_mold_management_target_warehouse, '')
		from `tabAsset Movement Item` asm_item
		join `tabAsset Movement` asm on asm.name = asm_item.parent
		where asm_item.asset = %(asset)s
			and asm.docstatus = 1
			and ifnull(asm_item.custom_mold_management_target_warehouse, '') != ''
		order by asm.transaction_date desc, asm.modified desc
		limit 1
		""",
		{"asset": asset_name},
	)
	return value[0][0] if value else ""


def _get_current_storage_bin(asset_name: str | None) -> str:
	if not asset_name or not _has_asset_movement_item_column("custom_mold_management_target_storage_bin"):
		return ""

	value = frappe.db.sql(
		"""
		select ifnull(asm_item.custom_mold_management_target_storage_bin, '')
		from `tabAsset Movement Item` asm_item
		join `tabAsset Movement` asm on asm.name = asm_item.parent
		where asm_item.asset = %(asset)s
			and asm.docstatus = 1
			and ifnull(asm_item.custom_mold_management_target_storage_bin, '') != ''
		order by asm.transaction_date desc, asm.modified desc
		limit 1
		""",
		{"asset": asset_name},
	)
	return value[0][0] if value else ""


def _get_current_transaction_fields(mold_name: str, asset_name: str | None) -> dict:
	open_outsource = _get_open_outsource_doc(mold_name)
	if open_outsource:
		return {
			"current_transaction_type": "Mold Outsource",
			"current_transaction_ref": open_outsource.name,
		}

	issue_context = _get_open_issue_context(asset_name) if asset_name else None
	if issue_context:
		return {
			"current_transaction_type": "Asset Movement",
			"current_transaction_ref": issue_context["name"],
		}

	open_repair = _get_open_repair_doc(asset_name) if asset_name else None
	if open_repair:
		return {
			"current_transaction_type": "Asset Repair",
			"current_transaction_ref": open_repair.name,
		}

	open_maintenance = _get_open_maintenance_doc(asset_name) if asset_name else None
	if open_maintenance:
		return {
			"current_transaction_type": "Asset Maintenance Log",
			"current_transaction_ref": open_maintenance.name,
		}

	events = _collect_lifecycle_events(mold_name, asset_name)
	if not events:
		return {"current_transaction_type": None, "current_transaction_ref": None}

	latest = events[0]
	return {
		"current_transaction_type": latest["doctype"],
		"current_transaction_ref": latest["name"],
	}


def _get_recent_activity_dates(mold_name: str, asset_name: str | None) -> dict:
	events = _collect_lifecycle_events(mold_name, asset_name)
	fields = {
		"last_transfer_on": None,
		"last_issue_on": None,
		"last_receipt_on": None,
		"last_repair_on": None,
		"last_maintenance_on": None,
		"last_outsource_on": None,
		"last_alteration_on": None,
	}

	for event in events:
		if event["doctype"] == "Asset Movement" and event["kind"] == "Transfer" and not fields["last_transfer_on"]:
			fields["last_transfer_on"] = event["time"]
		elif event["doctype"] == "Asset Movement" and event["kind"] == "Issue" and not fields["last_issue_on"]:
			fields["last_issue_on"] = event["time"]
		elif event["doctype"] == "Asset Movement" and event["kind"] == "Receipt" and not fields["last_receipt_on"]:
			fields["last_receipt_on"] = event["time"]
		elif event["doctype"] == "Asset Repair" and not fields["last_repair_on"]:
			fields["last_repair_on"] = event["time"]
		elif event["doctype"] == "Asset Maintenance Log" and not fields["last_maintenance_on"]:
			fields["last_maintenance_on"] = event["time"]
		elif event["doctype"] == "Mold Outsource" and not fields["last_outsource_on"]:
			fields["last_outsource_on"] = event["time"]
		elif event["doctype"] == "Mold Alteration" and not fields["last_alteration_on"]:
			fields["last_alteration_on"] = event["time"]

	return fields


def _collect_lifecycle_events(mold_name: str, asset_name: str | None) -> list[dict]:
	events: list[dict] = []

	if asset_name:
		for movement in frappe.get_all(
			"Asset Movement",
			fields=["name", "transaction_date", "purpose"],
			filters={"docstatus": 1},
			order_by="transaction_date desc, modified desc",
		):
			if frappe.db.exists("Asset Movement Item", {"parent": movement.name, "asset": asset_name}):
				events.append(
					{
						"doctype": "Asset Movement",
						"name": movement.name,
						"time": movement.transaction_date,
						"kind": movement.purpose,
					}
				)

		for repair in frappe.get_all(
			"Asset Repair",
			fields=["name", "modified", "repair_status"],
			filters={"asset": asset_name, "docstatus": 1},
			order_by="modified desc",
		):
			events.append(
				{
					"doctype": "Asset Repair",
					"name": repair.name,
					"time": repair.modified,
					"kind": repair.repair_status,
				}
			)

		for row in frappe.db.sql(
			"""
			select aml.name, coalesce(aml.completion_date, aml.due_date, aml.modified) as event_time, aml.maintenance_status
			from `tabAsset Maintenance Log` aml
			join `tabAsset Maintenance` am on am.name = aml.asset_maintenance
			where am.asset_name = %(asset)s and aml.docstatus = 1
			order by event_time desc
			""",
			{"asset": asset_name},
			as_dict=True,
		):
			events.append(
				{
					"doctype": "Asset Maintenance Log",
					"name": row.name,
					"time": row.event_time,
					"kind": row.maintenance_status,
				}
			)

	for alteration in frappe.get_all(
		"Mold Alteration",
		fields=["name", "alteration_date", "to_version"],
		filters={"mold": mold_name, "docstatus": 1},
		order_by="alteration_date desc, modified desc",
	):
		events.append(
			{
				"doctype": "Mold Alteration",
				"name": alteration.name,
				"time": alteration.alteration_date,
				"kind": alteration.to_version,
			}
		)

	for outsource in frappe.get_all(
		"Mold Outsource",
		fields=["name", "outsource_date", "actual_return_date", "outsource_type"],
		filters={"mold": mold_name, "docstatus": 1},
		order_by="modified desc",
	):
		events.append(
			{
				"doctype": "Mold Outsource",
				"name": outsource.name,
				"time": outsource.actual_return_date or outsource.outsource_date,
				"kind": outsource.outsource_type,
			}
		)

	events.sort(key=lambda row: (str(row.get("time") or ""), row["name"]), reverse=True)
	return events


def get_latest_submitted_version(mold_name: str) -> str:
	rows = frappe.get_all(
		"Mold Alteration",
		fields=["to_version"],
		filters={"mold": mold_name, "docstatus": 1},
	)
	if not rows:
		return "A0"
	return max((row.to_version for row in rows), key=version_sort_key)


def _get_current_version(mold) -> str:
	current_version = normalize_version(getattr(mold, "current_version", None))
	latest_version = normalize_version(get_latest_submitted_version(mold.name))
	return max((current_version, latest_version), key=version_sort_key)


def _get_open_outsource_doc(mold_name: str):
	name = frappe.db.get_value(
		"Mold Outsource",
		{"mold": mold_name, "docstatus": 1, "outsource_status": "Open"},
		"name",
		order_by="outsource_date desc, modified desc",
	)
	return frappe.get_doc("Mold Outsource", name) if name else None


def _get_open_issue_context(asset_name: str | None) -> dict | None:
	if not asset_name:
		return None

	rows = frappe.db.sql(
		"""
		select
			asm.name,
			ifnull(asm_item.to_employee, '') as to_employee,
			ifnull(asm_item.target_location, '') as target_location
		from `tabAsset Movement Item` asm_item
		join `tabAsset Movement` asm on asm.name = asm_item.parent
		where asm_item.asset = %(asset)s
			and asm.docstatus = 1
			and asm.purpose = 'Issue'
		order by asm.transaction_date desc, asm.modified desc
		limit 1
		""",
		{"asset": asset_name},
		as_dict=True,
	)
	return rows[0] if rows else None


def _get_open_repair_doc(asset_name: str | None):
	if not asset_name:
		return None

	name = frappe.db.get_value(
		"Asset Repair",
		{"asset": asset_name, "repair_status": "Pending", "docstatus": 1},
		"name",
		order_by="modified desc",
	)
	return frappe.get_doc("Asset Repair", name) if name else None


def _get_open_maintenance_doc(asset_name: str | None):
	if not asset_name:
		return None

	rows = frappe.db.sql(
		"""
		select aml.name
		from `tabAsset Maintenance Log` aml
		join `tabAsset Maintenance` am on am.name = aml.asset_maintenance
		where am.asset_name = %(asset)s
			and aml.docstatus = 1
			and aml.maintenance_status in ('Planned', 'Overdue')
		order by coalesce(aml.completion_date, aml.due_date, aml.modified) desc
		limit 1
		""",
		{"asset": asset_name},
		as_dict=True,
	)
	if not rows:
		return None
	return frappe.get_doc("Asset Maintenance Log", rows[0].name)


def _get_current_holder_summary(
	*,
	mold_name: str,
	asset,
	current_warehouse: str | None,
	current_location: str | None,
	current_storage_bin: str | None,
) -> str | None:
	if not asset:
		return _("Awaiting asset creation or linkage")

	open_outsource = _get_open_outsource_doc(mold_name)
	if open_outsource:
		return _format_outsource_summary(open_outsource)

	if asset.custodian:
		return _format_issue_summary(asset, _get_open_issue_context(asset.name))

	return _format_internal_location_summary(current_warehouse, current_location, current_storage_bin)


def _format_internal_location_summary(
	current_warehouse: str | None, current_location: str | None, current_storage_bin: str | None
) -> str | None:
	parts = [part for part in (current_warehouse, current_location, current_storage_bin) if part]
	return " / ".join(parts) if parts else None


def _format_issue_summary(asset, issue_context: dict | None) -> str:
	custodian = asset.custodian
	if not custodian:
		return _("Issued")

	employee_name = frappe.db.get_value("Employee", custodian, "employee_name") if custodian else None
	segments = [custodian]
	if employee_name and employee_name != custodian:
		segments.append(employee_name)
	if issue_context and issue_context.get("target_location"):
		segments.append(issue_context.get("target_location"))
	return _("Issued to {0}").format(" / ".join(segments))


def _format_outsource_summary(outsource_doc) -> str:
	segments = []
	if outsource_doc.destination_type == "Supplier" and outsource_doc.supplier:
		supplier_name = frappe.db.get_value("Supplier", outsource_doc.supplier, "supplier_name") or outsource_doc.supplier
		segments.append(supplier_name)
	elif outsource_doc.destination_type == "Customer" and outsource_doc.customer:
		customer_name = frappe.db.get_value("Customer", outsource_doc.customer, "customer_name") or outsource_doc.customer
		segments.append(customer_name)
	elif outsource_doc.destination_name:
		segments.append(outsource_doc.destination_name)

	if outsource_doc.destination_location:
		segments.append(outsource_doc.destination_location)

	if not segments:
		segments.append(outsource_doc.outsource_type or _("External Destination"))

	return _("Outsourced to {0}").format(" / ".join(segments))


def sanitize_lifecycle_values(values: dict) -> dict:
	cleaned = {}
	for key, value in values.items():
		if key in LIFECYCLE_DATETIME_FIELDS:
			cleaned[key] = value or None
			continue
		cleaned[key] = value
	return cleaned


@lru_cache(maxsize=8)
def _has_asset_movement_item_column(fieldname: str) -> bool:
	return frappe.db.has_column("Asset Movement Item", fieldname)

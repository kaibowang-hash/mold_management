from __future__ import annotations

import frappe
from frappe.utils import get_datetime, now_datetime

from mold_management.constants import MOLD_STORAGE_STATUS_AVAILABLE


def sync_mold_storage_location(mold_name: str, lifecycle_values: dict | None = None):
	if not frappe.db.exists("DocType", "Mold Storage Location") or not frappe.db.exists(
		"DocType", "Mold Storage Log"
	):
		return

	mold = frappe.get_doc("Mold", mold_name)
	values = _build_values_payload(mold, lifecycle_values or {})
	target_name = _ensure_target_storage_location(values)
	current_names = frappe.get_all(
		"Mold Storage Location",
		filters={"current_mold": mold.name, "docstatus": 1},
		pluck="name",
	)

	for location_name in current_names:
		if location_name != target_name:
			_release_storage_location(location_name, mold, values)

	if target_name:
		_occupy_storage_location(target_name, mold, values)


def _build_values_payload(mold, lifecycle_values: dict) -> dict:
	keys = (
		"status",
		"linked_asset",
		"current_warehouse",
		"current_location",
		"current_storage_bin",
		"current_transaction_type",
		"current_transaction_ref",
		"last_transfer_on",
		"last_issue_on",
		"last_receipt_on",
		"last_repair_on",
		"last_maintenance_on",
		"last_outsource_on",
		"last_alteration_on",
	)
	return {key: lifecycle_values[key] if key in lifecycle_values else mold.get(key) for key in keys}


def _find_target_storage_location(values: dict) -> str | None:
	warehouse = (values.get("current_warehouse") or "").strip()
	location = (values.get("current_location") or "").strip()
	storage_bin = (values.get("current_storage_bin") or "").strip()

	if not warehouse and not location and not storage_bin:
		return None

	row = frappe.db.sql(
		"""
		select name
		from `tabMold Storage Location`
		where ifnull(warehouse, '') = %(warehouse)s
			and ifnull(location, '') = %(location)s
			and ifnull(storage_bin, '') = %(storage_bin)s
			and docstatus = 1
		limit 1
		""",
		{
			"warehouse": warehouse,
			"location": location,
			"storage_bin": storage_bin,
		},
	)
	return row[0][0] if row else None


def _ensure_target_storage_location(values: dict) -> str | None:
	target_name = _find_target_storage_location(values)
	if target_name:
		return target_name

	warehouse = (values.get("current_warehouse") or "").strip()
	location = (values.get("current_location") or "").strip()
	storage_bin = (values.get("current_storage_bin") or "").strip()
	if not warehouse or not storage_bin:
		return None

	doc = frappe.get_doc(
		{
			"doctype": "Mold Storage Location",
			"storage_code": _build_storage_code(warehouse, location, storage_bin),
			"warehouse": warehouse,
			"location": location or None,
			"storage_bin": storage_bin,
			"notes": "Auto-created by Mold Management lifecycle sync.",
		}
	)
	doc.insert(ignore_permissions=True)
	doc.submit()
	return doc.name


def _occupy_storage_location(location_name: str, mold, values: dict):
	doc = frappe.get_doc("Mold Storage Location", location_name)
	new_values = {
		"current_mold": mold.name,
		"linked_asset": values.get("linked_asset"),
		"mold_status": values.get("status"),
		"storage_status": _get_storage_status(values.get("status"), mold.name),
		"last_activity_on": _get_posting_time(values),
	}
	changed = _has_field_changes(doc, new_values)
	reference_doctype = values.get("current_transaction_type")
	reference_name = values.get("current_transaction_ref")

	if changed:
		frappe.db.set_value("Mold Storage Location", location_name, new_values, update_modified=False)

	if changed or _should_log_reference(location_name, mold.name, reference_doctype, reference_name):
		_create_storage_log(
			location_name=location_name,
			mold_name=mold.name,
			linked_asset=values.get("linked_asset"),
			from_status=doc.storage_status,
			to_status=new_values["storage_status"],
			from_warehouse=doc.warehouse,
			to_warehouse=doc.warehouse,
			from_location=doc.location,
			to_location=doc.location,
			from_storage_bin=doc.storage_bin,
			to_storage_bin=doc.storage_bin,
			posting_time=new_values["last_activity_on"],
			reference_doctype=reference_doctype,
			reference_name=reference_name,
		)


def _release_storage_location(location_name: str, mold, values: dict):
	doc = frappe.get_doc("Mold Storage Location", location_name)
	new_values = {
		"current_mold": None,
		"linked_asset": None,
		"mold_status": None,
		"storage_status": MOLD_STORAGE_STATUS_AVAILABLE,
		"last_activity_on": _get_posting_time(values),
	}
	changed = _has_field_changes(doc, new_values)
	reference_doctype = values.get("current_transaction_type")
	reference_name = values.get("current_transaction_ref")

	if changed:
		frappe.db.set_value("Mold Storage Location", location_name, new_values, update_modified=False)

	if changed or _should_log_reference(location_name, mold.name, reference_doctype, reference_name):
		_create_storage_log(
			location_name=location_name,
			mold_name=mold.name,
			linked_asset=values.get("linked_asset") or doc.linked_asset,
			from_status=doc.storage_status,
			to_status=MOLD_STORAGE_STATUS_AVAILABLE,
			from_warehouse=doc.warehouse,
			to_warehouse=doc.warehouse,
			from_location=doc.location,
			to_location=doc.location,
			from_storage_bin=doc.storage_bin,
			to_storage_bin=doc.storage_bin,
			posting_time=new_values["last_activity_on"],
			reference_doctype=reference_doctype,
			reference_name=reference_name,
		)


def _has_field_changes(doc, new_values: dict) -> bool:
	return any(doc.get(fieldname) != value for fieldname, value in new_values.items())


def _should_log_reference(
	location_name: str, mold_name: str, reference_doctype: str | None, reference_name: str | None
) -> bool:
	if not reference_doctype or not reference_name:
		return False

	return not frappe.db.exists(
		"Mold Storage Log",
		{
			"mold_storage_location": location_name,
			"mold": mold_name,
			"reference_doctype": reference_doctype,
			"reference_name": reference_name,
		},
	)


def _create_storage_log(
	*,
	location_name: str,
	mold_name: str,
	linked_asset: str | None,
	from_status: str | None,
	to_status: str | None,
	from_warehouse: str | None,
	to_warehouse: str | None,
	from_location: str | None,
	to_location: str | None,
	from_storage_bin: str | None,
	to_storage_bin: str | None,
	posting_time,
	reference_doctype: str | None,
	reference_name: str | None,
):
	doc = frappe.get_doc(
		{
			"doctype": "Mold Storage Log",
			"mold_storage_location": location_name,
			"mold": mold_name,
			"linked_asset": linked_asset,
			"event_type": reference_doctype or "Lifecycle Sync",
			"from_status": from_status,
			"to_status": to_status,
			"from_warehouse": from_warehouse,
			"to_warehouse": to_warehouse,
			"from_location": from_location,
			"to_location": to_location,
			"from_storage_bin": from_storage_bin,
			"to_storage_bin": to_storage_bin,
			"posting_time": posting_time or now_datetime(),
			"reference_doctype": reference_doctype,
			"reference_name": reference_name,
		}
	)
	doc.insert(ignore_permissions=True)
	doc.submit()


def _get_storage_status(mold_status: str | None, mold_name: str | None) -> str:
	if not mold_name:
		return MOLD_STORAGE_STATUS_AVAILABLE
	return mold_status or MOLD_STORAGE_STATUS_AVAILABLE


def _get_posting_time(values: dict):
	timestamps = [
		values.get(key)
		for key in (
			"last_transfer_on",
			"last_issue_on",
			"last_receipt_on",
			"last_repair_on",
			"last_maintenance_on",
			"last_outsource_on",
			"last_alteration_on",
		)
		if values.get(key)
	]
	if timestamps:
		return max(timestamps, key=get_datetime)
	return now_datetime()


def _build_storage_code(warehouse: str, location: str, storage_bin: str) -> str:
	location_value = location or "NO-LOCATION"
	return f"{warehouse} :: {location_value} :: {storage_bin}"

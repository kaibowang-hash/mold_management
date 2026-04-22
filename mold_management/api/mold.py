from __future__ import annotations

import json

import frappe
from frappe import _
from frappe.utils import now_datetime, today
from frappe.utils.xlsxutils import build_xlsx_response

try:
	from mold_management.constants import ASSET_SETUP_MODE_CREATE, ASSET_SETUP_MODE_LINK
except ImportError:
	# Keep old workers from crashing if the Python module cache is temporarily stale
	# while the site is being updated.
	ASSET_SETUP_MODE_CREATE = "Create New Asset"
	ASSET_SETUP_MODE_LINK = "Link Existing Asset"
from mold_management.services.activity_log import get_item_mold_rows, get_mold_activity_rows
from mold_management.services.asset_setup import get_asset_setup_context, setup_asset_for_mold as run_asset_setup
from mold_management.services.dashboard import (
	get_storage_board_page_data as build_storage_board_page_data,
	get_storage_board_rows,
	get_workspace_dashboard_data as build_workspace_dashboard_data,
)
from mold_management.services.guardrails import (
	assert_action_allowed,
	create_receipt_to_default_for_mold,
	get_action_guardrail as build_action_guardrail,
	return_open_outsource_for_mold,
)
from mold_management.services.lifecycle import sync_mold_lifecycle
from mold_management.services.spare_parts import get_mold_spare_part_rows, make_spare_part_usage


@frappe.whitelist()
def create_asset_from_mold(mold_name: str) -> dict:
	result = run_asset_setup(mold_name, ASSET_SETUP_MODE_CREATE)
	sync_mold_lifecycle(mold_name)
	return result


@frappe.whitelist()
def link_existing_asset(mold_name: str, asset_name: str) -> dict:
	result = run_asset_setup(mold_name, ASSET_SETUP_MODE_LINK, asset_name)
	sync_mold_lifecycle(mold_name)
	return result


@frappe.whitelist()
def setup_asset_for_mold(mold_name: str, setup_mode: str, asset_name: str | None = None) -> dict:
	result = run_asset_setup(mold_name, setup_mode, asset_name)
	sync_mold_lifecycle(mold_name)
	return result


@frappe.whitelist()
def get_asset_setup_details(mold_name: str) -> dict:
	mold = frappe.get_doc("Mold", mold_name)
	return get_asset_setup_context(mold)


@frappe.whitelist()
def get_mold_by_barcode(barcode_value: str) -> dict:
	barcode_value = (barcode_value or "").strip()
	if not barcode_value:
		frappe.throw(_("Barcode value is required."))

	if not frappe.db.exists("Mold", barcode_value):
		frappe.throw(_("No Mold was found for barcode {0}.").format(frappe.bold(barcode_value)))

	doc = frappe.get_doc("Mold", barcode_value)
	return {
		"name": doc.name,
		"mold_name": doc.mold_name,
		"status": doc.status,
		"linked_asset": doc.linked_asset,
		"current_version": doc.current_version,
	}


@frappe.whitelist()
def create_asset_movement_from_mold(mold_name: str, purpose: str, values: str | dict | None = None) -> dict:
	assert_action_allowed(mold_name, purpose)
	mold = frappe.get_doc("Mold", mold_name)
	asset = _get_linked_asset(mold)
	values = _coerce_values(values)

	row = {
		"asset": asset.name,
		"source_location": values.get("source_location") or asset.location,
		"target_location": values.get("target_location"),
		"from_employee": values.get("from_employee"),
		"to_employee": values.get("to_employee"),
	}
	_apply_asset_movement_extension_fields(
		row,
		source_warehouse=values.get("source_warehouse") or mold.current_warehouse,
		source_storage_bin=values.get("source_storage_bin") or mold.current_storage_bin,
		target_warehouse=values.get("target_warehouse"),
		target_storage_bin=values.get("target_storage_bin"),
	)
	doc = frappe.get_doc(
		{
			"doctype": "Asset Movement",
			"company": mold.company,
			"purpose": purpose,
			"transaction_date": now_datetime(),
			"reference_doctype": "Mold",
			"reference_name": mold.name,
			"assets": [row],
		}
	)
	doc.insert(ignore_permissions=True)
	return {"doctype": doc.doctype, "name": doc.name}


@frappe.whitelist()
def create_asset_repair_from_mold(mold_name: str, values: str | dict | None = None) -> dict:
	assert_action_allowed(mold_name, "Repair")
	mold = frappe.get_doc("Mold", mold_name)
	asset = _get_linked_asset(mold)
	values = _coerce_values(values)

	doc = frappe.get_doc(
		{
			"doctype": "Asset Repair",
			"asset": asset.name,
			"company": mold.company,
			"failure_date": values.get("failure_date") or now_datetime(),
			"repair_status": values.get("repair_status") or "Pending",
			"description": values.get("description"),
			"actions_performed": values.get("actions_performed"),
		}
	)
	doc.insert(ignore_permissions=True)
	sync_mold_lifecycle(mold.name)
	return {"doctype": doc.doctype, "name": doc.name}


@frappe.whitelist()
def create_asset_maintenance_from_mold(mold_name: str, values: str | dict | None = None) -> dict:
	assert_action_allowed(mold_name, "Maintenance")
	mold = frappe.get_doc("Mold", mold_name)
	asset = _get_linked_asset(mold)
	values = _coerce_values(values)
	settings = frappe.get_single("Mold Management Settings")
	_require_value(
		settings.default_maintenance_team,
		_("Default Maintenance Team must be configured in Mold Management Settings."),
	)

	task_data = {
		"maintenance_task": values.get("maintenance_task") or _("General Mold Maintenance"),
		"maintenance_type": "Preventive Maintenance",
		"maintenance_status": "Planned",
		"start_date": values.get("start_date") or today(),
		"periodicity": values.get("periodicity") or "Monthly",
		"assign_to": values.get("assign_to") or frappe.session.user,
		"next_due_date": values.get("next_due_date") or today(),
		"description": values.get("description"),
	}

	maintenance_name = frappe.db.get_value(
		"Asset Maintenance",
		{"asset_name": asset.name},
		order_by="modified desc",
	)
	if maintenance_name:
		maintenance_doc = frappe.get_doc("Asset Maintenance", maintenance_name)
		maintenance_doc.append("asset_maintenance_tasks", task_data)
	else:
		maintenance_doc = frappe.get_doc(
			{
				"doctype": "Asset Maintenance",
				"asset_name": asset.name,
				"company": mold.company,
				"maintenance_team": settings.default_maintenance_team,
				"asset_maintenance_tasks": [task_data],
			}
		)

	maintenance_doc.save(ignore_permissions=True)
	task_name = maintenance_doc.asset_maintenance_tasks[-1].name
	log_name = frappe.db.get_value(
		"Asset Maintenance Log",
		{"asset_maintenance": maintenance_doc.name, "task": task_name},
		"name",
		order_by="modified desc",
	)
	sync_mold_lifecycle(mold.name)
	return {"doctype": "Asset Maintenance Log", "name": log_name}


@frappe.whitelist()
def create_outsource_from_mold(mold_name: str, values: str | dict | None = None) -> dict:
	assert_action_allowed(mold_name, "Outsource")
	mold = frappe.get_doc("Mold", mold_name)
	values = _coerce_values(values)

	doc = frappe.get_doc(
		{
			"doctype": "Mold Outsource",
			"mold": mold.name,
			"outsource_type": values.get("outsource_type"),
			"outsource_date": values.get("outsource_date") or today(),
			"expected_return_date": values.get("expected_return_date"),
			"destination_type": values.get("destination_type"),
			"supplier": values.get("supplier"),
			"customer": values.get("customer"),
			"destination_name": values.get("destination_name"),
			"destination_location": values.get("destination_location"),
			"notes": values.get("notes"),
		}
	)
	doc.insert(ignore_permissions=True)
	return {"doctype": doc.doctype, "name": doc.name}


@frappe.whitelist()
def create_alteration_from_mold(mold_name: str, alteration_type: str) -> dict:
	assert_action_allowed(mold_name, f"{alteration_type} Alteration")
	mold = frappe.get_doc("Mold", mold_name)
	if not mold.linked_asset:
		frappe.throw(_("Create or link an Asset first."))

	return {
		"doctype": "Mold Alteration",
		"defaults": {
			"mold": mold_name,
			"alteration_type": alteration_type,
			"alteration_date": today(),
		},
	}


@frappe.whitelist()
def scrap_linked_asset(mold_name: str) -> dict:
	from erpnext.assets.doctype.asset.depreciation import scrap_asset

	assert_action_allowed(mold_name, "Scrap")
	mold = frappe.get_doc("Mold", mold_name)
	asset = _get_linked_asset(mold)
	scrap_asset(asset.name)
	sync_mold_lifecycle(mold.name)
	return {"doctype": "Asset", "name": asset.name}


@frappe.whitelist()
def get_item_molds(item_code: str) -> list[dict]:
	rows = get_item_mold_rows(item_code)
	for row in rows:
		mold = frappe.get_cached_doc("Mold", row["mold"])
		row.update(
			{
				"mold_name": mold.mold_name,
				"status": mold.status,
				"current_version": mold.current_version,
				"current_warehouse": mold.current_warehouse,
				"current_location": mold.current_location,
				"current_holder_summary": mold.current_holder_summary,
			}
		)
	return rows


@frappe.whitelist()
def get_action_guardrail(mold_name: str, action_name: str) -> dict:
	return build_action_guardrail(mold_name, action_name)


@frappe.whitelist()
def create_receipt_to_default_from_mold(mold_name: str) -> dict:
	result = create_receipt_to_default_for_mold(mold_name)
	sync_mold_lifecycle(mold_name)
	return result


@frappe.whitelist()
def return_open_outsource_from_mold(mold_name: str, actual_return_date: str | None = None, return_result: str = "Active") -> dict:
	result = return_open_outsource_for_mold(mold_name, actual_return_date, return_result)
	sync_mold_lifecycle(mold_name)
	return result


@frappe.whitelist()
def get_workspace_dashboard_data() -> dict:
	return build_workspace_dashboard_data()


@frappe.whitelist()
def get_storage_board_data(
	current_mold: str | None = None,
	limit: int | None = None,
	warehouse: str | None = None,
	location: str | None = None,
	storage_status: str | None = None,
) -> list[dict]:
	return get_storage_board_rows(
		current_mold=current_mold,
		limit=limit,
		warehouse=warehouse,
		location=location,
		storage_status=storage_status,
	)


@frappe.whitelist()
def get_storage_board_page_data(
	warehouse: str | None = None,
	location: str | None = None,
	storage_status: str | None = None,
	current_mold: str | None = None,
) -> dict:
	return build_storage_board_page_data(
		warehouse=warehouse,
		location=location,
		storage_status=storage_status,
		current_mold=current_mold,
	)


@frappe.whitelist()
def export_item_molds(item_code: str):
	rows = get_item_molds(item_code)
	data = [
		["Mold", "Mold Name", "Status", "Version", "Warehouse", "Location", "Current Holder / Destination", "Priority", "Output Qty"],
	]
	for row in rows:
		data.append(
			[
				row["mold"],
				row["mold_name"],
				row["status"],
				row["current_version"],
				row["current_warehouse"],
				row["current_location"],
				row.get("current_holder_summary"),
				row["priority"],
				row["output_qty"],
			]
		)
	build_xlsx_response(data, f"{item_code}_molds")


@frappe.whitelist()
def get_mold_activity_log(mold_name: str) -> list[dict]:
	return get_mold_activity_rows(mold_name)


@frappe.whitelist()
def export_mold_activity_log(mold_name: str):
	rows = get_mold_activity_rows(mold_name)
	data = [["Type", "Document", "Time", "Activity", "Detail", "Docstatus"]]
	for row in rows:
		data.append(
			[
				row.get("reference_doctype"),
				row.get("name"),
				row.get("posting_time"),
				row.get("activity_type"),
				row.get("detail"),
				row.get("docstatus"),
			]
		)
	build_xlsx_response(data, f"{mold_name}_activity_log")


@frappe.whitelist()
def get_mold_spare_parts(mold_name: str) -> list[dict]:
	return get_mold_spare_part_rows(mold_name)


@frappe.whitelist()
def export_mold_spare_parts(mold_name: str):
	rows = get_mold_spare_part_rows(mold_name)
	data = [["Spare Part", "Part Code", "Part Name", "Specification", "UOM", "Supplier", "Alternative Part", "Preferred", "Notes"]]
	for row in rows:
		data.append(
			[
				row.get("name"),
				row.get("part_code"),
				row.get("part_name"),
				row.get("specification"),
				row.get("uom"),
				row.get("supplier"),
				row.get("alternative_part"),
				row.get("is_preferred"),
				row.get("fitment_notes"),
			]
		)
	build_xlsx_response(data, f"{mold_name}_spare_parts")


@frappe.whitelist()
def create_spare_part_usage_from_mold(mold_name: str, values: str | dict | None = None) -> dict:
	docname = make_spare_part_usage(mold_name, _coerce_values(values))
	return {"doctype": "Mold Spare Part Usage", "name": docname}


@frappe.whitelist()
def get_print_context(doctype: str, docname: str) -> dict:
	doc = frappe.get_doc(doctype, docname)
	settings = frappe.get_single("Mold Management Settings")
	operation = ""
	print_format = ""

	if doctype == "Asset Movement" and _is_mold_related_asset_movement(doc):
		operation = (doc.purpose or "").lower()
		print_format = {
			"transfer": settings.transfer_print_format,
			"issue": settings.issue_print_format,
			"receipt": settings.receipt_print_format,
		}.get(operation)
	elif doctype == "Asset Repair" and _is_mold_related_asset(doc.asset):
		operation = "repair"
		print_format = settings.repair_print_format
	elif doctype == "Asset Maintenance Log" and _is_mold_related_maintenance_log(doc):
		operation = "maintenance"
		print_format = settings.maintenance_print_format
	elif doctype == "Mold Outsource":
		operation = "outsource"
		print_format = settings.outsource_print_format
	elif doctype == "Mold Alteration":
		operation = "alteration"
		print_format = settings.alteration_print_format
	elif doctype == "Asset" and _is_mold_related_asset(doc.name) and doc.journal_entry_for_scrap:
		operation = "scrap"
		print_format = settings.scrap_print_format

	return {
		"should_print": bool(operation),
		"operation": operation,
		"print_format": print_format or frappe.get_meta(doctype).default_print_format or "Standard",
	}


def _coerce_values(values: str | dict | None) -> dict:
	if not values:
		return {}
	if isinstance(values, dict):
		return values
	return json.loads(values)


def _get_linked_asset(mold) -> "Document":
	asset_name = mold.linked_asset or frappe.db.get_value("Asset", {"custom_mold_management_mold": mold.name}, "name")
	if not asset_name:
		frappe.throw(_("Create or link an Asset first."))
	return frappe.get_doc("Asset", asset_name)


def _is_mold_related_asset(asset_name: str) -> bool:
	return bool(frappe.db.get_value("Asset", asset_name, "custom_mold_management_mold"))


def _is_mold_related_asset_movement(doc) -> bool:
	if doc.reference_doctype == "Mold" and doc.reference_name:
		return True
	return any(_is_mold_related_asset(row.asset) for row in doc.get("assets", []))


def _apply_asset_movement_extension_fields(
	row: dict,
	*,
	source_warehouse: str | None = None,
	source_storage_bin: str | None = None,
	target_warehouse: str | None = None,
	target_storage_bin: str | None = None,
):
	if frappe.db.has_column("Asset Movement Item", "custom_mold_management_source_warehouse"):
		row["custom_mold_management_source_warehouse"] = source_warehouse
	if frappe.db.has_column("Asset Movement Item", "custom_mold_management_source_storage_bin"):
		row["custom_mold_management_source_storage_bin"] = source_storage_bin
	if frappe.db.has_column("Asset Movement Item", "custom_mold_management_target_warehouse"):
		row["custom_mold_management_target_warehouse"] = target_warehouse
	if frappe.db.has_column("Asset Movement Item", "custom_mold_management_target_storage_bin"):
		row["custom_mold_management_target_storage_bin"] = target_storage_bin


def _is_mold_related_maintenance_log(doc) -> bool:
	asset_name = frappe.db.get_value("Asset Maintenance", doc.asset_maintenance, "asset_name")
	return _is_mold_related_asset(asset_name) if asset_name else False


def _require_value(value, message: str):
	if not value:
		frappe.throw(message)

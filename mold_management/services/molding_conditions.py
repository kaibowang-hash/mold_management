from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import now_datetime

from mold_management.services.versioning import get_next_version, normalize_version, version_sort_key
from mold_management.constants import ALTERATION_MINOR


CONDITION_STATUS_DRAFT = "Draft"
CONDITION_STATUS_APPROVED = "Approved"
CONDITION_STATUS_OBSOLETE = "Obsolete"
CONDITION_STATUS_CANCELLED = "Cancelled"


def set_condition_defaults(doc):
	if not doc.status:
		doc.status = CONDITION_STATUS_DRAFT
	if not doc.version:
		doc.version = get_next_condition_version(doc.item_code, doc.mold)
	else:
		doc.version = normalize_version(doc.version)
	doc.updated_to_version = doc.version
	if doc.update_source and not doc.updated_from_version:
		doc.updated_from_version = frappe.db.get_value(
			"Injection Molding Condition Sheet", doc.update_source, "version"
		)
	if not doc.output_group:
		doc.output_group = "Default"


def sync_condition_header(doc):
	if doc.item_code:
		doc.item_name = frappe.db.get_value("Item", doc.item_code, "item_name")
	if doc.item_code and doc.mold:
		product_row = frappe.db.get_value(
			"Mold Product",
			{"parent": doc.mold, "parenttype": "Mold", "item_code": doc.item_code},
			["output_group", "configuration_label", "color_spec", "output_qty", "cavity_output_qty"],
			as_dict=True,
		)
		if product_row:
			for fieldname in ("output_group", "configuration_label", "color_spec"):
				if not doc.get(fieldname) and product_row.get(fieldname):
					doc.set(fieldname, product_row.get(fieldname))
			for fieldname in ("output_qty", "cavity_output_qty"):
				if not doc.get(fieldname) and product_row.get(fieldname):
					doc.set(fieldname, product_row.get(fieldname))
	if doc.mold:
		mold = frappe.db.get_value(
			"Mold",
			doc.mold,
			["mold_name", "company", "machine_tonnage", "cavity_count"],
			as_dict=True,
		)
		if mold:
			doc.mold_name = mold.mold_name
			doc.company = mold.company
			if not doc.machine_tonnage:
				doc.machine_tonnage = mold.machine_tonnage
			if not doc.cavity_count:
				doc.cavity_count = mold.cavity_count
	if doc.material_item:
		doc.material_name = frappe.db.get_value("Item", doc.material_item, "item_name")


def validate_condition_sheet(doc):
	if not doc.item_code or not doc.mold:
		return
	if not frappe.db.exists(
		"Mold Product",
		{"parent": doc.mold, "parenttype": "Mold", "item_code": doc.item_code},
	):
		frappe.throw(_("Item {0} is not configured as a Mold Product for mold {1}.").format(doc.item_code, doc.mold))
	if doc.docstatus == 1 or doc.status == CONDITION_STATUS_APPROVED or doc.current_effective:
		validate_single_effective_condition(doc)


def validate_single_effective_condition(doc):
	excluded_names = [doc.name]
	if doc.get("update_source"):
		excluded_names.append(doc.update_source)
	if frappe.db.exists(
		"Injection Molding Condition Sheet",
		{
			"name": ("not in", excluded_names),
			"docstatus": 1,
			"item_code": doc.item_code,
			"mold": doc.mold,
			"current_effective": 1,
			"status": CONDITION_STATUS_APPROVED,
		},
	):
		frappe.throw(
			_("Item {0} and mold {1} already have a current effective Injection Molding Condition Sheet.").format(
				doc.item_code,
				doc.mold,
			)
		)


def activate_condition_sheet(doc):
	frappe.db.set_value(
		"Injection Molding Condition Sheet",
		doc.name,
		{
			"status": CONDITION_STATUS_APPROVED,
			"current_effective": 1,
			"effective_from": doc.effective_from or now_datetime(),
			"effective_by": doc.effective_by or frappe.session.user,
		},
		update_modified=False,
	)
	old_sheets = frappe.get_all(
		"Injection Molding Condition Sheet",
		filters={
			"name": ("!=", doc.name),
			"docstatus": 1,
			"item_code": doc.item_code,
			"mold": doc.mold,
			"current_effective": 1,
		},
		pluck="name",
	)
	if doc.get("update_source") and doc.update_source not in old_sheets:
		old_sheets.append(doc.update_source)
	for sheet_name in set(filter(None, old_sheets)):
		frappe.db.set_value(
			"Injection Molding Condition Sheet",
			sheet_name,
			{"status": CONDITION_STATUS_OBSOLETE, "current_effective": 0},
			update_modified=True,
		)
	sync_mold_condition_links(doc.mold)


def cancel_condition_sheet(doc):
	frappe.db.set_value(
		"Injection Molding Condition Sheet",
		doc.name,
		{"status": CONDITION_STATUS_CANCELLED, "current_effective": 0},
		update_modified=False,
	)
	sync_mold_condition_links(doc.mold)


def create_next_condition_version(sheet_name: str, update_reason: str) -> str:
	if not update_reason:
		frappe.throw(_("Update Reason is required."))
	source = frappe.get_doc("Injection Molding Condition Sheet", sheet_name)
	new_version = get_next_version(source.version or "A0", ALTERATION_MINOR)
	new_doc = frappe.copy_doc(source)
	new_doc.name = None
	new_doc.status = CONDITION_STATUS_DRAFT
	new_doc.current_effective = 0
	new_doc.effective_from = None
	new_doc.effective_by = None
	new_doc.version = new_version
	new_doc.update_source = source.name
	new_doc.update_reason = update_reason
	new_doc.updated_from_version = source.version
	new_doc.updated_to_version = new_version
	new_doc.amended_from = None
	new_doc.set("version_logs", [])
	for source_log in source.get("version_logs", []):
		row = new_doc.append("version_logs", {})
		for fieldname in (
			"update_date",
			"from_version",
			"to_version",
			"update_reason",
			"updated_by",
			"source_sheet",
			"new_sheet",
		):
			row.set(fieldname, source_log.get(fieldname))
	log = new_doc.append("version_logs", {})
	log.update(
		{
			"update_date": now_datetime(),
			"from_version": source.version,
			"to_version": new_version,
			"update_reason": update_reason,
			"updated_by": frappe.session.user,
			"source_sheet": source.name,
		}
	)
	new_doc.insert(ignore_permissions=True)
	log.db_set("new_sheet", new_doc.name, update_modified=False)
	return new_doc.name


def get_next_condition_version(item_code: str | None, mold: str | None) -> str:
	if not item_code or not mold:
		return "A0"
	rows = frappe.get_all(
		"Injection Molding Condition Sheet",
		filters={"item_code": item_code, "mold": mold, "docstatus": ("<", 2)},
		pluck="version",
	)
	if not rows:
		return "A0"
	return get_next_version(max((normalize_version(row) for row in rows), key=version_sort_key), ALTERATION_MINOR)


def sync_mold_condition_links(mold: str | None):
	if not mold or not frappe.db.exists("DocType", "Mold") or not frappe.db.exists("DocType", "Mold Condition Reference"):
		return
	if not frappe.get_meta("Mold").has_field("molding_condition_links"):
		return

	rows = get_molding_conditions_for_mold(mold)
	doc = frappe.get_doc("Mold", mold)
	doc.set("molding_condition_links", [])
	for row in rows:
		child = doc.append("molding_condition_links", {})
		child.condition_sheet = row["name"]
		child.item_code = row["item_code"]
		child.version = row["version"]
		child.status = row["status"]
		child.current_effective = row["current_effective"]
		child.cycle_time_seconds = row["cycle_time_seconds"]
		child.configuration_label = row["configuration_label"]
	doc.flags.ignore_validate_update_after_submit = True
	doc.save(ignore_permissions=True)


def get_active_molding_conditions_for_item(item_code: str) -> list[dict]:
	return frappe.get_all(
		"Injection Molding Condition Sheet",
		filters={
			"item_code": item_code,
			"docstatus": 1,
			"current_effective": 1,
			"status": CONDITION_STATUS_APPROVED,
		},
		fields=[
			"name",
			"mold",
			"mold_name",
			"item_code",
			"version",
			"configuration_label",
			"color_spec",
			"cycle_time_seconds",
			"output_group",
			"effective_from",
		],
		order_by="mold asc, modified desc",
	)


def get_molding_conditions_for_mold(mold: str) -> list[dict]:
	return frappe.get_all(
		"Injection Molding Condition Sheet",
		filters={"mold": mold, "docstatus": ("<", 2)},
		fields=[
			"name",
			"item_code",
			"item_name",
			"version",
			"status",
			"current_effective",
			"configuration_label",
			"color_spec",
			"cycle_time_seconds",
			"output_group",
			"effective_from",
		],
		order_by="current_effective desc, item_code asc, modified desc",
	)


def create_condition_sheet_from_trial_report(trial_report: str) -> dict:
	trial = frappe.get_doc("Mold Trial Report", trial_report)
	doc = frappe.get_doc(
		{
			"doctype": "Injection Molding Condition Sheet",
			"item_code": trial.item_code,
			"mold": trial.mold,
			"company": trial.company,
			"tpr_reference": trial.tpr_reference,
			"trial_report": trial.name,
			"workstation": trial.workstation,
			"machine": trial.machine,
			"cycle_time_seconds": trial.cycle_time_seconds,
			"material_item": trial.material_item,
			"material_lot": trial.material_lot,
			"color_spec": trial.color_spec,
			"quality_window": trial.trial_summary,
			"critical_notes": trial.parameter_snapshot,
			"attachment": trial.attachment,
		}
	)
	doc.insert(ignore_permissions=True)
	trial.db_set("condition_sheet", doc.name, update_modified=False)
	return {"doctype": doc.doctype, "name": doc.name}

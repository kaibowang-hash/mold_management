from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import now_datetime, today

from mold_management.constants import (
	MOLD_STATUS_ACTIVE,
	MOLD_STATUS_ISSUED,
	MOLD_STATUS_OUTSOURCED,
	MOLD_STATUS_PENDING_ASSET_LINK,
	MOLD_STATUS_SCRAPPED,
	MOLD_STATUS_UNDER_EXTERNAL_MAINTENANCE,
	MOLD_STATUS_UNDER_MAINTENANCE,
)

RESOLUTION_CREATE_RECEIPT = "create_receipt_to_default"
RESOLUTION_RETURN_OUTSOURCE = "return_open_outsource"

ACTION_LABELS = {
	"Transfer": "transfer",
	"Issue": "issue",
	"Receipt": "receipt",
	"Repair": "start repair",
	"Maintenance": "start maintenance",
	"Outsource": "outsource",
	"Minor Alteration": "create a minor alteration",
	"Major Alteration": "create a major alteration",
	"Scrap": "scrap",
	"Return Outsource": "return outsource",
}


def get_action_guardrail(mold_name: str, action_name: str) -> dict:
	mold = frappe.get_doc("Mold", mold_name)
	asset = frappe.get_doc("Asset", mold.linked_asset) if mold.linked_asset else None
	open_outsource = _get_open_outsource_doc(mold.name)
	open_issue = _get_open_issue_context(asset.name) if asset else None
	open_internal_work = _get_open_internal_work(asset.name) if asset else None
	action_label = ACTION_LABELS.get(action_name, action_name.lower())

	if action_name == "Create / Link Asset":
		return _allowed()

	if not mold.linked_asset:
		return _blocked(
			code="asset_required",
			title=_("Asset setup is still pending"),
			message=_(
				"Create or link the mold Asset first. Lifecycle actions stay locked until the asset has been established."
			),
		)

	if mold.status == MOLD_STATUS_SCRAPPED:
		return _blocked(
			code="already_scrapped",
			title=_("Mold is already scrapped"),
			message=_("Scrapped molds cannot start new lifecycle actions."),
		)

	if action_name == "Receipt":
		if _is_issued(mold, asset):
			return _allowed(reference_doctype="Asset Movement", reference_name=open_issue.get("name") if open_issue else None)
		return _blocked(
			code="receipt_not_needed",
			title=_("No issue return is pending"),
			message=_("This mold is not currently issued out, so no receipt back to the standard location is needed."),
		)

	if action_name == "Return Outsource":
		if open_outsource:
			return _allowed(reference_doctype="Mold Outsource", reference_name=open_outsource.name)
		return _blocked(
			code="outsource_return_not_needed",
			title=_("No outsource return is pending"),
			message=_("This mold does not have an open outsource document to return."),
		)

	if open_outsource:
		return _blocked(
			code="return_outsource_first",
			title=_("Mold is currently outsourced"),
			message=_(
				"Mold {0} is currently outside at {1}. Return it first before you {2}."
			).format(
				mold.name,
				mold.current_holder_summary or open_outsource.name,
				action_label,
			),
			reference_doctype="Mold Outsource",
			reference_name=open_outsource.name,
			resolution_action=RESOLUTION_RETURN_OUTSOURCE,
			resolution_label=_("Return Outsource First"),
		)

	if _is_issued(mold, asset) and action_name in {
		"Transfer",
		"Issue",
		"Repair",
		"Maintenance",
		"Outsource",
		"Minor Alteration",
		"Major Alteration",
		"Scrap",
	}:
		return _blocked(
			code="return_issue_first",
			title=_("Mold is currently issued"),
			message=_(
				"Mold {0} is currently issued to {1}. Return it to the default warehouse first before you {2}."
			).format(
				mold.name,
				_get_issue_target_text(mold, asset, open_issue),
				action_label,
			),
			reference_doctype="Asset Movement",
			reference_name=open_issue.get("name") if open_issue else None,
			resolution_action=RESOLUTION_CREATE_RECEIPT,
			resolution_label=_("Create Return Receipt"),
		)

	if open_internal_work and action_name in {"Transfer", "Issue", "Outsource", "Scrap"}:
		return _blocked(
			code="finish_internal_work_first",
			title=_("Mold is already in internal maintenance flow"),
			message=_(
				"Mold {0} already has an active internal repair or maintenance document {1}. Complete or cancel that document first before you {2}."
			).format(
				mold.name,
				open_internal_work["name"],
				action_label,
			),
			reference_doctype=open_internal_work["doctype"],
			reference_name=open_internal_work["name"],
		)

	if mold.status == MOLD_STATUS_PENDING_ASSET_LINK:
		return _blocked(
			code="pending_asset_link",
			title=_("Mold is still pending asset linkage"),
			message=_("This mold cannot enter lifecycle transactions until its asset is created or linked."),
		)

	if action_name == "Issue" and mold.status not in {MOLD_STATUS_ACTIVE}:
		return _blocked(
			code="issue_not_allowed",
			title=_("Issue is not allowed in the current status"),
			message=_("Only active molds can be issued out."),
		)

	if action_name == "Transfer" and mold.status not in {MOLD_STATUS_ACTIVE}:
		return _blocked(
			code="transfer_not_allowed",
			title=_("Transfer is not allowed in the current status"),
			message=_("Only active molds can be transferred internally."),
		)

	if action_name == "Outsource" and mold.status not in {MOLD_STATUS_ACTIVE}:
		return _blocked(
			code="outsource_not_allowed",
			title=_("Outsource is not allowed in the current status"),
			message=_("Only active molds can be outsourced."),
		)

	if action_name in {"Repair", "Maintenance"} and mold.status in {
		MOLD_STATUS_UNDER_MAINTENANCE,
		MOLD_STATUS_UNDER_EXTERNAL_MAINTENANCE,
	}:
		return _blocked(
			code="already_under_maintenance",
			title=_("Mold is already under maintenance"),
			message=_("Finish the current maintenance flow before starting another repair or maintenance document."),
			reference_doctype=open_internal_work["doctype"] if open_internal_work else None,
			reference_name=open_internal_work["name"] if open_internal_work else None,
		)

	return _allowed()


def assert_action_allowed(mold_name: str, action_name: str):
	result = get_action_guardrail(mold_name, action_name)
	if result.get("allowed"):
		return
	frappe.throw(result.get("message") or _("This action is blocked by mold lifecycle guardrails."))


def create_receipt_to_default_for_mold(mold_name: str) -> dict:
	mold = frappe.get_doc("Mold", mold_name)
	asset = _get_linked_asset(mold)
	assert_action_allowed(mold_name, "Receipt")

	doc = frappe.get_doc(
		{
			"doctype": "Asset Movement",
			"company": mold.company,
			"purpose": "Receipt",
			"transaction_date": now_datetime(),
			"reference_doctype": "Mold",
			"reference_name": mold.name,
			"assets": [
				{
					"asset": asset.name,
					"source_location": asset.location or mold.current_location,
					"target_location": mold.default_location or mold.current_location,
					"from_employee": asset.custodian,
					"custom_mold_management_source_warehouse": mold.current_warehouse or mold.default_warehouse,
					"custom_mold_management_source_storage_bin": mold.current_storage_bin or mold.default_storage_bin,
					"custom_mold_management_target_warehouse": mold.default_warehouse or mold.current_warehouse,
					"custom_mold_management_target_storage_bin": mold.default_storage_bin or mold.current_storage_bin,
				}
			],
		}
	)
	doc.insert(ignore_permissions=True)
	doc.submit()
	return {"doctype": doc.doctype, "name": doc.name}


def return_open_outsource_for_mold(mold_name: str, actual_return_date: str | None, return_result: str) -> dict:
	from mold_management.mold_management.doctype.mold_outsource.mold_outsource import mark_returned

	assert_action_allowed(mold_name, "Return Outsource")
	outsource_doc = _get_open_outsource_doc(mold_name)
	if not outsource_doc:
		frappe.throw(_("No open outsource document was found for mold {0}.").format(mold_name))

	mark_returned(outsource_doc.name, actual_return_date or today(), return_result)
	return {"doctype": outsource_doc.doctype, "name": outsource_doc.name}


def _allowed(reference_doctype: str | None = None, reference_name: str | None = None) -> dict:
	return {
		"allowed": True,
		"reference_doctype": reference_doctype,
		"reference_name": reference_name,
	}


def _blocked(
	*,
	code: str,
	title: str,
	message: str,
	reference_doctype: str | None = None,
	reference_name: str | None = None,
	resolution_action: str | None = None,
	resolution_label: str | None = None,
) -> dict:
	return {
		"allowed": False,
		"code": code,
		"title": title,
		"message": message,
		"reference_doctype": reference_doctype,
		"reference_name": reference_name,
		"resolution_action": resolution_action,
		"resolution_label": resolution_label,
	}


def _get_linked_asset(mold):
	if not mold.linked_asset:
		frappe.throw(_("Create or link an Asset first."))
	return frappe.get_doc("Asset", mold.linked_asset)


def _is_issued(mold, asset) -> bool:
	return bool(asset and asset.custodian) or mold.status == MOLD_STATUS_ISSUED


def _get_issue_target_text(mold, asset, open_issue: dict | None) -> str:
	if mold.current_holder_summary:
		prefix = "Issued to "
		if mold.current_holder_summary.startswith(prefix):
			return mold.current_holder_summary[len(prefix) :]
		return mold.current_holder_summary
	if asset and asset.custodian:
		employee_name = frappe.db.get_value("Employee", asset.custodian, "employee_name")
		return " / ".join([part for part in (asset.custodian, employee_name) if part])
	if open_issue and open_issue.get("to_employee"):
		return open_issue["to_employee"]
	return _("the current holder")


def _get_open_outsource_doc(mold_name: str):
	name = frappe.db.get_value(
		"Mold Outsource",
		{"mold": mold_name, "docstatus": 1, "outsource_status": "Open"},
		"name",
		order_by="outsource_date desc, modified desc",
	)
	return frappe.get_doc("Mold Outsource", name) if name else None


def _get_open_issue_context(asset_name: str) -> dict | None:
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


def _get_open_internal_work(asset_name: str):
	repair = frappe.db.get_value(
		"Asset Repair",
		{"asset": asset_name, "repair_status": "Pending", "docstatus": 1},
		"name",
		order_by="modified desc",
	)
	if repair:
		return {"doctype": "Asset Repair", "name": repair}

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
	if rows:
		return {"doctype": "Asset Maintenance Log", "name": rows[0].name}

	return None

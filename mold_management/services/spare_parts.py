from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import now_datetime


def get_mold_spare_part_rows(mold_name: str) -> list[dict]:
	return frappe.db.sql(
		"""
		select
			sp.name,
			sp.part_code,
			sp.part_name,
			sp.specification,
			sp.uom,
			sp.supplier,
			sp.alternative_part,
			sp.is_active,
			link.fitment_notes,
			link.is_preferred
		from `tabMold Spare Part Mold` link
		join `tabMold Spare Part` sp on sp.name = link.parent
		where link.mold = %(mold)s
		order by sp.part_code asc, sp.modified desc
		""",
		{"mold": mold_name},
		as_dict=True,
	)


def validate_spare_part_applicability(spare_part_name: str, mold_name: str):
	if not frappe.db.exists("Mold Spare Part Mold", {"parent": spare_part_name, "mold": mold_name}):
		frappe.throw(_("Spare Part {0} is not mapped to Mold {1}.").format(spare_part_name, mold_name))


def make_spare_part_usage(mold_name: str, values: dict | None = None) -> str:
	values = values or {}
	spare_part = values.get("spare_part")
	if not spare_part:
		frappe.throw(_("Spare Part is required."))

	validate_spare_part_applicability(spare_part, mold_name)
	part_doc = frappe.get_doc("Mold Spare Part", spare_part)
	doc = frappe.get_doc(
		{
			"doctype": "Mold Spare Part Usage",
			"mold": mold_name,
			"spare_part": spare_part,
			"part_code": part_doc.part_code,
			"part_name": part_doc.part_name,
			"usage_date": values.get("usage_date") or now_datetime(),
			"qty": values.get("qty") or 1,
			"uom": values.get("uom") or part_doc.uom,
			"used_by": values.get("used_by") or frappe.session.user,
			"reference_doctype": values.get("reference_doctype"),
			"reference_name": values.get("reference_name"),
			"remarks": values.get("remarks"),
		}
	)
	doc.insert(ignore_permissions=True)
	doc.submit()
	return doc.name

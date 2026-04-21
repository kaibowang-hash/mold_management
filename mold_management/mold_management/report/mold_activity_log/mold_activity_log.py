import frappe

from mold_management.services.activity_log import get_mold_activity_rows


def execute(filters=None):
	filters = filters or {}
	columns = [
		{"label": "Mold", "fieldname": "mold", "fieldtype": "Link", "options": "Mold", "width": 140},
		{"label": "Type", "fieldname": "reference_doctype", "fieldtype": "Data", "width": 160},
		{"label": "Document", "fieldname": "name", "fieldtype": "Dynamic Link", "options": "reference_doctype", "width": 180},
		{"label": "Time", "fieldname": "posting_time", "fieldtype": "Datetime", "width": 150},
		{"label": "Activity", "fieldname": "activity_type", "fieldtype": "Data", "width": 160},
		{"label": "Detail", "fieldname": "detail", "fieldtype": "Data", "width": 260},
		{"label": "Docstatus", "fieldname": "docstatus", "fieldtype": "Int", "width": 90}
	]

	molds = (
		[filters["mold"]]
		if filters.get("mold")
		else frappe.get_all("Mold", filters={"docstatus": 1}, pluck="name")
	)
	data = []
	for mold_name in molds:
		for row in get_mold_activity_rows(mold_name):
			row["mold"] = mold_name
			data.append(row)

	data.sort(key=lambda row: (str(row.get("posting_time") or ""), row.get("name") or ""), reverse=True)
	return columns, data

import frappe


def execute(filters=None):
	filters = filters or {}
	conditions = []
	values = {}

	if filters.get("mold"):
		conditions.append("mold = %(mold)s")
		values["mold"] = filters["mold"]
	if filters.get("alteration_type"):
		conditions.append("alteration_type = %(alteration_type)s")
		values["alteration_type"] = filters["alteration_type"]
	if filters.get("from_date"):
		conditions.append("alteration_date >= %(from_date)s")
		values["from_date"] = filters["from_date"]
	if filters.get("to_date"):
		conditions.append("alteration_date <= %(to_date)s")
		values["to_date"] = filters["to_date"]

	where_clause = f"where docstatus = 1{' and ' + ' and '.join(conditions) if conditions else ''}"
	columns = [
		{"label": "Alteration", "fieldname": "name", "fieldtype": "Link", "options": "Mold Alteration", "width": 170},
		{"label": "Mold", "fieldname": "mold", "fieldtype": "Link", "options": "Mold", "width": 150},
		{"label": "Type", "fieldname": "alteration_type", "fieldtype": "Data", "width": 90},
		{"label": "Date", "fieldname": "alteration_date", "fieldtype": "Date", "width": 100},
		{"label": "From Version", "fieldname": "from_version", "fieldtype": "Data", "width": 100},
		{"label": "To Version", "fieldname": "to_version", "fieldtype": "Data", "width": 100},
		{"label": "TPR Ref", "fieldname": "tpr_reference", "fieldtype": "Data", "width": 120},
		{"label": "MCR Ref", "fieldname": "mcr_reference", "fieldtype": "Data", "width": 120},
		{"label": "Reason", "fieldname": "reason", "fieldtype": "Small Text", "width": 250}
	]
	data = frappe.db.sql(
		f"""
		select name, mold, alteration_type, alteration_date, from_version, to_version, tpr_reference, mcr_reference, reason
		from `tabMold Alteration`
		{where_clause}
		order by alteration_date desc, modified desc
		""",
		values,
		as_dict=True,
	)
	return columns, data

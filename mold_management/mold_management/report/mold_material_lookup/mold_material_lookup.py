import frappe


def execute(filters=None):
	filters = filters or {}
	conditions = []
	values = {}

	if filters.get("material_item"):
		conditions.append("mdm.material_item = %(material_item)s")
		values["material_item"] = filters["material_item"]
	if filters.get("applicable_item"):
		conditions.append("mdm.applicable_item = %(applicable_item)s")
		values["applicable_item"] = filters["applicable_item"]

	where_clause = f"where m.docstatus = 1{' and ' + ' and '.join(conditions) if conditions else ''}"
	columns = [
		{"label": "Mold", "fieldname": "mold", "fieldtype": "Link", "options": "Mold", "width": 150},
		{"label": "Material Item", "fieldname": "material_item", "fieldtype": "Link", "options": "Item", "width": 140},
		{"label": "Material Name", "fieldname": "material_name", "fieldtype": "Data", "width": 180},
		{"label": "Grade", "fieldname": "grade", "fieldtype": "Data", "width": 120},
		{"label": "Color / Spec", "fieldname": "color_spec", "fieldtype": "Data", "width": 150},
		{"label": "Ratio %", "fieldname": "ratio_percent", "fieldtype": "Percent", "width": 90},
		{"label": "Applicable Item", "fieldname": "applicable_item", "fieldtype": "Link", "options": "Item", "width": 140},
		{"label": "Notes", "fieldname": "notes", "fieldtype": "Data", "width": 220}
	]
	data = frappe.db.sql(
		f"""
		select
			mdm.parent as mold,
			mdm.material_item,
			mdm.material_name,
			mdm.grade,
			mdm.color_spec,
			mdm.ratio_percent,
			mdm.applicable_item,
			mdm.notes
		from `tabMold Default Material` mdm
		join `tabMold` m on m.name = mdm.parent
		{where_clause}
		order by mdm.material_item asc, mdm.parent asc
		""",
		values,
		as_dict=True,
	)
	return columns, data

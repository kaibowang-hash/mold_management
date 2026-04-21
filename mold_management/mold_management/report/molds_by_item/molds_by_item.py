import frappe


def execute(filters=None):
	filters = filters or {}
	conditions = []
	values = {}

	if filters.get("item_code"):
		conditions.append("mp.item_code = %(item_code)s")
		values["item_code"] = filters["item_code"]
	if filters.get("status"):
		conditions.append("m.status = %(status)s")
		values["status"] = filters["status"]

	columns = [
		{"label": "Mold", "fieldname": "mold", "fieldtype": "Link", "options": "Mold", "width": 150},
		{"label": "Mold Name", "fieldname": "mold_name", "fieldtype": "Data", "width": 180},
		{"label": "Item Code", "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 150},
		{"label": "Item Name", "fieldname": "item_name", "fieldtype": "Data", "width": 200},
		{"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 140},
		{"label": "Version", "fieldname": "current_version", "fieldtype": "Data", "width": 90},
		{"label": "Warehouse", "fieldname": "current_warehouse", "fieldtype": "Link", "options": "Warehouse", "width": 140},
		{"label": "Location", "fieldname": "current_location", "fieldtype": "Link", "options": "Location", "width": 140},
		{"label": "Cycle (s)", "fieldname": "cycle_time_seconds", "fieldtype": "Float", "width": 100},
		{"label": "Priority", "fieldname": "priority", "fieldtype": "Int", "width": 90}
	]

	data = frappe.db.sql(
		f"""
		select
			m.name as mold,
			m.mold_name,
			mp.item_code,
			mp.item_name,
			m.status,
			m.current_version,
			m.current_warehouse,
			m.current_location,
			mp.cycle_time_seconds,
			mp.priority
		from `tabMold Product` mp
		join `tabMold` m on m.name = mp.parent
		where m.docstatus = 1
			{"and " + " and ".join(conditions) if conditions else ""}
		order by mp.item_code asc, mp.priority asc, m.name asc
		""",
		values,
		as_dict=True,
	)
	return columns, data

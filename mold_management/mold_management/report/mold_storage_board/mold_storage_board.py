import frappe


def execute(filters=None):
	filters = filters or {}
	conditions = []
	values = {}

	if filters.get("warehouse"):
		conditions.append("msl.warehouse = %(warehouse)s")
		values["warehouse"] = filters["warehouse"]
	if filters.get("location"):
		conditions.append("msl.location = %(location)s")
		values["location"] = filters["location"]
	if filters.get("storage_status"):
		conditions.append("msl.storage_status = %(storage_status)s")
		values["storage_status"] = filters["storage_status"]
	if filters.get("current_mold"):
		conditions.append("msl.current_mold = %(current_mold)s")
		values["current_mold"] = filters["current_mold"]

	columns = [
		{
			"label": "Storage Code",
			"fieldname": "storage_code",
			"fieldtype": "Link",
			"options": "Mold Storage Location",
			"width": 150,
		},
		{"label": "Warehouse", "fieldname": "warehouse", "fieldtype": "Link", "options": "Warehouse", "width": 150},
		{"label": "Location", "fieldname": "location", "fieldtype": "Link", "options": "Location", "width": 140},
		{"label": "Storage Bin", "fieldname": "storage_bin", "fieldtype": "Data", "width": 130},
		{"label": "Storage Status", "fieldname": "storage_status", "fieldtype": "Data", "width": 150},
		{"label": "Current Mold", "fieldname": "current_mold", "fieldtype": "Link", "options": "Mold", "width": 150},
		{"label": "Linked Asset", "fieldname": "linked_asset", "fieldtype": "Link", "options": "Asset", "width": 150},
		{"label": "Mold Status", "fieldname": "mold_status", "fieldtype": "Data", "width": 140},
		{"label": "Last Activity On", "fieldname": "last_activity_on", "fieldtype": "Datetime", "width": 180},
	]

	data = frappe.db.sql(
		f"""
		select
			msl.name as storage_code,
			msl.warehouse,
			msl.location,
			msl.storage_bin,
			msl.storage_status,
			msl.current_mold,
			msl.linked_asset,
			msl.mold_status,
			msl.last_activity_on
		from `tabMold Storage Location` msl
		where msl.docstatus = 1
			{"and " + " and ".join(conditions) if conditions else ""}
		order by msl.warehouse asc, msl.location asc, msl.storage_bin asc
		""",
		values,
		as_dict=True,
	)
	return columns, data

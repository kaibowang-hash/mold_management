STANDARD_CUSTOM_FIELDS = {
	"Asset": [
		{
			"fieldname": "custom_mold_management_mold",
			"label": "Mold",
			"fieldtype": "Link",
			"options": "Mold",
			"insert_after": "location",
			"allow_on_submit": 1,
			"read_only": 1,
			"in_list_view": 1,
			"no_copy": 1,
			"description": "Owned by the Mold Management app.",
		}
	],
	"Asset Movement Item": [
		{
			"fieldname": "custom_mold_management_source_warehouse",
			"label": "Source Warehouse",
			"fieldtype": "Link",
			"options": "Warehouse",
			"insert_after": "source_location",
			"allow_on_submit": 1,
			"description": "Owned by the Mold Management app.",
		},
		{
			"fieldname": "custom_mold_management_source_storage_bin",
			"label": "Source Storage Bin",
			"fieldtype": "Data",
			"insert_after": "custom_mold_management_source_warehouse",
			"allow_on_submit": 1,
			"description": "Owned by the Mold Management app.",
		},
		{
			"fieldname": "custom_mold_management_target_warehouse",
			"label": "Target Warehouse",
			"fieldtype": "Link",
			"options": "Warehouse",
			"insert_after": "target_location",
			"allow_on_submit": 1,
			"description": "Owned by the Mold Management app.",
		},
		{
			"fieldname": "custom_mold_management_target_storage_bin",
			"label": "Target Storage Bin",
			"fieldtype": "Data",
			"insert_after": "custom_mold_management_target_warehouse",
			"allow_on_submit": 1,
			"description": "Owned by the Mold Management app.",
		},
	],
}


def get_standard_custom_field_names():
	names = []
	for doctype, fields in STANDARD_CUSTOM_FIELDS.items():
		for field in fields:
			names.append(f"{doctype}-{field['fieldname']}")
	return names

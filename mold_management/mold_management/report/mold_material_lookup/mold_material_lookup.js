frappe.query_reports["Mold Material Lookup"] = {
	filters: [
		{
			fieldname: "material_item",
			label: __("Material Item"),
			fieldtype: "Link",
			options: "Item",
		},
		{
			fieldname: "applicable_item",
			label: __("Applicable Item"),
			fieldtype: "Link",
			options: "Item",
		},
	],
};

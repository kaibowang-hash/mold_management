frappe.query_reports["Molds By Item"] = {
	filters: [
		{
			fieldname: "item_code",
			label: __("Item Code"),
			fieldtype: "Link",
			options: "Item",
		},
		{
			fieldname: "status",
			label: __("Status"),
			fieldtype: "Select",
			options: "\nActive\nIssued\nUnder Maintenance\nUnder External Maintenance\nOutsourced\nScrapped",
		},
	],
};

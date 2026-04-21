frappe.query_reports["Mold Storage Board"] = {
	filters: [
		{
			fieldname: "warehouse",
			label: __("Warehouse"),
			fieldtype: "Link",
			options: "Warehouse",
		},
		{
			fieldname: "location",
			label: __("Location"),
			fieldtype: "Link",
			options: "Location",
		},
		{
			fieldname: "storage_status",
			label: __("Storage Status"),
			fieldtype: "Select",
			options: "\nAvailable\nPending Asset Link\nActive\nIssued\nUnder Maintenance\nUnder External Maintenance\nOutsourced\nScrapped",
		},
		{
			fieldname: "current_mold",
			label: __("Current Mold"),
			fieldtype: "Link",
			options: "Mold",
		},
	],
};

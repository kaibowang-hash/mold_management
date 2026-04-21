frappe.query_reports["Mold Alteration History"] = {
	filters: [
		{
			fieldname: "mold",
			label: __("Mold"),
			fieldtype: "Link",
			options: "Mold",
		},
		{
			fieldname: "alteration_type",
			label: __("Type"),
			fieldtype: "Select",
			options: "\nMajor\nMinor",
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
		},
	],
};

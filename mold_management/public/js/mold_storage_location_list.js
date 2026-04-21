frappe.listview_settings["Mold Storage Location"] = frappe.listview_settings["Mold Storage Location"] || {};

(() => {
	const settings = frappe.listview_settings["Mold Storage Location"];

	settings.get_indicator = function (doc) {
		const status = doc.storage_status || "";
		const color = {
			Available: "green",
			"Pending Asset Link": "orange",
			Active: "green",
			Issued: "blue",
			"Under Maintenance": "orange",
			"Under External Maintenance": "orange",
			Outsourced: "purple",
			Scrapped: "red",
		}[status] || "gray";

		return [__(status || "Unknown"), color, `storage_status,=,${status}`];
	};
})();

frappe.require("/assets/mold_management/js/mold_shared.js");

frappe.listview_settings["Mold"] = frappe.listview_settings["Mold"] || {};

(() => {
	const settings = frappe.listview_settings["Mold"];
	const previous_onload = settings.onload;

	settings.get_indicator = function (doc) {
		const status = doc.status || "";
		const color = {
			"Pending Asset Link": "orange",
			Active: "green",
			Issued: "blue",
			"Under Maintenance": "orange",
			"Under External Maintenance": "orange",
			Outsourced: "purple",
			Scrapped: "red",
		}[status] || "gray";
		return [__(status || "Unknown"), color, `status,=,${status}`];
	};

	settings.onload = function (listview) {
		if (typeof previous_onload === "function") {
			try {
				previous_onload(listview);
			} catch (error) {
				console.error(error);
			}
		}

		if (listview.__mm_label_sheet_btn_added) return;
		listview.__mm_label_sheet_btn_added = true;

		listview.page.add_inner_button(__("扫码打开模具"), function () {
			mold_management.ui.open_mold_barcode_prompt({
				action_label: __("Open Mold"),
				on_resolved(mold) {
					frappe.set_route("Form", "Mold", mold.name);
				},
			});
		});

		listview.page.add_inner_button(__("批量打印标签(A4 Sheet)"), function () {
			const selected = (listview.get_checked_items() || []).map((row) => row.name);
			if (!selected.length) {
				frappe.msgprint(__("Please select at least one Mold."));
				return;
			}

			frappe.call({
				method: "frappe.client.get_list",
				args: {
					doctype: "Mold",
					fields: ["name", "mold_name", "current_version", "company"],
					filters: [["Mold", "name", "in", selected]],
					limit_page_length: selected.length,
				},
				callback: function (response) {
					mold_management.ui.open_mold_label_sheet(response.message || []);
				},
			});
		});
	};
})();

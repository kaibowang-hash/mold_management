frappe.require("/assets/mold_management/js/mold_shared.js");

frappe.ui.form.on("Mold Trial Report", {
	refresh(frm) {
		apply_mold_item_query(frm);
		mold_management.ui.attach_scan_mold_button(frm, "mold");
		if (!frm.is_new() && !frm.doc.condition_sheet) {
			frm.add_custom_button(__("Create Condition Sheet"), () => {
				mold_management.ui.server_action({
					method: "mold_management.api.mold.create_condition_sheet_from_trial_report",
					args: { trial_report: frm.doc.name },
					freeze_message: __("Creating Condition Sheet..."),
					callback(r) {
						if (r.message) {
							frm.reload_doc();
							mold_management.ui.route_to_doc(r.message);
						}
					},
				});
			}, __("Actions"));
		}
	},
	mold(frm) {
		apply_mold_item_query(frm);
	},
});

function apply_mold_item_query(frm) {
	frm.set_query("item_code", () => {
		if (!frm.doc.mold) return {};
		return {
			query: "mold_management.api.mold.get_mold_product_item_query",
			filters: { mold: frm.doc.mold },
		};
	});
}

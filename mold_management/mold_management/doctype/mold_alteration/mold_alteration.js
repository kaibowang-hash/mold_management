frappe.require("/assets/mold_management/js/mold_shared.js");

frappe.ui.form.on("Mold Alteration", {
	refresh(frm) {
		mold_management.ui.boot_sap_state(frm);
		mold_management.ui.run_sap_state(frm, (setState) => {
			if (!frm.doc.reason) {
				setState("reason", "Error", __("Reason is required"));
			}
		});
		mold_management.ui.attach_scan_mold_button(frm, "mold");
		refresh_version_preview(frm);
		mold_management.ui.auto_print_submitted_doc(frm);
	},
	mold(frm) {
		refresh_version_preview(frm);
	},
	alteration_type(frm) {
		refresh_version_preview(frm);
	},
});

function refresh_version_preview(frm) {
	if (!frm.doc.mold || !frm.doc.alteration_type) return;

	frappe.call({
		method: "mold_management.mold_management.doctype.mold_alteration.mold_alteration.get_next_version_preview",
		args: {
			mold: frm.doc.mold,
			alteration_type: frm.doc.alteration_type,
		},
		callback: function (r) {
			if (r.message) {
				frm.set_value("from_version", r.message.from_version);
				frm.set_value("to_version", r.message.to_version);
			}
		},
	});
}

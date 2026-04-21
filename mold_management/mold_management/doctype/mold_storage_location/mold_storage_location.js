frappe.require("/assets/mold_management/js/mold_shared.js");

frappe.ui.form.on("Mold Storage Location", {
	refresh(frm) {
		mold_management.ui.boot_sap_state(frm);
		mold_management.ui.run_sap_state(frm);

		if (frm.doc.current_mold) {
			frm.add_custom_button(__("Open Mold"), function () {
				frappe.set_route("Form", "Mold", frm.doc.current_mold);
			}, __("Mold"));
		}
	},
});


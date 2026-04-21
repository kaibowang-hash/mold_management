frappe.require("/assets/mold_management/js/mold_shared.js");

frappe.ui.form.on("Mold Spare Part Usage", {
	refresh(frm) {
		mold_management.ui.boot_sap_state(frm);
		mold_management.ui.run_sap_state(frm);
		mold_management.ui.attach_scan_mold_button(frm, "mold");
	},
});

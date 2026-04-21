frappe.require("/assets/mold_management/js/mold_shared.js");

frappe.ui.form.on("Mold Spare Part", {
	refresh(frm) {
		mold_management.ui.boot_sap_state(frm);
		mold_management.ui.run_sap_state(frm);
	},
});

frappe.require("/assets/mold_management/js/mold_shared.js");

frappe.ui.form.on("Asset Movement", {
	refresh(frm) {
		mold_management.ui.auto_print_submitted_doc(frm);
	},
});

frappe.require("/assets/mold_management/js/mold_shared.js");

frappe.ui.form.on("Asset", {
	refresh(frm) {
		const mold = frm.doc.custom_mold_management_mold;
		if (mold && frm.doc.docstatus === 1) {
			frm.add_custom_button(__("Open Mold"), function () {
				frappe.set_route("Form", "Mold", mold);
			}, __("Mold"));
		}

		mold_management.ui.auto_print_submitted_doc(frm);
	},
});

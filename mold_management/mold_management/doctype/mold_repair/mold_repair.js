frappe.require("/assets/mold_management/js/mold_shared.js");

frappe.ui.form.on("Mold Repair", {
	refresh(frm) {
		mold_management.ui.boot_sap_state(frm);
		mold_management.ui.run_sap_state(frm, (setState) => {
			if (!frm.doc.problem_description) {
				setState("problem_description", "Error", __("Problem Description is required"));
			}
			if (["Ready for Acceptance", "Accepted"].includes(frm.doc.status) && !frm.doc.actions_performed) {
				setState("actions_performed", "Error", __("Actions Performed is required before acceptance"));
			}
		});
		mold_management.ui.attach_scan_mold_button(frm, "mold");
		mold_management.ui.auto_print_submitted_doc(frm);
	},
});

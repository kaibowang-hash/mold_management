frappe.require("/assets/mold_management/js/mold_shared.js");

frappe.ui.form.on("Mold Outsource", {
	refresh(frm) {
		mold_management.ui.boot_sap_state(frm);
		mold_management.ui.run_sap_state(frm);
		mold_management.ui.attach_scan_mold_button(frm, "mold");
		mold_management.ui.auto_print_submitted_doc(frm);

		if (frm.doc.docstatus === 1 && frm.doc.outsource_status === "Open") {
			frm.add_custom_button(__("Mark Returned"), function () {
				const dialog = new frappe.ui.Dialog({
					title: __("Mark Returned"),
					fields: [
						{ fieldname: "actual_return_date", fieldtype: "Date", label: __("Actual Return Date"), default: frappe.datetime.get_today(), reqd: 1 },
						{ fieldname: "return_result", fieldtype: "Select", label: __("Return Result"), options: "Active\nUnder Maintenance", reqd: 1 },
					],
					primary_action_label: __("Confirm"),
					primary_action(values) {
						frappe.call({
							method: "mold_management.mold_management.doctype.mold_outsource.mold_outsource.mark_returned",
							args: {
								name: frm.doc.name,
								actual_return_date: values.actual_return_date,
								return_result: values.return_result,
							},
							freeze: true,
							freeze_message: __("Updating Outsource Return..."),
							callback: function () {
								dialog.hide();
								frm.reload_doc();
							},
						});
					},
				});
				dialog.show();
			}, __("Mold"));
		}
	},
});

frappe.require("/assets/mold_management/js/mold_shared.js");

frappe.ui.form.on("Item", {
	refresh(frm) {
		if (frm.is_new()) return;

		frm.add_custom_button(__("View Molds"), function () {
			frappe.call({
				method: "mold_management.api.mold.get_item_molds",
				args: { item_code: frm.doc.name },
				callback: function (r) {
					const rows = r.message || [];
					mold_management.ui.show_table_dialog({
						title: __("Molds for {0}", [frm.doc.name]),
						columns: [
							{ label: __("Mold"), fieldname: "mold" },
							{ label: __("Status"), fieldname: "status" },
							{ label: __("Warehouse"), fieldname: "current_warehouse" },
							{ label: __("Priority"), fieldname: "priority" },
							{ label: __("Output Qty"), fieldname: "output_qty" },
						],
						rows,
						row_renderer(row, index) {
							const rowClass = index === 0 ? "mm-row-current" : "";
							return `
								<tr class="${rowClass}">
									<td>
										${mold_management.ui.doc_link("Mold", row.mold)}
										<div class="mm-muted">${frappe.utils.escape_html(row.mold_name || "")}</div>
									</td>
									<td>
										${mold_management.ui.status_badge_html(row.status || "")}
										<div class="mm-muted">${__("Version")} ${frappe.utils.escape_html(row.current_version || "-")}</div>
									</td>
									<td>
										<div>${frappe.utils.escape_html(row.current_warehouse || "-")}</div>
										<div class="mm-muted">${frappe.utils.escape_html(row.current_location || "-")}</div>
										<div class="mm-muted">${frappe.utils.escape_html(row.current_holder_summary || "")}</div>
									</td>
									<td>${frappe.utils.escape_html(row.priority || "")}</td>
									<td>${frappe.utils.escape_html(row.output_qty || "")}</td>
								</tr>
							`;
						},
						export_method: "mold_management.api.mold.export_item_molds",
						export_args: { item_code: frm.doc.name },
						secondary_action_label: __("Open Report"),
						secondary_action() {
							frappe.set_route("query-report", "Molds By Item", { item_code: frm.doc.name });
						},
					});
				},
			});
		}, __("View"));

		frm.add_custom_button(__("View Molding Conditions"), function () {
			frappe.call({
				method: "mold_management.api.mold.get_active_molding_conditions_for_item",
				args: { item_code: frm.doc.name },
				callback: function (r) {
					const rows = r.message || [];
					mold_management.ui.show_table_dialog({
						title: __("Current Molding Conditions for {0}", [frm.doc.name]),
						columns: [
							{ label: __("Mold"), fieldname: "mold" },
							{ label: __("Condition Sheet"), fieldname: "name" },
							{ label: __("Version"), fieldname: "version" },
							{ label: __("Configuration"), fieldname: "configuration_label" },
							{ label: __("Cycle (s)"), fieldname: "cycle_time_seconds" },
						],
						rows,
						row_renderer(row, index) {
							const rowClass = index === 0 ? "mm-row-current" : "";
							return `
								<tr class="${rowClass}">
									<td>
										${mold_management.ui.doc_link("Mold", row.mold)}
										<div class="mm-muted">${frappe.utils.escape_html(row.mold_name || "")}</div>
									</td>
									<td>${mold_management.ui.doc_link("Injection Molding Condition Sheet", row.name)}</td>
									<td>${frappe.utils.escape_html(row.version || "")}</td>
									<td>
										<div>${frappe.utils.escape_html(row.configuration_label || row.output_group || "-")}</div>
										<div class="mm-muted">${frappe.utils.escape_html(row.color_spec || "")}</div>
									</td>
									<td>${frappe.utils.escape_html(row.cycle_time_seconds || "")}</td>
								</tr>
							`;
						},
					});
				},
			});
		}, __("View"));
	},
});

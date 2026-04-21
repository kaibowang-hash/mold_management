frappe.require("/assets/mold_management/js/mold_shared.js");

const MM_PENDING_STATUS = "Pending Asset Link";
const MM_VIEW_GROUP = __("View");
const MM_ACTION_GROUP = __("Actions");
const MM_LIFECYCLE_FIELDS = [
	"status",
	"linked_asset",
	"current_version",
	"current_warehouse",
	"current_location",
	"current_storage_bin",
	"current_holder_summary",
	"current_transaction_type",
	"current_transaction_ref",
	"last_transfer_on",
	"last_issue_on",
	"last_receipt_on",
	"last_repair_on",
	"last_maintenance_on",
	"last_outsource_on",
	"last_alteration_on",
];

frappe.ui.form.on("Mold", {
	refresh(frm) {
		mold_management.ui.boot_sap_state(frm);
		mold_management.ui.ensure_attention_styles();
		mold_management.ui.ensure_surface_styles();
		apply_setting_defaults_in_ui(frm);

		if (frm.is_new() && !frm.doc.status) {
			frm.set_value("status", MM_PENDING_STATUS);
		}
		if (frm.is_new() && !frm.doc.current_version) {
			frm.set_value("current_version", "A0");
		}

		setup_basic_edit_mode(frm);
		render_form_banner(frm);
		run_field_state(frm);
		add_action_buttons(frm);
		render_barcode_panel(frm);
	},
	validate(frm) {
		validate_family_mold(frm);
		run_field_state(frm);
	},
	after_save(frm) {
		frm.__basic_edit_mode = false;
		render_barcode_panel(frm);
	},
	is_family_mold(frm) {
		render_form_banner(frm);
		run_field_state(frm);
	},
	mold_products_add(frm) {
		render_form_banner(frm);
		run_field_state(frm);
	},
	mold_products_remove(frm) {
		render_form_banner(frm);
		run_field_state(frm);
	},
});

function escape_html(value) {
	return frappe.utils.escape_html(value == null ? "" : String(value));
}

function render_barcode_panel(frm) {
	mold_management.ui.render_mold_barcode_panel(frm, "barcode_tools_html");
}

function run_field_state(frm) {
	mold_management.ui.run_sap_state(frm, (setState) => {
		if (!frm.doc.linked_asset) {
			setState("linked_asset", "Warning", __("Asset has not been created or linked yet"));
			setState("status", "Warning", __("Status stays pending until an asset is linked"));
		}
		if (frm.doc.ownership_type === "Customer" && !frm.doc.customer) {
			setState("customer", "Error", __("Customer is required"));
		}
		if (frm.doc.is_family_mold && (frm.doc.mold_products || []).length < 2) {
			setState("mold_name", "Error", __("Family Mold requires at least two Mold Product rows"));
		}
		if (!frm.doc.default_warehouse) {
			setState("default_warehouse", "Warning", __("Default mold warehouse is recommended"));
		}
		if (!frm.doc.default_storage_bin) {
			setState("default_storage_bin", "Information", __("Default storage bin is empty"));
		}
		if (frm.doc.ownership_type === "Company" && !frm.doc.asset_value) {
			setState("asset_value", "Warning", __("Company-owned molds need Asset Value before asset creation"));
		}
	});
}

function apply_setting_defaults_in_ui(frm) {
	if (
		frm.doc.default_warehouse &&
		frm.doc.default_location &&
		frm.doc.default_storage_bin
	) {
		return;
	}

	if (frm.__mm_defaults_loading) return;
	frm.__mm_defaults_loading = true;

	frappe.call({
		method: "frappe.client.get",
		args: {
			doctype: "Mold Management Settings",
			name: "Mold Management Settings",
		},
		callback: function (r) {
			frm.__mm_defaults_loading = false;
			const settings = r.message || {};
			const values = {};
			if (!frm.doc.default_warehouse && settings.default_mold_warehouse) {
				values.default_warehouse = settings.default_mold_warehouse;
			}
			if (!frm.doc.default_location && settings.default_mold_location) {
				values.default_location = settings.default_mold_location;
			}
			if (!frm.doc.default_storage_bin && settings.default_mold_storage_bin) {
				values.default_storage_bin = settings.default_mold_storage_bin;
			}
			if (Object.keys(values).length) {
				frm.set_value(values);
			}
		},
	});
}

function validate_family_mold(frm) {
	if (frm.doc.is_family_mold && (frm.doc.mold_products || []).length < 2) {
		frappe.throw(__("Family Mold requires at least two Mold Product rows."));
	}
}

function render_form_banner(frm) {
	const banners = [];

	if (!frm.doc.linked_asset) {
		banners.push({
			tone: "orange",
			html: `
				<div><strong>${__("Asset setup is pending")}</strong></div>
				<div>${__("Create or link the mold Asset first. Until then the lifecycle actions remain locked.")}</div>
			`,
		});
	}

	if (frm.__basic_edit_mode) {
		banners.push({
			tone: "green",
			html: `
				<div><strong>${__("Basic Info Edit is active")}</strong></div>
				<div>${__("Only non-lifecycle fields are unlocked. Save to keep changes or cancel to reload the locked record.")}</div>
			`,
		});
	} else if (frm.doc.docstatus === 1) {
		banners.push({
			tone: "blue",
			html: `
				<div><strong>${__("Submitted mold is locked")}</strong></div>
				<div>${__("Use Basic Info Edit for non-lifecycle changes. Status, current location, current transaction and version stay system-controlled.")}</div>
			`,
		});
	}

	if (frm.doc.is_family_mold && (frm.doc.mold_products || []).length < 2) {
		banners.push({
			tone: "orange",
			html: `
				<div><strong>${__("Family Mold validation is incomplete")}</strong></div>
				<div>${__("At least two Mold Product rows are required before save or submit.")}</div>
			`,
		});
	}

	if (!banners.length) {
		frm.layout.show_message();
		return;
	}

	const html = `
		<div class="mm-banner-stack">
			${banners
				.map(
					(banner) =>
						`<div class="mm-banner mm-banner-${banner.tone}">${banner.html}</div>`
				)
				.join("")}
		</div>
	`;
	frm.layout.show_message(html, banners[0].tone || "blue", true);
}

function setup_basic_edit_mode(frm) {
	if (frm.is_new() || frm.doc.docstatus !== 1) return;

	if (frm.__basic_edit_mode) {
		unlock_basic_fields(frm);
		frm.add_custom_button(__("Cancel Basic Info Edit"), function () {
			frm.__basic_edit_mode = false;
			frm.reload_doc();
		}, MM_ACTION_GROUP);
		return;
	}

	lock_main_fields(frm);
	frm.add_custom_button(__("Basic Info Edit"), function () {
		frm.__basic_edit_mode = true;
		frm.refresh();
	}, MM_ACTION_GROUP);
}

function lock_main_fields(frm) {
	(frm.meta.fields || []).forEach((df) => {
		if (["Section Break", "Column Break", "Tab Break", "Table", "Button", "HTML"].includes(df.fieldtype)) {
			return;
		}
		frm.set_df_property(df.fieldname, "read_only", 1);
	});
}

function unlock_basic_fields(frm) {
	(frm.meta.fields || []).forEach((df) => {
		if (["Section Break", "Column Break", "Tab Break", "Table", "Button", "HTML"].includes(df.fieldtype)) {
			return;
		}

		const original = frappe.meta.get_docfield(frm.doctype, df.fieldname);
		const locked = MM_LIFECYCLE_FIELDS.includes(df.fieldname) || (original && original.read_only === 1);
		frm.set_df_property(df.fieldname, "read_only", locked ? 1 : 0);
	});
}

function add_action_buttons(frm) {
	if (frm.is_new()) return;

	add_common_buttons(frm);

	const labelButton = frm.add_custom_button(__("Print Label"), function () {
		mold_management.ui.open_mold_label_sheet([
			{
				name: frm.doc.name,
				mold_name: frm.doc.mold_name,
				current_version: frm.doc.current_version,
				company: frm.doc.company,
			},
		]);
	}, MM_VIEW_GROUP);

	const scanButton = frm.add_custom_button(__("Scan Mold Barcode"), function () {
		mold_management.ui.open_mold_barcode_prompt({
			action_label: __("Open Mold"),
			on_resolved(mold) {
				frappe.set_route("Form", "Mold", mold.name);
			},
		});
	}, MM_VIEW_GROUP);

	if (labelButton && labelButton.removeClass) {
		labelButton.removeClass("btn-default");
	}
	if (scanButton && scanButton.removeClass) {
		scanButton.removeClass("btn-default");
	}

	if (!frm.doc.linked_asset) {
		const assetButton = frm.add_custom_button(__("Create / Link Asset"), function () {
			open_asset_setup_dialog(frm);
		});
		mold_management.ui.highlight_attention_button(assetButton);
		return;
	}

	add_contextual_return_button(frm);

	frm.add_custom_button(__("Transfer"), () => run_guarded_action(frm, "Transfer", () => open_movement_dialog(frm, "Transfer")), MM_ACTION_GROUP);
	frm.add_custom_button(__("Issue"), () => run_guarded_action(frm, "Issue", () => open_movement_dialog(frm, "Issue")), MM_ACTION_GROUP);
	frm.add_custom_button(__("Repair"), () => run_guarded_action(frm, "Repair", () => open_repair_dialog(frm)), MM_ACTION_GROUP);
	frm.add_custom_button(__("Maintenance"), () => run_guarded_action(frm, "Maintenance", () => open_maintenance_dialog(frm)), MM_ACTION_GROUP);
	frm.add_custom_button(__("Outsource"), () => run_guarded_action(frm, "Outsource", () => open_outsource_dialog(frm)), MM_ACTION_GROUP);
	frm.add_custom_button(__("Use Spare Part"), () => open_spare_part_usage_dialog(frm), MM_ACTION_GROUP);
	frm.add_custom_button(__("Alteration"), () => open_alteration_choice_dialog(frm), MM_ACTION_GROUP);
	frm.add_custom_button(__("Scrap"), () => run_guarded_action(frm, "Scrap", () => scrap_asset(frm)), MM_ACTION_GROUP);
}

function add_common_buttons(frm) {
	frm.add_custom_button(__("View Logs"), () => show_logs(frm), MM_VIEW_GROUP);
	frm.add_custom_button(__("View Spare Parts"), () => show_spare_parts(frm), MM_VIEW_GROUP);
	frm.add_custom_button(__("Storage Board"), function () {
		open_storage_board_page(frm.doc.name);
	}, MM_VIEW_GROUP);
}

function add_contextual_return_button(frm) {
	const currentType = frm.doc.current_transaction_type;
	const currentRef = frm.doc.current_transaction_ref;

	if (!currentType || !currentRef) {
		return;
	}

	if (currentType === "Asset Movement" && frm.doc.status === "Issued") {
		frm.add_custom_button(__("Return"), () => {
			run_guarded_action(frm, "Receipt", () => create_receipt_to_default(frm));
		}, MM_ACTION_GROUP);
		return;
	}

	if (
		currentType === "Mold Outsource" &&
		["Outsourced", "Under External Maintenance"].includes(frm.doc.status)
	) {
		frm.add_custom_button(__("Return Outsource"), () => {
			run_guarded_action(frm, "Return Outsource", () => open_outsource_return_dialog(frm));
		}, MM_ACTION_GROUP);
	}
}

function open_alteration_choice_dialog(frm) {
	const dialog = new frappe.ui.Dialog({
		title: __("Alteration"),
		fields: [
			{
				fieldname: "alteration_type",
				fieldtype: "Select",
				label: __("Alteration Type"),
				options: "Minor\nMajor",
				default: "Minor",
				reqd: 1,
			},
			{
				fieldname: "alteration_help",
				fieldtype: "HTML",
				options: `
					<div class="mm-barcode-panel" style="padding:12px 14px 10px;">
						<div style="font-weight:700; margin-bottom:8px;">${__("Version Progression")}</div>
						<div class="mm-muted">${__("Minor keeps the letter and increments the number, for example A0 -> A1. Major increments the letter and resets the number, for example A3 -> B0.")}</div>
					</div>
				`,
			},
		],
		primary_action_label: __("Create"),
		primary_action(values) {
			const alterationType = values.alteration_type || "Minor";
			run_guarded_action(frm, `${alterationType} Alteration`, () => create_alteration(frm, alterationType));
			dialog.hide();
		},
	});

	dialog.show();
}

function run_guarded_action(frm, actionName, actionFn) {
	frappe.call({
		method: "mold_management.api.mold.get_action_guardrail",
		args: {
			mold_name: frm.doc.name,
			action_name: actionName,
		},
		callback: function (r) {
			const guardrail = r.message || {};
			if (guardrail.allowed) {
				actionFn();
				return;
			}
			show_guardrail_dialog(frm, guardrail);
		},
	});
}

function show_guardrail_dialog(frm, guardrail) {
	const dialog = new frappe.ui.Dialog({
		title: guardrail.title || __("Action Blocked"),
		fields: [
			{
				fieldname: "guardrail_html",
				fieldtype: "HTML",
			},
		],
		primary_action_label: guardrail.resolution_label || __("Close"),
		primary_action() {
			if (!guardrail.resolution_action) {
				dialog.hide();
				return;
			}
			dialog.hide();
			run_guardrail_resolution(frm, guardrail);
		},
	});

	const relatedDoc = guardrail.reference_doctype && guardrail.reference_name
		? `<div class="mm-muted" style="margin-top:8px;">${__("Related Document")}: ${mold_management.ui.doc_link(
				guardrail.reference_doctype,
				guardrail.reference_name
		  )}</div>`
		: "";
	const html = `
		<div class="mm-barcode-panel" style="padding:14px 14px 10px;">
			<div style="font-weight:700; margin-bottom:8px;">${escape_html(guardrail.title || __("Lifecycle Guardrail"))}</div>
			<div>${escape_html(guardrail.message || __("This action is blocked by the mold lifecycle state."))}</div>
			${relatedDoc}
		</div>
	`;
	dialog.fields_dict.guardrail_html.$wrapper.html(html);

	if (guardrail.reference_doctype && guardrail.reference_name) {
		dialog.set_secondary_action_label(__("Open Related Document"));
		dialog.set_secondary_action(function () {
			dialog.hide();
			frappe.set_route("Form", guardrail.reference_doctype, guardrail.reference_name);
		});
	}

	dialog.show();
}

function run_guardrail_resolution(frm, guardrail) {
	if (guardrail.resolution_action === "create_receipt_to_default") {
		mold_management.ui.server_action({
			method: "mold_management.api.mold.create_receipt_to_default_from_mold",
			args: { mold_name: frm.doc.name },
			freeze_message: __("Returning Mold To Default Location..."),
			callback: function (r) {
				frm.reload_doc();
				if (r.message) {
					mold_management.ui.route_to_doc(r.message);
				}
			},
		});
		return;
	}

	if (guardrail.resolution_action === "return_open_outsource") {
		open_outsource_return_dialog(frm, guardrail);
	}
}

function open_asset_setup_dialog(frm) {
	frappe.call({
		method: "mold_management.api.mold.get_asset_setup_details",
		args: { mold_name: frm.doc.name },
		callback: function (r) {
			const ctx = r.message || {};
			const dialog = new frappe.ui.Dialog({
				title: __("Create / Link Asset"),
				fields: [
					{
						fieldname: "setup_mode",
						fieldtype: "Select",
						label: __("Action"),
						options: "Create New Asset\nLink Existing Asset",
						default: "Create New Asset",
						reqd: 1,
					},
					{
						fieldname: "asset_rules",
						fieldtype: "HTML",
					},
					{
						fieldname: "asset_name",
						fieldtype: "Link",
						label: __("Asset"),
						options: "Asset",
						depends_on: "eval:doc.setup_mode==='Link Existing Asset'",
						get_query() {
							const filters = {};
							if (ctx.allowed_asset_item) filters.item_code = ctx.allowed_asset_item;
							if (ctx.asset_category) filters.asset_category = ctx.asset_category;
							return { filters };
						},
					},
				],
				primary_action_label: __("Continue"),
				primary_action(values) {
					mold_management.ui.server_action({
						method: "mold_management.api.mold.setup_asset_for_mold",
						args: {
							mold_name: frm.doc.name,
							setup_mode: values.setup_mode,
							asset_name: values.asset_name,
						},
						freeze_message:
							values.setup_mode === "Link Existing Asset"
								? __("Linking Asset...")
								: __("Creating Asset..."),
						callback: function (response) {
							dialog.hide();
							frm.reload_doc();
							if (response.message) {
								mold_management.ui.route_to_doc(response.message);
							}
						},
					});
				},
			});

			const html = `
				<div class="mm-barcode-panel" style="padding:14px 14px 10px;">
					<div style="font-weight:700; margin-bottom:8px;">${__("Asset Guardrails")}</div>
					<div class="mm-muted" style="margin-bottom:10px;">
						${__("Only the configured mold asset item and asset category are allowed. One asset cannot be linked to multiple molds.")}
					</div>
					<div class="mm-barcode-meta">
						<div class="mm-barcode-meta-item">
							<span class="mm-barcode-meta-label">${__("Allowed Item For This Mold")}</span>
							<div>${escape_html(ctx.allowed_asset_item || "-")}</div>
						</div>
						<div class="mm-barcode-meta-item">
							<span class="mm-barcode-meta-label">${__("Ownership Type")}</span>
							<div>${escape_html(ctx.ownership_type || "-")}</div>
						</div>
						<div class="mm-barcode-meta-item">
							<span class="mm-barcode-meta-label">${__("Required Asset Category")}</span>
							<div>${escape_html(ctx.asset_category || "-")}</div>
						</div>
						<div class="mm-barcode-meta-item">
							<span class="mm-barcode-meta-label">${__("Default Warehouse")}</span>
							<div>${escape_html(ctx.default_warehouse || "-")}</div>
						</div>
						<div class="mm-barcode-meta-item">
							<span class="mm-barcode-meta-label">${__("Default Location")}</span>
							<div>${escape_html(ctx.default_location || "-")}</div>
						</div>
						<div class="mm-barcode-meta-item">
							<span class="mm-barcode-meta-label">${__("Default Storage Bin")}</span>
							<div>${escape_html(ctx.default_storage_bin || "-")}</div>
						</div>
						<div class="mm-barcode-meta-item">
							<span class="mm-barcode-meta-label">${__("Asset Value Required")}</span>
							<div>${ctx.requires_asset_value ? __("Yes") : __("No")}</div>
						</div>
					</div>
				</div>
			`;
			dialog.fields_dict.asset_rules.$wrapper.html(html);
			dialog.show();
		},
	});
}

function open_movement_dialog(frm, purpose) {
	const isTransfer = purpose === "Transfer";
	const isIssue = purpose === "Issue";
	const isReceipt = purpose === "Receipt";
	const dialog = new frappe.ui.Dialog({
		title: __(purpose),
		fields: [
			{
				fieldname: "target_location",
				fieldtype: "Link",
				label: __("Target Location"),
				options: "Location",
				default: isTransfer || isReceipt ? frm.doc.default_location : "",
				reqd: isTransfer || isReceipt,
			},
			{
				fieldname: "target_warehouse",
				fieldtype: "Link",
				label: __("Target Warehouse"),
				options: "Warehouse",
				default: isTransfer || isReceipt ? frm.doc.default_warehouse : "",
				reqd: isTransfer || isReceipt,
			},
			{
				fieldname: "target_storage_bin",
				fieldtype: "Data",
				label: __("Target Storage Bin"),
				default: isTransfer || isReceipt ? frm.doc.default_storage_bin : "",
			},
			{
				fieldname: "to_employee",
				fieldtype: "Link",
				label: __("To Employee"),
				options: "Employee",
				reqd: isIssue,
			},
		],
		primary_action_label: __("Create"),
		primary_action(values) {
			mold_management.ui.server_action({
				method: "mold_management.api.mold.create_asset_movement_from_mold",
				args: {
					mold_name: frm.doc.name,
					purpose,
					values,
				},
				freeze_message: __("Generating {0}...", [purpose]),
				callback: function (r) {
					dialog.hide();
					if (r.message) mold_management.ui.route_to_doc(r.message);
				},
			});
		},
	});
	dialog.show();
}

function open_repair_dialog(frm) {
	const dialog = new frappe.ui.Dialog({
		title: __("Repair"),
		fields: [
			{
				fieldname: "failure_date",
				fieldtype: "Datetime",
				label: __("Failure Date"),
				default: frappe.datetime.now_datetime(),
			},
			{ fieldname: "description", fieldtype: "Small Text", label: __("Error Description"), reqd: 1 },
		],
		primary_action_label: __("Create"),
		primary_action(values) {
			mold_management.ui.server_action({
				method: "mold_management.api.mold.create_asset_repair_from_mold",
				args: { mold_name: frm.doc.name, values },
				freeze_message: __("Generating Repair..."),
				callback: function (r) {
					dialog.hide();
					if (r.message) mold_management.ui.route_to_doc(r.message);
				},
			});
		},
	});
	dialog.show();
}

function open_maintenance_dialog(frm) {
	const dialog = new frappe.ui.Dialog({
		title: __("Maintenance"),
		fields: [
			{
				fieldname: "maintenance_task",
				fieldtype: "Data",
				label: __("Task"),
				default: __("General Mold Maintenance"),
				reqd: 1,
			},
			{ fieldname: "description", fieldtype: "Small Text", label: __("Description") },
			{
				fieldname: "next_due_date",
				fieldtype: "Date",
				label: __("Due Date"),
				default: frappe.datetime.get_today(),
			},
			{
				fieldname: "periodicity",
				fieldtype: "Select",
				label: __("Periodicity"),
				options: "Daily\nWeekly\nMonthly\nQuarterly\nHalf-yearly\nYearly\n2 Yearly\n3 Yearly",
				default: "Monthly",
			},
			{
				fieldname: "assign_to",
				fieldtype: "Link",
				label: __("Assign To"),
				options: "User",
				default: frappe.session.user,
			},
		],
		primary_action_label: __("Create"),
		primary_action(values) {
			mold_management.ui.server_action({
				method: "mold_management.api.mold.create_asset_maintenance_from_mold",
				args: { mold_name: frm.doc.name, values },
				freeze_message: __("Generating Maintenance..."),
				callback: function (r) {
					dialog.hide();
					if (r.message) mold_management.ui.route_to_doc(r.message);
				},
			});
		},
	});
	dialog.show();
}

function open_outsource_dialog(frm) {
	const dialog = new frappe.ui.Dialog({
		title: __("Outsource"),
		fields: [
			{
				fieldname: "outsource_type",
				fieldtype: "Select",
				label: __("Outsource Type"),
				options: "External Production\nExternal Maintenance\nExternal Modification\nExternal Inspection\nOther",
				reqd: 1,
			},
			{
				fieldname: "outsource_date",
				fieldtype: "Date",
				label: __("Outsource Date"),
				default: frappe.datetime.get_today(),
				reqd: 1,
			},
			{ fieldname: "expected_return_date", fieldtype: "Date", label: __("Expected Return Date") },
			{
				fieldname: "destination_type",
				fieldtype: "Select",
				label: __("Destination Type"),
				options: "Supplier\nCustomer\nOther",
				reqd: 1,
			},
			{ fieldname: "supplier", fieldtype: "Link", label: __("Supplier"), options: "Supplier" },
			{ fieldname: "customer", fieldtype: "Link", label: __("Customer"), options: "Customer" },
			{ fieldname: "destination_name", fieldtype: "Data", label: __("Destination Name") },
			{ fieldname: "destination_location", fieldtype: "Data", label: __("Destination Location") },
			{ fieldname: "notes", fieldtype: "Small Text", label: __("Notes") },
		],
		primary_action_label: __("Create"),
		primary_action(values) {
			mold_management.ui.server_action({
				method: "mold_management.api.mold.create_outsource_from_mold",
				args: { mold_name: frm.doc.name, values },
				freeze_message: __("Generating Outsource..."),
				callback: function (r) {
					dialog.hide();
					if (r.message) mold_management.ui.route_to_doc(r.message);
				},
			});
		},
	});
	dialog.show();
}

function open_outsource_return_dialog(frm) {
	const dialog = new frappe.ui.Dialog({
		title: __("Return Outsource"),
		fields: [
			{
				fieldname: "actual_return_date",
				fieldtype: "Date",
				label: __("Actual Return Date"),
				default: frappe.datetime.get_today(),
				reqd: 1,
			},
			{
				fieldname: "return_result",
				fieldtype: "Select",
				label: __("Return Result"),
				options: "Active\nUnder Maintenance",
				default: "Active",
				reqd: 1,
			},
		],
		primary_action_label: __("Return"),
		primary_action(values) {
			mold_management.ui.server_action({
				method: "mold_management.api.mold.return_open_outsource_from_mold",
				args: {
					mold_name: frm.doc.name,
					actual_return_date: values.actual_return_date,
					return_result: values.return_result,
				},
				freeze_message: __("Returning Outsourced Mold..."),
				callback: function (r) {
					dialog.hide();
					frm.reload_doc();
					if (r.message) {
						mold_management.ui.route_to_doc(r.message);
					}
				},
			});
		},
	});
	dialog.show();
}

function create_receipt_to_default(frm) {
	mold_management.ui.server_action({
		method: "mold_management.api.mold.create_receipt_to_default_from_mold",
		args: { mold_name: frm.doc.name },
		freeze_message: __("Returning Mold To Default Location..."),
		callback: function (r) {
			frm.reload_doc();
			if (r.message) {
				mold_management.ui.route_to_doc(r.message);
			}
		},
	});
}

function open_storage_board_page(currentMold) {
	frappe.route_options = currentMold ? { current_mold: currentMold } : null;
	frappe.set_route("mold-storage-board");
}

function open_spare_part_usage_dialog(frm) {
	frappe.call({
		method: "mold_management.api.mold.get_mold_spare_parts",
		args: { mold_name: frm.doc.name },
		callback: function (r) {
			const rows = r.message || [];
			if (!rows.length) {
				frappe.msgprint(__("No spare parts are mapped to this mold yet."));
				return;
			}

			const options = rows.map((row) => `${row.name} | ${row.part_code} | ${row.part_name}`);
			const dialog = new frappe.ui.Dialog({
				title: __("Use Spare Part"),
				fields: [
					{
						fieldname: "spare_part_label",
						fieldtype: "Select",
						label: __("Spare Part"),
						options: options.join("\n"),
						reqd: 1,
					},
					{
						fieldname: "usage_date",
						fieldtype: "Datetime",
						label: __("Usage Date"),
						default: frappe.datetime.now_datetime(),
						reqd: 1,
					},
					{ fieldname: "qty", fieldtype: "Float", label: __("Qty"), default: 1, reqd: 1 },
					{
						fieldname: "reference_doctype",
						fieldtype: "Link",
						label: __("Reference Doctype"),
						options: "DocType",
					},
					{
						fieldname: "reference_name",
						fieldtype: "Dynamic Link",
						label: __("Reference Name"),
						options: "reference_doctype",
					},
					{ fieldname: "remarks", fieldtype: "Small Text", label: __("Remarks") },
				],
				primary_action_label: __("Create"),
				primary_action(values) {
					const spare_part = (values.spare_part_label || "").split(" | ")[0];
					mold_management.ui.server_action({
						method: "mold_management.api.mold.create_spare_part_usage_from_mold",
						args: {
							mold_name: frm.doc.name,
							values: {
								spare_part,
								usage_date: values.usage_date,
								qty: values.qty,
								reference_doctype: values.reference_doctype,
								reference_name: values.reference_name,
								remarks: values.remarks,
							},
						},
						freeze_message: __("Recording Spare Part Usage..."),
						callback: function (response) {
							dialog.hide();
							if (response.message) {
								mold_management.ui.route_to_doc(response.message);
							}
						},
					});
				},
			});
			dialog.show();
		},
	});
}

function create_alteration(frm, alterationType) {
	mold_management.ui.server_action({
		method: "mold_management.api.mold.create_alteration_from_mold",
		args: { mold_name: frm.doc.name, alteration_type: alterationType },
		freeze_message: __("Generating {0} Alteration...", [alterationType]),
		callback: function (r) {
			if (r.message) mold_management.ui.route_to_doc(r.message);
		},
	});
}

function show_logs(frm) {
	frappe.call({
		method: "mold_management.api.mold.get_mold_activity_log",
		args: { mold_name: frm.doc.name },
		callback: function (r) {
			const rows = r.message || [];
			mold_management.ui.show_table_dialog({
				title: __("Mold Activity Log"),
				columns: [
					{ label: __("Date"), fieldname: "posting_time" },
					{ label: __("Document"), fieldname: "name" },
					{ label: __("Activity"), fieldname: "activity_type" },
					{ label: __("Detail"), fieldname: "detail" },
				],
				rows,
				row_renderer(row, index) {
					const rowClass = index === 0 ? "mm-row-current" : "";
					const dateText = row.posting_time
						? frappe.datetime.str_to_user(row.posting_time).split(" ")[0]
						: "-";
					return `
						<tr class="${rowClass}">
							<td>${escape_html(dateText)}</td>
							<td>
								${mold_management.ui.doc_link(row.reference_doctype, row.name)}
								<div class="mm-muted">${escape_html(row.reference_doctype || "")}</div>
							</td>
							<td>${mold_management.ui.status_badge_html(row.activity_type || __("Open"))}</td>
							<td>${escape_html(row.detail || "-")}</td>
						</tr>
					`;
				},
				export_method: "mold_management.api.mold.export_mold_activity_log",
				export_args: { mold_name: frm.doc.name },
				secondary_action_label: __("Open Activity Report"),
				secondary_action() {
					frappe.set_route("query-report", "Mold Activity Log", { mold: frm.doc.name });
				},
			});
		},
	});
}

function show_spare_parts(frm) {
	frappe.call({
		method: "mold_management.api.mold.get_mold_spare_parts",
		args: { mold_name: frm.doc.name },
		callback: function (r) {
			const rows = r.message || [];
			mold_management.ui.show_table_dialog({
				title: __("Spare Parts for {0}", [frm.doc.name]),
				columns: [
					{ label: __("Part"), fieldname: "part_code" },
					{ label: __("Supplier"), fieldname: "supplier" },
					{ label: __("Specification"), fieldname: "specification" },
					{ label: __("Fitment"), fieldname: "fitment_notes" },
				],
				rows,
				row_renderer(row) {
					const preferred = Number(row.is_preferred || 0) ? mold_management.ui.badge_html(__("Preferred"), "green") : "";
					return `
						<tr>
							<td>
								<div><strong>${escape_html(row.part_code || row.name || "-")}</strong> ${preferred}</div>
								<div class="mm-muted">${escape_html(row.part_name || "")}</div>
							</td>
							<td>${escape_html(row.supplier || "-")}</td>
							<td>${escape_html(row.specification || "-")}</td>
							<td>${escape_html(row.fitment_notes || "-")}</td>
						</tr>
					`;
				},
				export_method: "mold_management.api.mold.export_mold_spare_parts",
				export_args: { mold_name: frm.doc.name },
				empty_message: __("No spare parts are mapped to this mold yet."),
			});
		},
	});
}

function scrap_asset(frm) {
	frappe.confirm(__("Scrap the linked asset for this mold?"), function () {
		mold_management.ui.server_action({
			method: "mold_management.api.mold.scrap_linked_asset",
			args: { mold_name: frm.doc.name },
			freeze_message: __("Scrapping Asset..."),
			callback: function () {
				frm.reload_doc();
			},
		});
	});
}

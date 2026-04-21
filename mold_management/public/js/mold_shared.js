frappe.provide("mold_management.ui");

(function () {
	if (mold_management.ui.__initialized) {
		return;
	}

	mold_management.ui.__initialized = true;

	function escape_html(value) {
		return frappe.utils.escape_html(value == null ? "" : String(value));
	}

	function as_user_datetime(value) {
		if (!value) return "";
		try {
			return frappe.datetime.str_to_user(value);
		} catch (error) {
			return value;
		}
	}

	function as_user_date(value) {
		if (!value) return "";
		try {
			return frappe.datetime.str_to_user(value).split(" ")[0];
		} catch (error) {
			return value;
		}
	}

	mold_management.ui.route_to_doc = function (result) {
		if (result && result.doctype && result.name) {
			frappe.set_route("Form", result.doctype, result.name);
		}
	};

	mold_management.ui.route_to_list = function (doctype, filters) {
		frappe.set_route("List", doctype, filters || {});
	};

	mold_management.ui.server_action = function ({ method, args, freeze_message, callback }) {
		frappe.call({
			method,
			args: args || {},
			freeze: true,
			freeze_message: freeze_message || __("Processing..."),
			callback: function (r) {
				if (callback) {
					callback(r);
				}
			},
		});
	};

	mold_management.ui.open_print = function (doctype, docname, print_format) {
		const query = new URLSearchParams({
			doctype,
			name: docname,
			format: print_format || "Standard",
			no_letterhead: 0,
			trigger_print: 1,
		});
		window.open(`/printview?${query.toString()}`, "_blank");
	};

	mold_management.ui.auto_print_submitted_doc = function (frm) {
		if (!frm.doc || frm.doc.docstatus !== 1 || !frm.doc.name) {
			return;
		}

		const cache_key = `${frm.doctype}::${frm.doc.name}::mold_auto_print`;
		if (window.sessionStorage.getItem(cache_key)) {
			return;
		}

		frappe.call({
			method: "mold_management.api.mold.get_print_context",
			args: {
				doctype: frm.doctype,
				docname: frm.doc.name,
			},
			callback: function (r) {
				const data = r.message || {};
				if (!data.should_print) {
					return;
				}
				window.sessionStorage.setItem(cache_key, "1");
				mold_management.ui.open_print(frm.doctype, frm.doc.name, data.print_format);
			},
		});
	};

	mold_management.ui.export_via_post = function (method, args) {
		if (typeof open_url_post === "function") {
			open_url_post(`/api/method/${method}`, args || {});
			return;
		}

		const query = new URLSearchParams(args || {});
		window.open(`/api/method/${method}?${query.toString()}`, "_blank");
	};

	mold_management.ui.ensure_surface_styles = function () {
		const style_id = "mm-surface-style";
		if (document.getElementById(style_id)) return;

		const style = document.createElement("style");
		style.id = style_id;
		style.textContent = `
			.mm-table-shell {
				max-height: 64vh;
				overflow: auto;
				border: 1px solid #d8dee9;
				border-radius: 14px;
				background: linear-gradient(180deg, #ffffff 0%, #fbfcfd 100%);
			}
			.mm-table {
				margin: 0;
				font-size: 12px;
			}
			.mm-table thead th {
				position: sticky;
				top: 0;
				z-index: 1;
				background: #f5f7fa;
				border-bottom: 1px solid #d8dee9;
				font-weight: 700;
				color: #334155;
			}
			.mm-table tbody tr:hover {
				background: #f8fafc;
			}
			.mm-table tbody tr.mm-row-current {
				background: #eef4ff;
				font-weight: 600;
			}
			.mm-muted {
				color: #64748b;
				font-size: 11px;
			}
			.mm-pill {
				display: inline-flex;
				align-items: center;
				padding: 2px 8px;
				border-radius: 999px;
				border: 1px solid #d3d8df;
				background: #f8fafc;
				color: #475569;
				font-size: 10px;
				font-weight: 600;
				line-height: 1.35;
				white-space: nowrap;
			}
			.mm-pill.mm-pill-blue {
				background: #eef4ff;
				border-color: #bfd3ff;
				color: #1d4ed8;
			}
			.mm-pill.mm-pill-green {
				background: #ecfdf3;
				border-color: #b7ebc6;
				color: #107e3e;
			}
			.mm-pill.mm-pill-orange {
				background: #fff7ed;
				border-color: #fed7aa;
				color: #c2410c;
			}
			.mm-pill.mm-pill-red {
				background: #fff1f2;
				border-color: #fecdd3;
				color: #be123c;
			}
			.mm-pill.mm-pill-purple {
				background: #f5f3ff;
				border-color: #ddd6fe;
				color: #6d28d9;
			}
			.mm-banner-stack {
				display: flex;
				flex-direction: column;
				gap: 8px;
			}
			.mm-banner {
				border-radius: 12px;
				padding: 10px 12px;
				border: 1px solid #d8dee9;
				background: #ffffff;
				line-height: 1.5;
			}
			.mm-banner.mm-banner-blue {
				background: #eef4ff;
				border-color: #bfd3ff;
				color: #1d4ed8;
			}
			.mm-banner.mm-banner-orange {
				background: #fff7ed;
				border-color: #fdba74;
				color: #c2410c;
			}
			.mm-banner.mm-banner-green {
				background: #ecfdf3;
				border-color: #b7ebc6;
				color: #107e3e;
			}
			.mm-barcode-panel {
				border: 1px solid #d8dee9;
				border-radius: 16px;
				padding: 18px 18px 14px;
				background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
			}
			.mm-barcode-panel-head {
				display: flex;
				justify-content: space-between;
				align-items: flex-start;
				gap: 12px;
				margin-bottom: 10px;
			}
			.mm-barcode-panel-title {
				font-size: 16px;
				font-weight: 700;
				color: #1f2937;
			}
			.mm-barcode-meta {
				display: grid;
				grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
				gap: 8px 12px;
				margin: 8px 0 12px;
			}
			.mm-barcode-meta-item {
				padding: 9px 10px;
				border-radius: 10px;
				background: #ffffff;
				border: 1px solid #e2e8f0;
			}
			.mm-barcode-meta-label {
				display: block;
				font-size: 10px;
				font-weight: 700;
				text-transform: uppercase;
				letter-spacing: 0.04em;
				color: #64748b;
				margin-bottom: 3px;
			}
			.mm-barcode-svg {
				border: 1px dashed #cbd5e1;
				border-radius: 12px;
				background: #fff;
				padding: 12px 14px 6px;
				text-align: center;
			}
			.mm-barcode-svg svg {
				width: 100% !important;
				max-width: 420px;
				height: 54px;
			}
			.mm-barcode-actions {
				display: flex;
				flex-wrap: wrap;
				gap: 8px;
				margin-top: 12px;
			}
			.mm-barcode-actions .btn {
				border-radius: 999px;
			}
		`;
		document.head.appendChild(style);
	};

	mold_management.ui.badge_html = function (label, tone) {
		if (!label) return "";
		const palette = {
			blue: "mm-pill-blue",
			green: "mm-pill-green",
			orange: "mm-pill-orange",
			red: "mm-pill-red",
			purple: "mm-pill-purple",
		};
		return `<span class="mm-pill ${palette[tone] || ""}">${escape_html(label)}</span>`;
	};

	mold_management.ui.status_badge_html = function (status) {
		const tone = {
			"Pending Asset Link": "orange",
			Active: "green",
			Issued: "blue",
			"Under Maintenance": "orange",
			"Under External Maintenance": "orange",
			Outsourced: "purple",
			Scrapped: "red",
			Available: "green",
			Open: "orange",
			Returned: "green",
		}[status] || "blue";
		return mold_management.ui.badge_html(status, tone);
	};

	mold_management.ui.doc_link = function (doctype, name, label) {
		if (!doctype || !name) return "-";
		const route = frappe.utils.get_form_link(doctype, name);
		return `<a href="${route}">${escape_html(label || name)}</a>`;
	};

	mold_management.ui.show_table_dialog = function ({
		title,
		columns,
		rows,
		export_method,
		export_args,
		row_renderer,
		empty_message,
		primary_action_label,
		secondary_action_label,
		secondary_action,
	}) {
		mold_management.ui.ensure_surface_styles();

		const dialog = new frappe.ui.Dialog({
			title: title || __("Results"),
			size: "extra-large",
			fields: [
				{
					fieldname: "table_html",
					fieldtype: "HTML",
				},
			],
			primary_action_label: primary_action_label || (export_method ? __("Export CSV / Excel") : __("Close")),
			primary_action: function () {
				if (export_method) {
					mold_management.ui.export_via_post(export_method, export_args || {});
				} else {
					dialog.hide();
				}
			},
		});

		if (secondary_action_label && typeof secondary_action === "function") {
			dialog.set_secondary_action_label(secondary_action_label);
			dialog.set_secondary_action(function () {
				secondary_action(dialog);
			});
		}

		const header_html = (columns || [])
			.map((column) => `<th>${escape_html(column.label || "")}</th>`)
			.join("");

		const body_html = (rows || []).length
			? (rows || [])
					.map((row, row_index) => {
						if (typeof row_renderer === "function") {
							return row_renderer(row, row_index);
						}

						return `<tr>${(columns || [])
							.map((column) => {
								let value = row[column.fieldname];
								if (typeof column.formatter === "function") {
									value = column.formatter(value, row, row_index);
								} else if (column.fieldtype === "Date") {
									value = escape_html(as_user_date(value) || "");
								} else if (column.fieldtype === "Datetime") {
									value = escape_html(as_user_datetime(value) || "");
								} else if (column.options && column.fieldtype === "Link" && value) {
									value = mold_management.ui.doc_link(column.options, value);
								} else {
									value = escape_html(value || "");
								}
								return `<td>${value || ""}</td>`;
							})
							.join("")}</tr>`;
					})
					.join("")
			: `<tr><td colspan="${(columns || []).length || 1}" class="text-center text-muted">${escape_html(
					empty_message || __("No records found")
			  )}</td></tr>`;

		const html = `
			<div class="mm-table-shell">
				<table class="table table-sm mm-table">
					<thead><tr>${header_html}</tr></thead>
					<tbody>${body_html}</tbody>
				</table>
			</div>
		`;

		dialog.fields_dict.table_html.$wrapper.html(html);
		dialog.show();
	};

	mold_management.ui.ensure_attention_styles = function () {
		const style_id = "mm-attention-style";
		if (document.getElementById(style_id)) return;

		const style = document.createElement("style");
		style.id = style_id;
		style.textContent = `
			.mm-attention-button {
				position: relative;
				animation: mm-pulse 1.2s ease-in-out infinite;
				box-shadow: 0 0 0 0 rgba(233, 115, 12, 0.45);
			}
			@keyframes mm-pulse {
				0% { transform: translateY(0); box-shadow: 0 0 0 0 rgba(233, 115, 12, 0.45); }
				70% { transform: translateY(-1px); box-shadow: 0 0 0 10px rgba(233, 115, 12, 0); }
				100% { transform: translateY(0); box-shadow: 0 0 0 0 rgba(233, 115, 12, 0); }
			}
		`;
		document.head.appendChild(style);
	};

	mold_management.ui.highlight_attention_button = function (button) {
		if (button && button.addClass) {
			button.addClass("mm-attention-button");
		}
	};

	mold_management.ui.boot_sap_state = function (frm) {
		if (!frm || !frm.wrapper) return;
		const $scope = $(frm.wrapper);
		$scope.addClass("mm-sap-scope");

		const style_id = "mm-sap-field-style";
		if (document.getElementById(style_id)) return;

		const style = document.createElement("style");
		style.id = style_id;
		style.textContent = `
			.mm-sap-scope {
				--mm-info: #0a6ed1;
				--mm-warn: #e9730c;
				--mm-error: #bb0000;
				--mm-success: #107e3e;
				--mm-corner-size: 10px;
				--mm-corner-thick: 2px;
			}
			.mm-sap-scope .mm-sap-host { position: relative; }
			.mm-sap-scope .mm-sap-host.mm-sap-has-icon .form-control,
			.mm-sap-scope .mm-sap-host.mm-sap-has-icon input,
			.mm-sap-scope .mm-sap-host.mm-sap-has-icon select,
			.mm-sap-scope .mm-sap-host.mm-sap-has-icon textarea { padding-right: 32px !important; }
			.mm-sap-scope .mm-sap-icon {
				position: absolute; right: 8px; top: 50%; transform: translateY(-50%);
				width: 16px; height: 16px; display: flex; align-items: center; justify-content: center;
				font-size: 13px;
			}
			.mm-sap-scope .mm-sap-host[data-mm-level="Information"] { --mm-accent: var(--mm-info); }
			.mm-sap-scope .mm-sap-host[data-mm-level="Warning"] { --mm-accent: var(--mm-warn); }
			.mm-sap-scope .mm-sap-host[data-mm-level="Error"] { --mm-accent: var(--mm-error); }
			.mm-sap-scope .mm-sap-host[data-mm-level="Success"] { --mm-accent: var(--mm-success); }
			.mm-sap-scope .mm-sap-host[data-mm-level] .mm-sap-icon { color: var(--mm-accent); }
			.mm-sap-scope .mm-sap-host[data-mm-level] .form-control,
			.mm-sap-scope .mm-sap-host[data-mm-level] input,
			.mm-sap-scope .mm-sap-host[data-mm-level] select,
			.mm-sap-scope .mm-sap-host[data-mm-level] textarea { border-color: var(--mm-accent) !important; }
			.mm-sap-scope .mm-sap-reqd:focus-within .control-input-wrapper,
			.mm-sap-scope .mm-sap-reqd:focus-within .input-with-feedback,
			.mm-sap-scope .mm-sap-reqd:focus-within .control-input {
				position: relative; overflow: visible;
			}
			.mm-sap-scope .mm-sap-reqd:focus-within .control-input-wrapper::before,
			.mm-sap-scope .mm-sap-reqd:focus-within .input-with-feedback::before,
			.mm-sap-scope .mm-sap-reqd:focus-within .control-input::before {
				content: ""; position: absolute; left: -4px; top: -4px;
				width: var(--mm-corner-size); height: var(--mm-corner-size);
				border-left: var(--mm-corner-thick) solid var(--mm-accent, var(--mm-info));
				border-top: var(--mm-corner-thick) solid var(--mm-accent, var(--mm-info));
			}
			.mm-sap-scope .mm-sap-reqd:focus-within .control-input-wrapper::after,
			.mm-sap-scope .mm-sap-reqd:focus-within .input-with-feedback::after,
			.mm-sap-scope .mm-sap-reqd:focus-within .control-input::after {
				content: ""; position: absolute; right: -4px; bottom: -4px;
				width: var(--mm-corner-size); height: var(--mm-corner-size);
				border-right: var(--mm-corner-thick) solid var(--mm-accent, var(--mm-info));
				border-bottom: var(--mm-corner-thick) solid var(--mm-accent, var(--mm-info));
			}
		`;
		document.head.appendChild(style);
	};

	mold_management.ui.run_sap_state = function (frm, extraEvaluator) {
		if (!frm || !frm.fields_dict) return;

		Object.keys(frm.fields_dict).forEach((fieldname) => {
			const field = frm.fields_dict[fieldname];
			if (field && field.df && field.wrapper) {
				if (field.df.reqd && field.df.fieldtype !== "Check") {
					$(field.wrapper).addClass("mm-sap-reqd");
				} else {
					$(field.wrapper).removeClass("mm-sap-reqd");
				}
				mold_management.ui.clear_field_state(frm, fieldname);
			}
		});

		const stateMap = {};
		const rank = { Error: 4, Warning: 3, Information: 2, Success: 1 };
		const setState = (fieldname, level, tip) => {
			const previous = stateMap[fieldname];
			if (!previous || rank[level] > rank[previous.level]) {
				stateMap[fieldname] = { level, tip };
			}
		};

		Object.keys(frm.fields_dict).forEach((fieldname) => {
			const field = frm.fields_dict[fieldname];
			const skipTypes = new Set([
				"Check",
				"Section Break",
				"Column Break",
				"Tab Break",
				"HTML",
				"Button",
				"Table",
				"Heading",
			]);
			if (!field || !field.df || !field.wrapper || skipTypes.has(field.df.fieldtype) || !field.df.reqd) {
				return;
			}

			const value = frm.doc ? frm.doc[fieldname] : null;
			const empty =
				value === null ||
				value === undefined ||
				(typeof value === "string" && value.trim() === "");
			if (empty) setState(fieldname, "Error", __("Required field is empty"));
		});

		if (typeof extraEvaluator === "function") {
			extraEvaluator(setState);
		}

		Object.keys(stateMap).forEach((fieldname) => {
			const state = stateMap[fieldname];
			mold_management.ui.apply_field_state(frm, fieldname, state.level, state.tip);
		});
	};

	mold_management.ui.apply_field_state = function (frm, fieldname, level, tip) {
		const field = frm.fields_dict[fieldname];
		if (!field || !field.wrapper || field.df.fieldtype === "Check") return;

		let $host = $(field.wrapper).find(".control-input-wrapper").first();
		if (!$host.length) $host = $(field.wrapper).find(".input-with-feedback").first();
		if (!$host.length) $host = $(field.wrapper).find(".control-input").first();
		if (!$host.length) return;

		$host.addClass("mm-sap-host").attr("data-mm-level", level);
		let $icon = $host.find(`.mm-sap-icon[data-mm-field="${fieldname}"]`).first();
		if (!$icon.length) {
			$icon = $(`<span class="mm-sap-icon" data-mm-field="${fieldname}"></span>`);
			$host.append($icon);
		}
		$icon.text({ Information: "ℹ", Warning: "⚠", Error: "⛔", Success: "✓" }[level] || "ℹ");
		if (tip) $icon.attr("title", tip);
		$host.addClass("mm-sap-has-icon");
	};

	mold_management.ui.clear_field_state = function (frm, fieldname) {
		const field = frm.fields_dict[fieldname];
		if (!field || !field.wrapper) return;
		const $host = $(field.wrapper).find(".mm-sap-host").first();
		if (!$host.length) return;
		$host.find(`.mm-sap-icon[data-mm-field="${fieldname}"]`).remove();
		if (!$host.find(".mm-sap-icon").length) {
			$host.removeAttr("data-mm-level").removeClass("mm-sap-host mm-sap-has-icon");
		}
	};

	mold_management.ui.make_barcode_svg = function (value) {
		if (!frappe.ui || !frappe.ui.form || !frappe.ui.form.make_control) {
			return `<div>${escape_html(value || "")}</div>`;
		}

		const $parent = $('<div style="position:fixed;left:-9999px;top:-9999px;opacity:0;"></div>').appendTo(
			document.body
		);
		const control = frappe.ui.form.make_control({
			parent: $parent,
			df: {
				fieldtype: "Barcode",
				options: JSON.stringify({
					format: "CODE128",
					displayValue: true,
					fontSize: 12,
					height: 42,
					width: 1.25,
					margin: 0,
				}),
			},
			render_input: true,
		});
		const svg = control.get_barcode_html(value) || "";
		$parent.remove();
		return svg;
	};

	mold_management.ui.resolve_mold_barcode = function (barcode_value, callback) {
		frappe.call({
			method: "mold_management.api.mold.get_mold_by_barcode",
			args: { barcode_value },
			freeze: true,
			freeze_message: __("Resolving Mold Barcode..."),
			callback: function (r) {
				if (callback) {
					callback(r.message || null);
				}
			},
		});
	};

	mold_management.ui.open_mold_barcode_prompt = function ({
		title,
		action_label,
		description,
		on_resolved,
	}) {
		const dialog = new frappe.ui.Dialog({
			title: title || __("Scan Mold Barcode"),
			fields: [
				{
					fieldname: "barcode_value",
					fieldtype: "Barcode",
					label: __("Mold Barcode"),
					description:
						description || __("Scan the mold label barcode or paste the Mold number directly."),
					reqd: 1,
				},
			],
			primary_action_label: action_label || __("Continue"),
			primary_action(values) {
				mold_management.ui.resolve_mold_barcode(values.barcode_value, function (mold) {
					dialog.hide();
					if (typeof on_resolved === "function") {
						on_resolved(mold);
					}
				});
			},
		});

		dialog.set_secondary_action_label(__("Camera Scan"));
		dialog.set_secondary_action(function () {
			new frappe.ui.Scanner({
				dialog: true,
				multiple: false,
				on_scan(data) {
					const scanned = data && data.result && data.result.text;
					if (scanned) {
						dialog.get_field("barcode_value").set_value(scanned);
					}
				},
			});
		});
		dialog.show();
	};

	mold_management.ui.attach_scan_mold_button = function (frm, target_field, group_label) {
		if (!frm || !target_field || frm.doc.docstatus > 0) return;

		frm.add_custom_button(__("Scan Mold Barcode"), function () {
			mold_management.ui.open_mold_barcode_prompt({
				action_label: __("Use Mold"),
				on_resolved(mold) {
					frm.set_value(target_field, mold.name);
					frappe.show_alert({
						message: __("Loaded Mold {0}", [mold.name]),
						indicator: "green",
					});
				},
			});
		}, group_label || __("Mold"));
	};

	mold_management.ui.render_mold_barcode_panel = function (frm, fieldname) {
		mold_management.ui.ensure_surface_styles();
		if (!frm || !frm.fields_dict || !frm.fields_dict[fieldname]) return;

		const wrapper = frm.fields_dict[fieldname].$wrapper;
		if (!wrapper || !frm.doc.name) {
			wrapper && wrapper.empty();
			return;
		}

		const barcode_svg = mold_management.ui.make_barcode_svg(frm.doc.name);
		const html = `
			<div class="mm-barcode-panel">
				<div class="mm-barcode-panel-head">
					<div>
						<div class="mm-barcode-panel-title">${__("Mold Barcode Center")}</div>
						<div class="mm-muted">${__("Barcode content uses Mold.name and can be scanned in mold lookup workflows.")}</div>
					</div>
					<div>${mold_management.ui.status_badge_html(frm.doc.status || __("Unknown"))}</div>
				</div>
				<div class="mm-barcode-meta">
					<div class="mm-barcode-meta-item">
						<span class="mm-barcode-meta-label">${__("Mold No.")}</span>
						<div><strong>${escape_html(frm.doc.name)}</strong></div>
					</div>
					<div class="mm-barcode-meta-item">
						<span class="mm-barcode-meta-label">${__("Mold Name")}</span>
						<div>${escape_html(frm.doc.mold_name || "-")}</div>
					</div>
					<div class="mm-barcode-meta-item">
						<span class="mm-barcode-meta-label">${__("Current Version")}</span>
						<div>${escape_html(frm.doc.current_version || "-")}</div>
					</div>
					<div class="mm-barcode-meta-item">
						<span class="mm-barcode-meta-label">${__("Linked Asset")}</span>
						<div>${frm.doc.linked_asset ? mold_management.ui.doc_link("Asset", frm.doc.linked_asset) : "-"}</div>
					</div>
					<div class="mm-barcode-meta-item">
						<span class="mm-barcode-meta-label">${__("Current Holder / Destination")}</span>
						<div>${escape_html(frm.doc.current_holder_summary || "-")}</div>
					</div>
				</div>
				<div class="mm-barcode-svg">${barcode_svg}</div>
				<div class="mm-barcode-actions">
					<button type="button" class="btn btn-default btn-sm mm-barcode-print">${__("Print A4 Label")}</button>
					<button type="button" class="btn btn-default btn-sm mm-barcode-scan">${__("Scan Another Mold")}</button>
					<button type="button" class="btn btn-default btn-sm mm-open-storage-board">${__("Open Storage Slots")}</button>
				</div>
			</div>
		`;

		wrapper.html(html);
		wrapper.find(".mm-barcode-print").on("click", function () {
			mold_management.ui.open_mold_label_sheet([
				{
					name: frm.doc.name,
					mold_name: frm.doc.mold_name,
					current_version: frm.doc.current_version,
					company: frm.doc.company,
				},
			]);
		});
		wrapper.find(".mm-barcode-scan").on("click", function () {
			mold_management.ui.open_mold_barcode_prompt({
				action_label: __("Open Mold"),
				on_resolved(mold) {
					frappe.set_route("Form", "Mold", mold.name);
				},
			});
		});
		wrapper.find(".mm-open-storage-board").on("click", function () {
			frappe.set_route("List", "Mold Storage Location", { current_mold: frm.doc.name });
		});
	};

	mold_management.ui.open_mold_label_sheet = function (rows) {
		const labelRows = rows || [];
		if (!labelRows.length) {
			frappe.msgprint(__("Please select at least one Mold."));
			return;
		}

		const labels_html = labelRows
			.map((row) => {
				const barcode_svg = mold_management.ui.make_barcode_svg(row.name);
				return `
					<div class="mm-label">
						<div class="mm-label-title">${escape_html(row.name || "")}</div>
						<div class="mm-label-subtitle">${escape_html(row.mold_name || "")}</div>
						<div class="mm-label-barcode">${barcode_svg}</div>
						<div class="mm-label-meta">
							<span>${escape_html(row.current_version || "")}</span>
							<span>${escape_html(row.company || "")}</span>
						</div>
					</div>
				`;
			})
			.join("");

		const printWindow = window.open("", "_blank");
		if (!printWindow) {
			frappe.msgprint(__("Popup was blocked. Please allow popups and try again."));
			return;
		}

		printWindow.document.write(`
			<html>
				<head>
					<title>${__("Mold Labels")}</title>
					<style>
						@page { size: A4 portrait; margin: 8mm; }
						body { font-family: Arial, sans-serif; margin: 0; padding: 0; color: #1f2937; }
						.mm-label-grid {
							display: grid;
							grid-template-columns: repeat(3, 1fr);
							gap: 4mm;
						}
						.mm-label {
							border: 1px solid #cbd5e1;
							border-radius: 8px;
							padding: 4mm 3.5mm;
							min-height: 28mm;
							display: flex;
							flex-direction: column;
							justify-content: space-between;
							box-sizing: border-box;
							background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
						}
						.mm-label-title { font-weight: 700; font-size: 12px; letter-spacing: 0.2px; }
						.mm-label-subtitle { font-size: 10px; margin-top: 1mm; min-height: 4mm; color: #475569; }
						.mm-label-barcode { margin: 2mm 0 1mm; text-align: center; }
						.mm-label-barcode svg { width: 100% !important; height: 36px; }
						.mm-label-meta {
							display: flex;
							justify-content: space-between;
							gap: 6px;
							font-size: 9px;
							color: #475569;
						}
					</style>
				</head>
				<body>
					<div class="mm-label-grid">${labels_html}</div>
					<script>
						window.onload = function () {
							setTimeout(function () {
								window.print();
							}, 120);
						};
					</script>
				</body>
			</html>
		`);
		printWindow.document.close();
	};
})();

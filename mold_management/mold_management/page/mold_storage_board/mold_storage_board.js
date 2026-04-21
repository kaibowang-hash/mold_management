window.mold_management = window.mold_management || {};

const MM_STORAGE_BOARD_PAGE_STATUS_OPTIONS = [
	"",
	"Available",
	"Pending Asset Link",
	"Active",
	"Issued",
	"Under Maintenance",
	"Under External Maintenance",
	"Outsourced",
	"Scrapped",
];

frappe.pages["mold-storage-board"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Mold Storage Board"),
		single_column: true,
	});

	frappe.require("/assets/mold_management/js/mold_shared.js", () => {
		wrapper.mm_storage_board_page = new MoldStorageBoardPage(page);
		wrapper.mm_storage_board_page.on_show();
	});
};

frappe.pages["mold-storage-board"].on_page_show = function (wrapper) {
	wrapper.mm_storage_board_page?.on_show();
};

class MoldStorageBoardPage {
	constructor(page) {
		this.page = page;
		this.wrapper = $(page.wrapper);
		this.main = $(page.main);
		this.initialized = false;
		this.applying_route_options = false;

		mold_management.ui.ensure_surface_styles();
		this.ensure_styles();
		this.make_filters();
		this.make_body();
		this.page.set_secondary_action(__("Refresh"), () => this.refresh(), "refresh");
	}

	on_show() {
		const applied = this.apply_route_options();
		if (!this.initialized || applied) {
			this.refresh();
		}
		this.initialized = true;
	}

	make_filters() {
		this.warehouse_field = this.page.add_field({
			fieldname: "warehouse",
			label: __("Warehouse"),
			fieldtype: "Link",
			options: "Warehouse",
			change: () => this.refresh_on_filter_change(),
		});

		this.location_field = this.page.add_field({
			fieldname: "location",
			label: __("Location"),
			fieldtype: "Link",
			options: "Location",
			change: () => this.refresh_on_filter_change(),
		});

		this.storage_status_field = this.page.add_field({
			fieldname: "storage_status",
			label: __("Storage Status"),
			fieldtype: "Select",
			options: MM_STORAGE_BOARD_PAGE_STATUS_OPTIONS.join("\n"),
			change: () => this.refresh_on_filter_change(),
		});

		this.current_mold_field = this.page.add_field({
			fieldname: "current_mold",
			label: __("Current Mold"),
			fieldtype: "Link",
			options: "Mold",
			get_query() {
				return {
					filters: {
						docstatus: 1,
					},
				};
			},
			change: () => this.refresh_on_filter_change(),
		});
	}

	make_body() {
		this.main.html(`
			<div class="mm-board-page">
				<div class="mm-board-feedback">Loading submitted storage slots...</div>
				<div class="mm-board-summary"></div>
				<div class="mm-board-groups"></div>
			</div>
		`);
		this.feedback = this.main.find(".mm-board-feedback");
		this.summary = this.main.find(".mm-board-summary");
		this.groups = this.main.find(".mm-board-groups");
	}

	ensure_styles() {
		const style_id = "mm-storage-board-page-style";
		if (document.getElementById(style_id)) return;

		const style = document.createElement("style");
		style.id = style_id;
		style.textContent = `
			.mm-board-page {
				display: flex;
				flex-direction: column;
				gap: 14px;
				padding: 8px 0 20px;
			}
			.mm-board-feedback {
				font-size: 12px;
				color: #64748b;
			}
			.mm-board-summary {
				display: grid;
				grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
				gap: 12px;
			}
			.mm-board-card {
				border: 1px solid #d8dee9;
				border-radius: 16px;
				padding: 14px 15px;
				background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
			}
			.mm-board-card-label {
				display: block;
				font-size: 11px;
				text-transform: uppercase;
				letter-spacing: 0.05em;
				color: #64748b;
				margin-bottom: 6px;
			}
			.mm-board-card-value {
				font-size: 24px;
				line-height: 1.1;
				font-weight: 700;
				color: #0f172a;
			}
			.mm-board-card-note {
				margin-top: 6px;
				font-size: 11px;
				color: #64748b;
			}
			.mm-board-groups {
				display: flex;
				flex-direction: column;
				gap: 16px;
			}
			.mm-board-warehouse {
				border: 1px solid #d8dee9;
				border-radius: 18px;
				padding: 16px;
				background: #fff;
			}
			.mm-board-warehouse-head {
				display: flex;
				justify-content: space-between;
				align-items: center;
				gap: 12px;
				margin-bottom: 12px;
			}
			.mm-board-warehouse-head h3,
			.mm-board-location-head h4 {
				margin: 0;
			}
			.mm-board-warehouse-meta,
			.mm-board-location-meta {
				font-size: 11px;
				color: #64748b;
			}
			.mm-board-location + .mm-board-location {
				margin-top: 14px;
				padding-top: 14px;
				border-top: 1px solid #eef2f7;
			}
			.mm-board-location-head {
				display: flex;
				justify-content: space-between;
				align-items: center;
				gap: 12px;
				margin-bottom: 8px;
			}
		`;
		document.head.appendChild(style);
	}

	apply_route_options() {
		const route_options = frappe.route_options || {};
		if (!Object.keys(route_options).length) return false;

		this.applying_route_options = true;
		this.warehouse_field.set_value(route_options.warehouse || "");
		this.location_field.set_value(route_options.location || "");
		this.storage_status_field.set_value(route_options.storage_status || "");
		this.current_mold_field.set_value(route_options.current_mold || "");
		this.applying_route_options = false;
		frappe.route_options = null;
		return true;
	}

	refresh_on_filter_change() {
		if (this.applying_route_options) return;
		this.refresh();
	}

	get_filters() {
		return {
			warehouse: this.warehouse_field.get_value(),
			location: this.location_field.get_value(),
			storage_status: this.storage_status_field.get_value(),
			current_mold: this.current_mold_field.get_value(),
		};
	}

	refresh() {
		const filters = this.get_filters();
		this.feedback.text(__("Loading submitted storage slots..."));
		frappe.call({
			method: "mold_management.api.mold.get_storage_board_page_data",
			args: filters,
			callback: (r) => {
				const data = r.message || {};
				this.render_summary(data.summary || {});
				this.render_groups(data.groups || [], filters.current_mold);
				this.feedback.text(__("Showing submitted Mold Storage Location records only."));
			},
			error: () => {
				this.feedback.text(__("Failed to load Mold Storage Board."));
				this.groups.html("");
			},
		});
	}

	render_summary(summary) {
		const cards = [
			{
				label: __("Visible Slots"),
				value: summary.total_slots || 0,
				note: __("Submitted storage slot masters after filters"),
			},
			{
				label: __("Occupied"),
				value: summary.occupied_slots || 0,
				note: __("Slots currently carrying a mold"),
			},
			{
				label: __("Available"),
				value: summary.available_slots || 0,
				note: __("Free slots still available"),
			},
			{
				label: __("Locations"),
				value: summary.location_count || 0,
				note: __("{0} warehouses in current view", [summary.warehouse_count || 0]),
			},
		];

		this.summary.html(
			cards
				.map(
					(card) => `
						<div class="mm-board-card">
							<span class="mm-board-card-label">${frappe.utils.escape_html(card.label)}</span>
							<div class="mm-board-card-value">${frappe.utils.escape_html(card.value)}</div>
							<div class="mm-board-card-note">${frappe.utils.escape_html(card.note)}</div>
						</div>
					`
				)
				.join("")
		);
	}

	render_groups(groups, currentMoldFilter) {
		if (!groups.length) {
			this.groups.html(`
				<div class="mm-barcode-panel">
					<div style="font-weight:700; margin-bottom:8px;">${__("No submitted storage slots matched the current filters")}</div>
					<div class="mm-muted">${__("Adjust Warehouse / Location / Status filters or submit Mold Storage Location records first.")}</div>
				</div>
			`);
			return;
		}

		const html = groups
			.map((warehouseGroup) => {
				const locations = (warehouseGroup.locations || [])
					.map((locationGroup) => this.render_location_group(locationGroup, currentMoldFilter))
					.join("");
				const rowCount = (warehouseGroup.locations || []).reduce(
					(total, locationGroup) => total + (locationGroup.row_count || 0),
					0
				);
				return `
					<section class="mm-board-warehouse">
						<div class="mm-board-warehouse-head">
							<div>
								<h3>${frappe.utils.escape_html(warehouseGroup.warehouse_label || __("Unassigned Warehouse"))}</h3>
								<div class="mm-board-warehouse-meta">${__("Submitted storage slots grouped by location")}</div>
							</div>
							${mold_management.ui.badge_html(__("{0} Slots", [rowCount]), "blue")}
						</div>
						${locations}
					</section>
				`;
			})
			.join("");

		this.groups.html(html);
	}

	render_location_group(locationGroup, currentMoldFilter) {
		return `
			<section class="mm-board-location">
				<div class="mm-board-location-head">
					<div>
						<h4>${frappe.utils.escape_html(locationGroup.location_label || __("Unassigned Location"))}</h4>
						<div class="mm-board-location-meta">${__("Storage bins currently grouped under this location")}</div>
					</div>
					${mold_management.ui.badge_html(__("{0} Bins", [locationGroup.row_count || 0]), "green")}
				</div>
				<div class="mm-table-shell">
					<table class="table table-bordered mm-table">
						<thead>
							<tr>
								<th>${__("Storage Bin")}</th>
								<th>${__("Current Mold")}</th>
								<th>${__("Mold Status")}</th>
								<th>${__("Current Holder / Destination")}</th>
								<th>${__("Linked Asset")}</th>
								<th>${__("Current Version")}</th>
								<th>${__("Last Activity")}</th>
							</tr>
						</thead>
						<tbody>
							${(locationGroup.rows || [])
								.map((row) => this.render_row(row, currentMoldFilter))
								.join("")}
						</tbody>
					</table>
				</div>
			</section>
		`;
	}

	render_row(row, currentMoldFilter) {
		const isCurrent = currentMoldFilter && row.current_mold === currentMoldFilter;
		const currentBadge = isCurrent ? ` ${mold_management.ui.badge_html(__("Current"), "blue")}` : "";
		const moldCell = row.current_mold
			? `
				<div>${mold_management.ui.doc_link("Mold", row.current_mold)}${currentBadge}</div>
				<div class="mm-muted">${frappe.utils.escape_html(row.mold_name || "")}</div>
			`
			: `<span class="mm-muted">${__("Available")}</span>`;
		const moldStatus = row.mold_status || row.storage_status || __("Available");
		const slotMeta = [row.storage_code, row.warehouse, row.location].filter(Boolean).join(" / ");
		const assetCell = row.linked_asset
			? mold_management.ui.doc_link("Asset", row.linked_asset)
			: '<span class="mm-muted">-</span>';
		const lastActivity = row.last_activity_on ? frappe.datetime.str_to_user(row.last_activity_on) : "-";

		return `
			<tr class="${isCurrent ? "mm-row-current" : ""}">
				<td>
					<div><strong>${frappe.utils.escape_html(row.storage_bin || "-")}</strong></div>
					<div class="mm-muted">${frappe.utils.escape_html(slotMeta || "-")}</div>
				</td>
				<td>${moldCell}</td>
				<td>
					${mold_management.ui.status_badge_html(moldStatus)}
					<div class="mm-muted">${__("Storage Slot")}: ${frappe.utils.escape_html(row.storage_status || "-")}</div>
				</td>
				<td>${frappe.utils.escape_html(row.current_holder_summary || "-")}</td>
				<td>${assetCell}</td>
				<td>${frappe.utils.escape_html(row.current_version || "-")}</td>
				<td>${frappe.utils.escape_html(lastActivity)}</td>
			</tr>
		`;
	}
}

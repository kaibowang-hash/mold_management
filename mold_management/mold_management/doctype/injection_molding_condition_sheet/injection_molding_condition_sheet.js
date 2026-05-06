frappe.require("/assets/mold_management/js/mold_shared.js");

frappe.ui.form.on("Injection Molding Condition Sheet", {
	refresh(frm) {
		apply_mold_item_query(frm);
		["status", "current_effective", "version", "effective_from", "effective_by", "update_source", "updated_from_version", "updated_to_version"].forEach((fieldname) => {
			frm.set_df_property(fieldname, "read_only", 1);
		});
		mold_management.ui.attach_scan_mold_button(frm, "mold");
		if (!["Obsolete", "Cancelled"].includes(frm.doc.status) && frm.doc.docstatus === 0) {
			frm.add_custom_button(__("Load Paper Template Rows"), () => {
				load_paper_template_rows(frm);
			}, __("Actions"));
		}
		if (frm.is_new() || ["Obsolete", "Cancelled"].includes(frm.doc.status)) return;
		frm.add_custom_button(__("Update Version"), () => {
			frappe.prompt(
				[
					{
						fieldname: "update_reason",
						label: __("Update Reason"),
						fieldtype: "Small Text",
						reqd: 1,
					},
				],
				(values) => {
					frappe.call({
						method: "mold_management.api.mold.create_next_injection_molding_condition_version",
						args: {
							condition_sheet: frm.doc.name,
							update_reason: values.update_reason,
						},
						freeze: true,
						freeze_message: __("Creating new condition version..."),
					}).then((r) => {
						if (r.message) frappe.set_route("Form", "Injection Molding Condition Sheet", r.message);
					});
				},
				__("Update Injection Molding Condition Version")
			);
		});
	},
	mold(frm) {
		apply_mold_item_query(frm);
	},
});

const PAPER_TEMPLATE_ROWS = {
	opening_rows: ["开模1 / Open 1", "开模2 / Open 2", "开模3 / Open 3", "开模4 / Open 4", "开模5 / Open 5"],
	closing_rows: ["锁模1 / Close 1", "锁模2 / Close 2", "锁模3 / Close 3", "锁模4 / Close 4", "锁模5 / Close 5"],
	ejector_rows: ["顶针1 / Ejector 1", "顶针2 / Ejector 2", "退针1 / Return 1", "退针2 / Return 2"],
	injection_rows: [
		"射胶1 / Injection 1",
		"射胶2 / Injection 2",
		"射胶3 / Injection 3",
		"射胶4 / Injection 4",
		"射胶5 / Injection 5",
		"保压1 / Holding 1",
		"保压2 / Holding 2",
		"保压3 / Holding 3",
		"熔胶 / Plasticizing",
		"射退 / Suck Back",
	],
	core_rows: [
		"中子1进 / Core 1 In",
		"中子1退 / Core 1 Out",
		"中子2进 / Core 2 In",
		"中子2退 / Core 2 Out",
		"中子3进 / Core 3 In",
		"中子3退 / Core 3 Out",
		"中子4进 / Core 4 In",
		"中子4退 / Core 4 Out",
		"中子5进 / Core 5 In",
		"中子5退 / Core 5 Out",
	],
};

const TEMPERATURE_TEMPLATE_ROWS = [
	"射咀 T1 / Nozzle T1",
	"射咀 T2 / Nozzle T2",
	"射咀 T3 / Nozzle T3",
	"射咀 T4 / Nozzle T4",
	"射咀 T5 / Nozzle T5",
	"热流道 T1 / Hot Runner T1",
	"热流道 T2 / Hot Runner T2",
	"热流道 T3 / Hot Runner T3",
	"热流道 T4 / Hot Runner T4",
	"热流道 T5 / Hot Runner T5",
	"热流道 T6 / Hot Runner T6",
	"热流道 T7 / Hot Runner T7",
	"热流道 T8 / Hot Runner T8",
];

const MOLD_TEMPERATURE_TEMPLATE_ROWS = [
	"前模 / Cavity Side",
	"后模 / Core Side",
	"滑块 / Slide",
	"单独芯子 / Separate Core",
];

function load_paper_template_rows(frm) {
	let changed = false;
	Object.keys(PAPER_TEMPLATE_ROWS).forEach((fieldname) => {
		changed = add_missing_action_rows(frm, fieldname, PAPER_TEMPLATE_ROWS[fieldname]) || changed;
	});
	changed = add_missing_zone_rows(frm, "temperature_rows", TEMPERATURE_TEMPLATE_ROWS) || changed;
	changed = add_missing_zone_rows(frm, "mold_temperature_rows", MOLD_TEMPERATURE_TEMPLATE_ROWS) || changed;

	if (!changed) {
		frappe.show_alert({ message: __("Paper template rows already exist."), indicator: "blue" });
		return;
	}

	[
		"opening_rows",
		"closing_rows",
		"ejector_rows",
		"injection_rows",
		"core_rows",
		"temperature_rows",
		"mold_temperature_rows",
	].forEach((fieldname) => frm.refresh_field(fieldname));
	frm.dirty();
	frappe.show_alert({ message: __("Paper template rows loaded."), indicator: "green" });
}

function add_missing_action_rows(frm, fieldname, labels) {
	const existing = new Set((frm.doc[fieldname] || []).map((row) => row.action_name));
	let changed = false;
	labels.forEach((label) => {
		if (existing.has(label)) return;
		const row = frm.add_child(fieldname);
		row.action_name = label;
		changed = true;
	});
	return changed;
}

function add_missing_zone_rows(frm, fieldname, labels) {
	const existing = new Set((frm.doc[fieldname] || []).map((row) => row.zone));
	let changed = false;
	labels.forEach((label) => {
		if (existing.has(label)) return;
		const row = frm.add_child(fieldname);
		row.zone = label;
		changed = true;
	});
	return changed;
}

function apply_mold_item_query(frm) {
	frm.set_query("item_code", () => {
		if (!frm.doc.mold) return {};
		return {
			query: "mold_management.api.mold.get_mold_product_item_query",
			filters: { mold: frm.doc.mold },
		};
	});
}

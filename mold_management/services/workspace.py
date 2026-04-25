from __future__ import annotations

import json

import frappe

WORKSPACE_NAME = "Mold Management"
DASHBOARD_BLOCK_NAME = "Mold Management Dashboard"
STORAGE_BOARD_PAGE_NAME = "mold-storage-board"
STORAGE_BOARD_PAGE_LABEL = "Storage Board"

DASHBOARD_HTML = """
<div class="mm-workspace-dashboard">
	<div class="mm-dashboard-head">
		<div>
			<h3 class="mm-title"></h3>
			<p class="mm-subtitle"></p>
		</div>
		<button type="button" class="mm-refresh"></button>
	</div>
	<div class="mm-feedback"></div>
	<div class="mm-summary-grid"></div>
	<div class="mm-secondary-grid"></div>
	<div class="mm-section">
		<div class="mm-section-head">
			<div>
				<h4 class="mm-storage-title"></h4>
				<span class="mm-section-note"></span>
			</div>
			<button type="button" class="mm-open-board"></button>
		</div>
		<div class="mm-storage-board"></div>
	</div>
</div>
"""

DASHBOARD_STYLE = """
:host {
	display: block;
}
.mm-workspace-dashboard {
	border: 1px solid #d8dee9;
	border-radius: 18px;
	padding: 20px;
	background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
	font-family: Inter, "Helvetica Neue", Arial, sans-serif;
	color: #1f2937;
}
.mm-dashboard-head {
	display: flex;
	align-items: flex-start;
	justify-content: space-between;
	gap: 16px;
	margin-bottom: 12px;
}
.mm-dashboard-head h3 {
	margin: 0 0 4px;
	font-size: 20px;
}
.mm-dashboard-head p {
	margin: 0;
	font-size: 12px;
	color: #64748b;
	max-width: 760px;
}
.mm-refresh {
	border: 1px solid #cbd5e1;
	background: #fff;
	border-radius: 999px;
	padding: 7px 14px;
	cursor: pointer;
	font-size: 12px;
	font-weight: 600;
}
.mm-open-board {
	border: 1px solid #cbd5e1;
	background: #eef4ff;
	color: #1d4ed8;
	border-radius: 999px;
	padding: 7px 14px;
	cursor: pointer;
	font-size: 12px;
	font-weight: 700;
}
.mm-feedback {
	margin-bottom: 12px;
	font-size: 12px;
	color: #64748b;
}
.mm-summary-grid,
.mm-secondary-grid {
	display: grid;
	grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
	gap: 12px;
	margin-bottom: 14px;
}
.mm-card {
	border-radius: 14px;
	padding: 14px 15px;
	background: #fff;
	border: 1px solid #e2e8f0;
}
.mm-card-label {
	display: block;
	font-size: 11px;
	text-transform: uppercase;
	letter-spacing: 0.05em;
	color: #64748b;
	margin-bottom: 6px;
}
.mm-card-value {
	font-size: 24px;
	font-weight: 700;
	line-height: 1.1;
}
.mm-card-note {
	margin-top: 6px;
	font-size: 11px;
	color: #64748b;
}
.mm-section {
	border-radius: 16px;
	background: #fff;
	border: 1px solid #e2e8f0;
	padding: 14px;
}
.mm-section-head {
	display: flex;
	align-items: center;
	justify-content: space-between;
	gap: 10px;
	margin-bottom: 10px;
}
.mm-section-head h4 {
	margin: 0;
	font-size: 15px;
}
.mm-section-note {
	font-size: 11px;
	color: #64748b;
}
.mm-table-shell {
	max-height: 420px;
	overflow: auto;
	border: 1px solid #e2e8f0;
	border-radius: 14px;
}
.mm-table {
	width: 100%;
	border-collapse: collapse;
	font-size: 12px;
}
.mm-table thead th {
	position: sticky;
	top: 0;
	background: #f8fafc;
	border-bottom: 1px solid #e2e8f0;
	padding: 9px 10px;
	text-align: left;
}
.mm-table tbody td {
	padding: 9px 10px;
	border-bottom: 1px solid #f1f5f9;
	vertical-align: top;
}
.mm-table tbody tr.is-current {
	background: #eef4ff;
	font-weight: 600;
}
.mm-muted {
	color: #64748b;
	font-size: 11px;
}
.mm-badge {
	display: inline-flex;
	align-items: center;
	padding: 2px 8px;
	border-radius: 999px;
	font-size: 10px;
	font-weight: 700;
	border: 1px solid #d3d8df;
	background: #f8fafc;
	color: #475569;
}
.mm-badge.green { background: #ecfdf3; border-color: #b7ebc6; color: #107e3e; }
.mm-badge.orange { background: #fff7ed; border-color: #fed7aa; color: #c2410c; }
.mm-badge.blue { background: #eef4ff; border-color: #bfd3ff; color: #1d4ed8; }
.mm-badge.red { background: #fff1f2; border-color: #fecdd3; color: #be123c; }
.mm-badge.purple { background: #f5f3ff; border-color: #ddd6fe; color: #6d28d9; }
a {
	color: #0a6ed1;
	text-decoration: none;
}
"""

DASHBOARD_SCRIPT = """
const root = root_element;
const feedback = root.querySelector('.mm-feedback');
const summaryGrid = root.querySelector('.mm-summary-grid');
const secondaryGrid = root.querySelector('.mm-secondary-grid');
const storageBoard = root.querySelector('.mm-storage-board');
const refreshButton = root.querySelector('.mm-refresh');
const openBoardButton = root.querySelector('.mm-open-board');
const titleNode = root.querySelector('.mm-title');
const subtitleNode = root.querySelector('.mm-subtitle');
const storageTitleNode = root.querySelector('.mm-storage-title');
const sectionNoteNode = root.querySelector('.mm-section-note');

const toneMap = {
	'Pending Asset Link': 'orange',
	'Active': 'green',
	'Issued': 'blue',
	'Under Maintenance': 'orange',
	'Under External Maintenance': 'orange',
	'Outsourced': 'purple',
	'Scrapped': 'red',
	'Available': 'green'
};

function escapeHtml(value) {
	return frappe.utils.escape_html(value == null ? '' : String(value));
}

function t(label, args) {
	return __(label, args);
}

function badge(label) {
	const tone = toneMap[label] || 'blue';
	return `<span class="mm-badge ${tone}">${escapeHtml(t(label))}</span>`;
}

function docLink(doctype, name, label) {
	if (!doctype || !name) return '-';
	return `<a href="${frappe.utils.get_form_link(doctype, name)}">${escapeHtml(label || name)}</a>`;
}

function renderCards(cards, target) {
	target.innerHTML = cards.map((card) => `
		<div class="mm-card">
			<span class="mm-card-label">${escapeHtml(card.label)}</span>
			<div class="mm-card-value">${escapeHtml(card.value)}</div>
			${card.note ? `<div class="mm-card-note">${escapeHtml(card.note)}</div>` : ''}
		</div>
	`).join('');
}

function renderStorageRows(rows) {
	if (!rows.length) {
		storageBoard.innerHTML = `<div class="mm-muted">${escapeHtml(t("No submitted Mold Storage Location records were found yet. Submit the storage slot masters first and they will appear here automatically."))}</div>`;
		return;
	}

	let html = `
		<div class="mm-table-shell">
			<table class="mm-table">
				<thead>
					<tr>
						<th>${escapeHtml(t("Storage Slot"))}</th>
						<th>${escapeHtml(t("Current Mold"))}</th>
						<th>${escapeHtml(t("Status"))}</th>
						<th>${escapeHtml(t("Current Holder / Destination"))}</th>
						<th>${escapeHtml(t("Last Activity"))}</th>
					</tr>
				</thead>
				<tbody>
	`;

	rows.forEach((row) => {
		const rowClass = row.current_mold ? 'is-current' : '';
		const lastActivity = row.last_activity_on ? frappe.datetime.str_to_user(row.last_activity_on) : '-';
		const moldCell = row.current_mold
			? `${docLink('Mold', row.current_mold)}<div class="mm-muted">${escapeHtml(row.mold_name || '')} ${row.current_version ? `| ${escapeHtml(row.current_version)}` : ''}</div>`
			: `<span class="mm-muted">${escapeHtml(t("Available"))}</span>`;

		html += `
			<tr class="${rowClass}">
				<td>
					<div><strong>${docLink('Mold Storage Location', row.storage_code)}</strong></div>
					<div class="mm-muted">${escapeHtml([row.warehouse, row.location, row.storage_bin].filter(Boolean).join(' / ') || '-')}</div>
				</td>
				<td>${moldCell}</td>
				<td>${badge(row.storage_status || row.mold_status || 'Available')}</td>
				<td>${escapeHtml(row.current_holder_summary || '-')}</td>
				<td>${escapeHtml(lastActivity)}</td>
			</tr>
		`;
	});

	html += '</tbody></table></div>';
	storageBoard.innerHTML = html;
}

async function loadDashboard() {
	feedback.textContent = t('Loading dashboard...');
	try {
		const data = await frappe.xcall('mold_management.api.mold.get_workspace_dashboard_data');
		renderCards([
			{ label: t('Submitted Molds'), value: data.total_molds || 0, note: t('Main mold master records only') },
			{ label: t('Active'), value: data.status_counts?.Active || 0, note: t('Ready for internal use') },
			{ label: t('Pending Asset'), value: data.status_counts?.['Pending Asset Link'] || 0, note: t('Need create / link asset') },
			{ label: t('Issued'), value: data.status_counts?.Issued || 0, note: t('Currently outside standard location') },
			{ label: t('Outsourced'), value: data.status_counts?.Outsourced || 0, note: t('External production / modification / inspection') },
			{ label: t('Under Maintenance'), value: (data.status_counts?.['Under Maintenance'] || 0) + (data.status_counts?.['Under External Maintenance'] || 0), note: t('Internal + external maintenance') }
		], summaryGrid);

		renderCards([
			{ label: t('Company-Owned'), value: data.ownership_counts?.Company || 0, note: t('Self-owned molds') },
			{ label: t('Customer-Owned'), value: data.ownership_counts?.Customer || 0, note: t('Managed via asset flow without depreciation') },
			{ label: t('Open Outsource'), value: data.queue_counts?.open_outsource || 0, note: t('Submitted and still open') },
			{ label: t('Storage Slots'), value: data.queue_counts?.submitted_storage_slots || 0, note: t('{0} occupied / {1} available', [data.queue_counts?.occupied_storage_slots || 0, data.queue_counts?.available_storage_slots || 0]) }
		], secondaryGrid);

		renderStorageRows(data.storage_rows || []);
		feedback.textContent = t('Dashboard refreshed from submitted records.');
	} catch (error) {
		console.error(error);
		feedback.textContent = t('Failed to load mold dashboard.');
	}
}

titleNode && (titleNode.textContent = t('Mold Operations Dashboard'));
subtitleNode && (subtitleNode.textContent = t('Only submitted mold documents are counted here. Draft records stay outside the dashboard and storage board.'));
refreshButton && (refreshButton.textContent = t('Refresh'));
storageTitleNode && (storageTitleNode.textContent = t('Mold Storage Board'));
sectionNoteNode && (sectionNoteNode.textContent = t('Submitted storage slots only'));
openBoardButton && (openBoardButton.textContent = t('Open Board'));
refreshButton?.addEventListener('click', loadDashboard);
openBoardButton?.addEventListener('click', () => frappe.set_route('mold-storage-board'));
loadDashboard();
"""


def ensure_workspace_resources():
	_ensure_dashboard_custom_block()
	_ensure_workspace_dashboard_layout()


def remove_workspace_resources():
	if frappe.db.exists("Workspace", WORKSPACE_NAME):
		workspace = frappe.get_doc("Workspace", WORKSPACE_NAME)
		content = _load_workspace_content(workspace)
		content = [
			block
			for block in content
			if not (
				block.get("type") == "custom_block"
				and (block.get("data") or {}).get("custom_block_name") == DASHBOARD_BLOCK_NAME
			)
		]
		workspace.content = json.dumps(content, separators=(",", ":"))
		workspace.set(
			"custom_blocks",
			[row for row in workspace.custom_blocks if row.custom_block_name != DASHBOARD_BLOCK_NAME],
		)
		workspace.save(ignore_permissions=True)

	if frappe.db.exists("Custom HTML Block", DASHBOARD_BLOCK_NAME):
		frappe.delete_doc("Custom HTML Block", DASHBOARD_BLOCK_NAME, force=1, ignore_permissions=True)


def _ensure_dashboard_custom_block():
	exists = frappe.db.exists("Custom HTML Block", DASHBOARD_BLOCK_NAME)
	if exists:
		doc = frappe.get_doc("Custom HTML Block", DASHBOARD_BLOCK_NAME)
	else:
		doc = frappe.new_doc("Custom HTML Block")
		doc.name = DASHBOARD_BLOCK_NAME
		doc.private = 0
	doc.html = DASHBOARD_HTML
	doc.style = DASHBOARD_STYLE
	doc.script = DASHBOARD_SCRIPT
	if exists:
		doc.save(ignore_permissions=True)
	else:
		doc.insert(ignore_permissions=True)


def _ensure_workspace_dashboard_layout():
	if not frappe.db.exists("Workspace", WORKSPACE_NAME):
		return

	workspace = frappe.get_doc("Workspace", WORKSPACE_NAME)
	changed = False

	if not any(row.custom_block_name == DASHBOARD_BLOCK_NAME for row in workspace.custom_blocks):
		workspace.append(
			"custom_blocks",
			{
				"custom_block_name": DASHBOARD_BLOCK_NAME,
				"label": "Dashboard",
			},
		)
		changed = True

	content = _load_workspace_content(workspace)
	if not any(
		block.get("type") == "custom_block"
		and (block.get("data") or {}).get("custom_block_name") == DASHBOARD_BLOCK_NAME
		for block in content
	):
		insert_at = 2 if len(content) >= 2 else len(content)
		content.insert(
			insert_at,
			{
				"id": "custom-block-mold-dashboard",
				"type": "custom_block",
				"data": {
					"custom_block_name": DASHBOARD_BLOCK_NAME,
					"col": 12,
				},
			},
		)
		changed = True

	original_shortcuts = list(workspace.shortcuts)
	workspace.set("shortcuts", [row for row in workspace.shortcuts if row.link_to != "Mold Storage Board"])
	if len(workspace.shortcuts) != len(original_shortcuts):
		changed = True

	original_links = list(workspace.links)
	workspace.set(
		"links",
		[
			row
			for row in workspace.links
			if not (row.link_type == "Report" and row.link_to == "Mold Storage Board")
		],
	)
	if len(workspace.links) != len(original_links):
		changed = True

	if not any(row.link_type == "Page" and row.link_to == STORAGE_BOARD_PAGE_NAME for row in workspace.links):
		links = list(workspace.links)
		insert_at = next(
			(index for index, row in enumerate(links) if row.type == "Card Break" and row.label == "Transactions"),
			len(links),
		)
		links.insert(
			insert_at,
			frappe._dict(
				{
					"label": STORAGE_BOARD_PAGE_LABEL,
					"link_to": STORAGE_BOARD_PAGE_NAME,
					"link_type": "Page",
					"type": "Link",
				}
			),
		)
		workspace.set("links", links)
		changed = True

	for row in workspace.links:
		if row.type == "Card Break" and row.label == "Master Data" and row.link_count != 5:
			row.link_count = 5
			changed = True

	for row in workspace.shortcuts:
		if row.type != "DocType" or not row.link_to:
			continue
		if frappe.db.exists("DocType", row.link_to) and frappe.get_meta(row.link_to).issingle and row.doc_view:
			row.doc_view = ""
			changed = True

	if changed:
		workspace.content = json.dumps(content, separators=(",", ":"))
		workspace.save(ignore_permissions=True)


def _load_workspace_content(workspace) -> list[dict]:
	try:
		return json.loads(workspace.content or "[]")
	except Exception:
		return []

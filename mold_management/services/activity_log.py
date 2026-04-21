from __future__ import annotations

import frappe


def get_mold_activity_rows(mold_name: str) -> list[dict]:
	mold = frappe.get_doc("Mold", mold_name)
	asset = mold.linked_asset
	rows: list[dict] = []

	if asset:
		rows.extend(_get_asset_movement_rows(asset))
		rows.extend(_get_asset_repair_rows(asset))
		rows.extend(_get_asset_maintenance_rows(asset))
		rows.extend(_get_asset_scrap_rows(asset))

	rows.extend(_get_mold_alteration_rows(mold_name))
	rows.extend(_get_mold_outsource_rows(mold_name))
	rows.extend(_get_spare_part_usage_rows(mold_name))
	rows.extend(_get_storage_log_rows(mold_name))

	rows.sort(key=lambda row: (str(row.get("posting_time") or ""), row.get("name") or ""), reverse=True)
	return rows


def get_item_mold_rows(item_code: str) -> list[dict]:
	return frappe.db.sql(
		"""
		select
			parent as mold,
			item_code,
			item_name,
			priority,
			output_qty,
			cycle_time_seconds,
			is_default_product
		from `tabMold Product` mp
		join `tabMold` m on m.name = mp.parent
		where mp.item_code = %(item_code)s
			and m.docstatus = 1
		order by mp.priority asc, mp.parent asc
		""",
		{"item_code": item_code},
		as_dict=True,
	)


def _get_asset_movement_rows(asset_name: str) -> list[dict]:
	return frappe.db.sql(
		"""
		select
			'Asset Movement' as reference_doctype,
			asm.name,
			asm.transaction_date as posting_time,
			asm.purpose as activity_type,
			concat_ws(' / ', asm_item.target_location, asm_item.to_employee) as detail,
			asm.docstatus
		from `tabAsset Movement Item` asm_item
		join `tabAsset Movement` asm on asm.name = asm_item.parent
		where asm_item.asset = %(asset)s and asm.docstatus = 1
		order by asm.transaction_date desc, asm.modified desc
		""",
		{"asset": asset_name},
		as_dict=True,
	)


def _get_asset_repair_rows(asset_name: str) -> list[dict]:
	return frappe.db.sql(
		"""
		select
			'Asset Repair' as reference_doctype,
			name,
			modified as posting_time,
			repair_status as activity_type,
			description as detail,
			docstatus
		from `tabAsset Repair`
		where asset = %(asset)s and docstatus = 1
		order by modified desc
		""",
		{"asset": asset_name},
		as_dict=True,
	)


def _get_asset_maintenance_rows(asset_name: str) -> list[dict]:
	return frappe.db.sql(
		"""
		select
			'Asset Maintenance Log' as reference_doctype,
			aml.name,
			coalesce(aml.completion_date, aml.due_date, aml.modified) as posting_time,
			aml.maintenance_status as activity_type,
			aml.task_name as detail,
			aml.docstatus
		from `tabAsset Maintenance Log` aml
		join `tabAsset Maintenance` am on am.name = aml.asset_maintenance
		where am.asset_name = %(asset)s and aml.docstatus = 1
		order by coalesce(aml.completion_date, aml.due_date, aml.modified) desc
		""",
		{"asset": asset_name},
		as_dict=True,
	)


def _get_asset_scrap_rows(asset_name: str) -> list[dict]:
	return frappe.db.sql(
		"""
		select
			'Asset' as reference_doctype,
			name,
			modified as posting_time,
			'Scrapped' as activity_type,
			journal_entry_for_scrap as detail,
			docstatus
		from `tabAsset`
		where name = %(asset)s and ifnull(journal_entry_for_scrap, '') != ''
		""",
		{"asset": asset_name},
		as_dict=True,
	)


def _get_mold_alteration_rows(mold_name: str) -> list[dict]:
	return frappe.db.sql(
		"""
		select
			'Mold Alteration' as reference_doctype,
			name,
			alteration_date as posting_time,
			alteration_type as activity_type,
			concat_ws(' -> ', from_version, to_version) as detail,
			docstatus
		from `tabMold Alteration`
		where mold = %(mold)s and docstatus = 1
		order by alteration_date desc, modified desc
		""",
		{"mold": mold_name},
		as_dict=True,
	)


def _get_mold_outsource_rows(mold_name: str) -> list[dict]:
	return frappe.db.sql(
		"""
		select
			'Mold Outsource' as reference_doctype,
			name,
			coalesce(actual_return_date, outsource_date) as posting_time,
			outsource_type as activity_type,
			concat_ws(' / ', outsource_status, destination_name) as detail,
			docstatus
		from `tabMold Outsource`
		where mold = %(mold)s and docstatus = 1
		order by coalesce(actual_return_date, outsource_date) desc, modified desc
		""",
		{"mold": mold_name},
		as_dict=True,
	)


def _get_storage_log_rows(mold_name: str) -> list[dict]:
	if not frappe.db.exists("DocType", "Mold Storage Log"):
		return []

	return frappe.db.sql(
		"""
		select
			'Mold Storage Log' as reference_doctype,
			name,
			posting_time,
			event_type as activity_type,
			concat_ws(
				' / ',
				concat_ws(' -> ', ifnull(from_status, ''), ifnull(to_status, '')),
				concat_ws(' -> ', ifnull(from_storage_bin, ''), ifnull(to_storage_bin, ''))
			) as detail,
			docstatus
		from `tabMold Storage Log`
		where mold = %(mold)s and docstatus = 1
		order by posting_time desc, modified desc
		""",
		{"mold": mold_name},
		as_dict=True,
	)


def _get_spare_part_usage_rows(mold_name: str) -> list[dict]:
	if not frappe.db.exists("DocType", "Mold Spare Part Usage"):
		return []

	return frappe.db.sql(
		"""
		select
			'Mold Spare Part Usage' as reference_doctype,
			name,
			usage_date as posting_time,
			'Spare Part Usage' as activity_type,
			concat_ws(' / ', part_code, qty, uom) as detail,
			docstatus
		from `tabMold Spare Part Usage`
		where mold = %(mold)s and docstatus = 1
		order by usage_date desc, modified desc
		""",
		{"mold": mold_name},
		as_dict=True,
	)

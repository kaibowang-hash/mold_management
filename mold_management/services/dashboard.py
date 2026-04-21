from __future__ import annotations

from collections import OrderedDict

import frappe

from mold_management.constants import MOLD_STATUSES, MOLD_STORAGE_STATUS_AVAILABLE


def get_workspace_dashboard_data() -> dict:
	status_rows = frappe.db.sql(
		"""
		select status, count(*) as qty
		from `tabMold`
		where docstatus = 1
		group by status
		""",
		as_dict=True,
	)
	status_counts = {status: 0 for status in MOLD_STATUSES}
	for row in status_rows:
		status_counts[row.status] = row.qty

	storage_rows = get_storage_board_rows(limit=18)
	occupied_count = sum(1 for row in storage_rows if row.get("current_mold"))
	available_count = sum(1 for row in storage_rows if row.get("storage_status") == MOLD_STORAGE_STATUS_AVAILABLE)

	return {
		"total_molds": sum(status_counts.values()),
		"status_counts": status_counts,
		"ownership_counts": _get_ownership_counts(),
		"queue_counts": {
			"open_outsource": frappe.db.count("Mold Outsource", {"docstatus": 1, "outsource_status": "Open"}),
			"open_alteration": frappe.db.count("Mold Alteration", {"docstatus": 1}),
			"submitted_spare_part_usage": _safe_count("Mold Spare Part Usage", {"docstatus": 1}),
			"submitted_storage_slots": _safe_count("Mold Storage Location", {"docstatus": 1}),
			"occupied_storage_slots": occupied_count,
			"available_storage_slots": available_count,
		},
		"storage_rows": storage_rows,
	}


def get_storage_board_page_data(
	*,
	warehouse: str | None = None,
	location: str | None = None,
	storage_status: str | None = None,
	current_mold: str | None = None,
) -> dict:
	rows = get_storage_board_rows(
		warehouse=warehouse,
		location=location,
		storage_status=storage_status,
		current_mold=current_mold,
	)
	groups = group_storage_board_rows(rows)

	return {
		"summary": {
			"total_slots": len(rows),
			"occupied_slots": sum(1 for row in rows if row.get("current_mold")),
			"available_slots": sum(
				1
				for row in rows
				if row.get("storage_status") == MOLD_STORAGE_STATUS_AVAILABLE and not row.get("current_mold")
			),
			"warehouse_count": len(groups),
			"location_count": sum(len(group.get("locations") or []) for group in groups),
		},
		"groups": groups,
	}


def get_storage_board_rows(
	*,
	warehouse: str | None = None,
	location: str | None = None,
	storage_status: str | None = None,
	current_mold: str | None = None,
	limit: int | None = None,
) -> list[dict]:
	conditions = ["msl.docstatus = 1"]
	values: dict[str, object] = {}

	if warehouse:
		conditions.append("msl.warehouse = %(warehouse)s")
		values["warehouse"] = warehouse

	if location:
		conditions.append("msl.location = %(location)s")
		values["location"] = location

	if storage_status:
		conditions.append("msl.storage_status = %(storage_status)s")
		values["storage_status"] = storage_status

	if current_mold:
		conditions.append("msl.current_mold = %(current_mold)s")
		values["current_mold"] = current_mold

	limit_sql = ""
	if limit:
		limit_sql = "limit %(limit)s"
		values["limit"] = int(limit)

	where_clause = " and ".join(conditions)
	return frappe.db.sql(
		f"""
		select
			msl.name as storage_code,
			msl.warehouse,
			msl.location,
			msl.storage_bin,
			msl.storage_status,
			msl.current_mold,
			msl.linked_asset,
			msl.mold_status,
			msl.last_activity_on,
			m.mold_name,
			m.current_version,
			m.current_holder_summary
		from `tabMold Storage Location` msl
		left join `tabMold` m on m.name = msl.current_mold and m.docstatus = 1
		where {where_clause}
		order by
			case when ifnull(msl.current_mold, '') = '' then 1 else 0 end asc,
			msl.warehouse asc,
			msl.location asc,
			msl.storage_bin asc
		{limit_sql}
		""",
		values,
		as_dict=True,
	)


def group_storage_board_rows(rows: list[dict]) -> list[dict]:
	grouped: "OrderedDict[str, dict]" = OrderedDict()

	for row in rows:
		warehouse = row.get("warehouse") or "Unassigned Warehouse"
		location = row.get("location") or "Unassigned Location"
		warehouse_group = grouped.setdefault(
			warehouse,
			{
				"warehouse": row.get("warehouse"),
				"warehouse_label": warehouse,
				"locations": OrderedDict(),
			},
		)
		location_group = warehouse_group["locations"].setdefault(
			location,
			{
				"location": row.get("location"),
				"location_label": location,
				"rows": [],
			},
		)
		location_group["rows"].append(row)

	return [
		{
			"warehouse": warehouse_group["warehouse"],
			"warehouse_label": warehouse_group["warehouse_label"],
			"locations": [
				{
					"location": location_group["location"],
					"location_label": location_group["location_label"],
					"row_count": len(location_group["rows"]),
					"rows": location_group["rows"],
				}
				for location_group in warehouse_group["locations"].values()
			],
		}
		for warehouse_group in grouped.values()
	]


def _get_ownership_counts() -> dict:
	rows = frappe.db.sql(
		"""
		select ownership_type, count(*) as qty
		from `tabMold`
		where docstatus = 1
		group by ownership_type
		""",
		as_dict=True,
	)
	counts = {"Company": 0, "Customer": 0}
	for row in rows:
		counts[row.ownership_type] = row.qty
	return counts


def _safe_count(doctype: str, filters: dict) -> int:
	if not frappe.db.exists("DocType", doctype):
		return 0
	return frappe.db.count(doctype, filters)

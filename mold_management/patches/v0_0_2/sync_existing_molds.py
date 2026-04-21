from __future__ import annotations

import frappe

from mold_management.services.lifecycle import sync_mold_lifecycle


def execute():
	settings = frappe.get_single("Mold Management Settings")

	for mold_name in frappe.get_all("Mold", pluck="name"):
		values = {}
		doc = frappe.get_doc("Mold", mold_name)

		if not doc.default_warehouse and settings.default_mold_warehouse:
			values["default_warehouse"] = settings.default_mold_warehouse
		if not doc.default_location and settings.default_mold_location:
			values["default_location"] = settings.default_mold_location
		if not doc.default_storage_bin and settings.default_mold_storage_bin:
			values["default_storage_bin"] = settings.default_mold_storage_bin
		if not doc.current_version:
			values["current_version"] = "A0"

		if values:
			frappe.db.set_value("Mold", mold_name, values, update_modified=False)

		sync_mold_lifecycle(mold_name)

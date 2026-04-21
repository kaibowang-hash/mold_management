import frappe
from frappe import _
from frappe.model.document import Document

from mold_management.constants import MOLD_STORAGE_STATUS_AVAILABLE
from mold_management.services.lifecycle import sync_mold_lifecycle


class MoldStorageLocation(Document):
	def validate(self):
		self._set_defaults()
		self._validate_unique_physical_slot()

	def on_submit(self):
		self._sync_matching_mold()

	def _set_defaults(self):
		if self.storage_code:
			self.storage_code = self.storage_code.strip().upper()
		if self.storage_bin:
			self.storage_bin = self.storage_bin.strip().upper()

		if not self.current_mold:
			self.linked_asset = ""
			self.mold_status = ""
			self.storage_status = MOLD_STORAGE_STATUS_AVAILABLE
		elif not self.storage_status:
			self.storage_status = self.mold_status or MOLD_STORAGE_STATUS_AVAILABLE

	def _validate_unique_physical_slot(self):
		if not self.storage_bin:
			return

		existing_name = frappe.db.sql(
			"""
			select name
			from `tabMold Storage Location`
			where ifnull(warehouse, '') = %(warehouse)s
				and ifnull(location, '') = %(location)s
				and ifnull(storage_bin, '') = %(storage_bin)s
				and docstatus < 2
				and name != %(name)s
			limit 1
			""",
			{
				"warehouse": self.warehouse or "",
				"location": self.location or "",
				"storage_bin": self.storage_bin,
				"name": self.name or "",
			},
		)
		if existing_name:
			frappe.throw(
				_(
					"Mold Storage Location {0} already uses Warehouse {1}, Location {2}, Storage Bin {3}."
				).format(
					frappe.bold(existing_name[0][0]),
					frappe.bold(self.warehouse or "-"),
					frappe.bold(self.location or "-"),
					frappe.bold(self.storage_bin),
				)
			)

	def _sync_matching_mold(self):
		mold_name = self.current_mold or frappe.db.get_value(
			"Mold",
			{
				"docstatus": 1,
				"current_warehouse": self.warehouse,
				"current_location": self.location,
				"current_storage_bin": self.storage_bin,
			},
			"name",
		)
		if mold_name:
			sync_mold_lifecycle(mold_name)

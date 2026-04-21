import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime

from mold_management.services.spare_parts import validate_spare_part_applicability


class MoldSparePartUsage(Document):
	def validate(self):
		if not self.mold or not self.spare_part:
			return
		self._sync_part_meta()
		self._set_defaults()
		validate_spare_part_applicability(self.spare_part, self.mold)

	def _sync_part_meta(self):
		part = frappe.get_doc("Mold Spare Part", self.spare_part)
		self.part_code = part.part_code
		self.part_name = part.part_name
		if not self.uom:
			self.uom = part.uom

	def _set_defaults(self):
		if not self.usage_date:
			self.usage_date = now_datetime()
		if not self.used_by:
			self.used_by = frappe.session.user

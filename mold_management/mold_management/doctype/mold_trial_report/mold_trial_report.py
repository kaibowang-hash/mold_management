import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime


class MoldTrialReport(Document):
	def validate(self):
		self._set_defaults()
		self._sync_header()
		self._validate_mold_item_link()

	def _set_defaults(self):
		if not self.trial_date:
			self.trial_date = now_datetime()

	def _sync_header(self):
		if self.mold:
			self.company = frappe.db.get_value("Mold", self.mold, "company")
		if self.item_code:
			self.item_name = frappe.db.get_value("Item", self.item_code, "item_name")

	def _validate_mold_item_link(self):
		if not self.mold or not self.item_code:
			return
		if not frappe.db.exists("Mold Product", {"parent": self.mold, "parenttype": "Mold", "item_code": self.item_code}):
			frappe.throw(_("Item {0} is not configured as a Mold Product for mold {1}.").format(self.item_code, self.mold))

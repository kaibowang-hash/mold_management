import frappe
from frappe import _
from frappe.model.document import Document

from mold_management.services.lifecycle import get_latest_submitted_version, sync_mold_lifecycle
from mold_management.services.versioning import get_next_version, normalize_version


class MoldAlteration(Document):
	def validate(self):
		self._sync_header()
		self._set_versions()

	def on_submit(self):
		frappe.db.set_value(
			"Mold",
			self.mold,
			{
				"current_version": self.to_version,
				"current_transaction_type": self.doctype,
				"current_transaction_ref": self.name,
				"last_alteration_on": self.alteration_date,
			},
			update_modified=False,
		)
		sync_mold_lifecycle(self.mold)

	def on_cancel(self):
		if frappe.db.exists(
			"Mold Alteration",
			{
				"mold": self.mold,
				"docstatus": 1,
				"alteration_date": (">", self.alteration_date),
			},
		):
			frappe.throw(_("Cancel the later mold alterations first."))

		frappe.db.set_value("Mold", self.mold, "current_version", normalize_version(self.from_version))
		sync_mold_lifecycle(self.mold)

	def _sync_header(self):
		mold = frappe.get_doc("Mold", self.mold)
		if not mold.linked_asset:
			frappe.throw(_("Create or link an Asset before creating a Mold Alteration."))
		self.linked_asset = mold.linked_asset
		self.company = mold.company
		self.from_version = normalize_version(mold.current_version)

	def _set_versions(self):
		self.from_version = normalize_version(self.from_version)
		self.to_version = get_next_version(self.from_version, self.alteration_type)

		if not self.alteration_date:
			self.alteration_date = frappe.utils.today()


@frappe.whitelist()
def get_next_version_preview(mold: str, alteration_type: str) -> dict:
	current = frappe.db.get_value("Mold", mold, "current_version") or get_latest_submitted_version(mold)
	return {
		"from_version": normalize_version(current),
		"to_version": get_next_version(current, alteration_type),
	}

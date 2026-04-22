import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.naming import getseries
from frappe.utils import getdate

from mold_management.constants import (
	LIFECYCLE_FIELDS,
	MOLD_STATUS_ACTIVE,
	MOLD_STATUS_PENDING_ASSET_LINK,
)
from mold_management.services.asset_setup import apply_mold_defaults, validate_asset_matches_mold
from mold_management.services.lifecycle import sync_mold_lifecycle
from mold_management.services.versioning import normalize_version


class Mold(Document):
	def autoname(self):
		self.name = make_mold_name()

	def validate(self):
		self._set_defaults()
		self._validate_ownership()
		self._validate_family_mold()
		self._validate_lifecycle_fields()
		self._validate_asset_link()

	def on_submit(self):
		sync_mold_lifecycle(self.name)

	def on_trash(self):
		if self.linked_asset:
			frappe.throw(_("Unlink the linked Asset before deleting this mold."))

	def _set_defaults(self):
		settings = frappe.get_single("Mold Management Settings")
		apply_mold_defaults(self, settings)
		if not self.status:
			self.status = MOLD_STATUS_PENDING_ASSET_LINK if not self.linked_asset else MOLD_STATUS_ACTIVE
		self.current_version = normalize_version(self.current_version or "A0")
		if not self.default_storage_bin and self.current_storage_bin:
			self.default_storage_bin = self.current_storage_bin

	def _validate_ownership(self):
		if self.ownership_type == "Customer" and not self.customer:
			frappe.throw(_("Customer is required when ownership type is Customer."))
		if self.ownership_type == "Company":
			self.customer = ""

	def _validate_family_mold(self):
		if self.is_family_mold and len(self.get("mold_products") or []) < 2:
			frappe.throw(_("Family Mold requires at least two Mold Product rows."))

	def _validate_lifecycle_fields(self):
		if self.is_new() or self.docstatus != 1:
			return

		previous = self.get_doc_before_save()
		if not previous:
			return

		for fieldname in LIFECYCLE_FIELDS:
			if previous.get(fieldname) != self.get(fieldname):
				frappe.throw(
					_("Lifecycle field {0} can only be updated by system actions.").format(
						frappe.bold(self.meta.get_label(fieldname))
					)
				)

	def _validate_asset_link(self):
		if not self.linked_asset:
			return

		asset = frappe.get_doc("Asset", self.linked_asset)
		validate_asset_matches_mold(self, asset)


@frappe.whitelist()
def get_overview(mold_name: str):
	doc = frappe.get_doc("Mold", mold_name)
	return {
		"name": doc.name,
		"linked_asset": doc.linked_asset,
		"status": doc.status,
		"current_version": doc.current_version,
		"current_warehouse": doc.current_warehouse,
		"current_location": doc.current_location,
		"current_storage_bin": doc.current_storage_bin,
		"current_holder_summary": doc.current_holder_summary,
	}


def get_mold_name_prefix(posting_date=None) -> str:
	date_value = getdate(posting_date or frappe.utils.today())
	return f"MDINJ-{date_value.strftime('%d%m%y')}-"


def make_mold_name(posting_date=None) -> str:
	prefix = get_mold_name_prefix(posting_date)
	return f"{prefix}{getseries(prefix, 3)}"

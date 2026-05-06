import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime

from mold_management.constants import (
	MOLD_WORKFLOW_STATUS_ACCEPTED,
	MOLD_WORKFLOW_STATUS_DRAFT,
	MOLD_WORKFLOW_STATUS_IN_PROGRESS,
	MOLD_WORKFLOW_STATUS_READY_FOR_ACCEPTANCE,
)
from mold_management.services.lifecycle import get_latest_submitted_version, sync_mold_lifecycle
from mold_management.services.versioning import get_next_version, normalize_version


class MoldAlteration(Document):
	def validate(self):
		self._sync_header()
		self._set_workflow_defaults()
		self._set_versions()
		self._validate_workflow_fields()

	def on_submit(self):
		self.db_set(
			{
				"status": MOLD_WORKFLOW_STATUS_ACCEPTED,
				"accepted_by": self.accepted_by or frappe.session.user,
				"accepted_on": self.accepted_on or now_datetime(),
			},
			update_modified=False,
		)
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

	def _set_workflow_defaults(self):
		if not self.status:
			self.status = MOLD_WORKFLOW_STATUS_DRAFT
		if self.status == MOLD_WORKFLOW_STATUS_IN_PROGRESS and not self.work_started_on:
			self.work_started_on = now_datetime()
		if self.status == MOLD_WORKFLOW_STATUS_READY_FOR_ACCEPTANCE and not self.work_completed_on:
			self.work_completed_on = now_datetime()

	def _validate_workflow_fields(self):
		if self.status in {MOLD_WORKFLOW_STATUS_READY_FOR_ACCEPTANCE, MOLD_WORKFLOW_STATUS_ACCEPTED}:
			if not self.actions_performed:
				frappe.throw(_("Actions Performed is required before acceptance."))
			if not self.work_completed_on:
				frappe.throw(_("Work Completed On is required before acceptance."))


@frappe.whitelist()
def get_next_version_preview(mold: str, alteration_type: str) -> dict:
	current = frappe.db.get_value("Mold", mold, "current_version") or get_latest_submitted_version(mold)
	return {
		"from_version": normalize_version(current),
		"to_version": get_next_version(current, alteration_type),
	}

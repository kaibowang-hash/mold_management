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
from mold_management.services.lifecycle import sync_mold_lifecycle


class MoldRepair(Document):
	def validate(self):
		self._sync_header()
		self._set_defaults()
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
		sync_mold_lifecycle(self.mold)

	def on_cancel(self):
		sync_mold_lifecycle(self.mold)

	def _sync_header(self):
		mold = frappe.get_doc("Mold", self.mold)
		if not mold.linked_asset:
			frappe.throw(_("Create or link an Asset before creating a Mold Repair."))
		self.linked_asset = mold.linked_asset
		self.company = mold.company

	def _set_defaults(self):
		if not self.status:
			self.status = MOLD_WORKFLOW_STATUS_DRAFT
		if not self.failure_date:
			self.failure_date = now_datetime()
		if not self.requested_by:
			self.requested_by = frappe.session.user
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

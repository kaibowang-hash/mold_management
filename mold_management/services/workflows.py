from __future__ import annotations

import frappe

from mold_management.constants import (
	MOLD_WORKFLOW_STATUS_ACCEPTED,
	MOLD_WORKFLOW_STATUS_CANCELLED,
	MOLD_WORKFLOW_STATUS_DRAFT,
	MOLD_WORKFLOW_STATUS_IN_PROGRESS,
	MOLD_WORKFLOW_STATUS_PENDING_WORK,
	MOLD_WORKFLOW_STATUS_READY_FOR_ACCEPTANCE,
	MOLD_WORKFLOW_STATUS_REWORK_REQUIRED,
	ROLE_MOLD_KEEPER,
	ROLE_MOLD_MANAGER,
	ROLE_MOLD_TECHNICIAN,
)


MOLD_ROLES = (ROLE_MOLD_KEEPER, ROLE_MOLD_TECHNICIAN, ROLE_MOLD_MANAGER)


def ensure_mold_workflows():
	ensure_mold_roles()
	for state, style in {
		MOLD_WORKFLOW_STATUS_DRAFT: "Danger",
		MOLD_WORKFLOW_STATUS_PENDING_WORK: "Info",
		MOLD_WORKFLOW_STATUS_IN_PROGRESS: "Info",
		MOLD_WORKFLOW_STATUS_READY_FOR_ACCEPTANCE: "Warning",
		MOLD_WORKFLOW_STATUS_REWORK_REQUIRED: "Warning",
		MOLD_WORKFLOW_STATUS_ACCEPTED: "Success",
		MOLD_WORKFLOW_STATUS_CANCELLED: "Danger",
	}.items():
		ensure_workflow_state(state, style)

	for action in (
		"Submit",
		"Start Work",
		"Send for Acceptance",
		"Request Rework",
		"Accept",
		"Cancel",
	):
		ensure_workflow_action(action)

	for doctype, workflow_name in (
		("Mold Repair", "Mold Repair Workflow"),
		("Mold Alteration", "Mold Alteration Workflow"),
	):
		ensure_workflow(
			workflow_name,
			doctype,
			"status",
			[
				(MOLD_WORKFLOW_STATUS_DRAFT, 0, ROLE_MOLD_KEEPER),
				(MOLD_WORKFLOW_STATUS_PENDING_WORK, 0, ROLE_MOLD_TECHNICIAN),
				(MOLD_WORKFLOW_STATUS_IN_PROGRESS, 0, ROLE_MOLD_TECHNICIAN),
				(MOLD_WORKFLOW_STATUS_READY_FOR_ACCEPTANCE, 0, ROLE_MOLD_KEEPER),
				(MOLD_WORKFLOW_STATUS_REWORK_REQUIRED, 0, ROLE_MOLD_TECHNICIAN),
				(MOLD_WORKFLOW_STATUS_ACCEPTED, 1, ROLE_MOLD_MANAGER),
				(MOLD_WORKFLOW_STATUS_CANCELLED, 0, ROLE_MOLD_MANAGER),
			],
			[
				(MOLD_WORKFLOW_STATUS_DRAFT, "Submit", MOLD_WORKFLOW_STATUS_PENDING_WORK, ROLE_MOLD_KEEPER),
				(MOLD_WORKFLOW_STATUS_DRAFT, "Submit", MOLD_WORKFLOW_STATUS_PENDING_WORK, ROLE_MOLD_MANAGER),
				(MOLD_WORKFLOW_STATUS_PENDING_WORK, "Start Work", MOLD_WORKFLOW_STATUS_IN_PROGRESS, ROLE_MOLD_TECHNICIAN),
				(MOLD_WORKFLOW_STATUS_PENDING_WORK, "Start Work", MOLD_WORKFLOW_STATUS_IN_PROGRESS, ROLE_MOLD_MANAGER),
				(MOLD_WORKFLOW_STATUS_REWORK_REQUIRED, "Start Work", MOLD_WORKFLOW_STATUS_IN_PROGRESS, ROLE_MOLD_TECHNICIAN),
				(MOLD_WORKFLOW_STATUS_REWORK_REQUIRED, "Start Work", MOLD_WORKFLOW_STATUS_IN_PROGRESS, ROLE_MOLD_MANAGER),
				(
					MOLD_WORKFLOW_STATUS_IN_PROGRESS,
					"Send for Acceptance",
					MOLD_WORKFLOW_STATUS_READY_FOR_ACCEPTANCE,
					ROLE_MOLD_TECHNICIAN,
				),
				(
					MOLD_WORKFLOW_STATUS_IN_PROGRESS,
					"Send for Acceptance",
					MOLD_WORKFLOW_STATUS_READY_FOR_ACCEPTANCE,
					ROLE_MOLD_MANAGER,
				),
				(
					MOLD_WORKFLOW_STATUS_READY_FOR_ACCEPTANCE,
					"Request Rework",
					MOLD_WORKFLOW_STATUS_REWORK_REQUIRED,
					ROLE_MOLD_KEEPER,
				),
				(
					MOLD_WORKFLOW_STATUS_READY_FOR_ACCEPTANCE,
					"Request Rework",
					MOLD_WORKFLOW_STATUS_REWORK_REQUIRED,
					ROLE_MOLD_MANAGER,
				),
				(MOLD_WORKFLOW_STATUS_READY_FOR_ACCEPTANCE, "Accept", MOLD_WORKFLOW_STATUS_ACCEPTED, ROLE_MOLD_KEEPER),
				(MOLD_WORKFLOW_STATUS_READY_FOR_ACCEPTANCE, "Accept", MOLD_WORKFLOW_STATUS_ACCEPTED, ROLE_MOLD_MANAGER),
				(MOLD_WORKFLOW_STATUS_DRAFT, "Cancel", MOLD_WORKFLOW_STATUS_CANCELLED, ROLE_MOLD_MANAGER),
				(MOLD_WORKFLOW_STATUS_PENDING_WORK, "Cancel", MOLD_WORKFLOW_STATUS_CANCELLED, ROLE_MOLD_MANAGER),
				(MOLD_WORKFLOW_STATUS_IN_PROGRESS, "Cancel", MOLD_WORKFLOW_STATUS_CANCELLED, ROLE_MOLD_MANAGER),
				(MOLD_WORKFLOW_STATUS_READY_FOR_ACCEPTANCE, "Cancel", MOLD_WORKFLOW_STATUS_CANCELLED, ROLE_MOLD_MANAGER),
				(MOLD_WORKFLOW_STATUS_REWORK_REQUIRED, "Cancel", MOLD_WORKFLOW_STATUS_CANCELLED, ROLE_MOLD_MANAGER),
			],
		)


def ensure_mold_roles():
	for role in MOLD_ROLES:
		if frappe.db.exists("Role", role):
			continue
		frappe.get_doc({"doctype": "Role", "role_name": role, "desk_access": 1}).insert(ignore_permissions=True)


def ensure_workflow_state(state: str, style: str):
	if frappe.db.exists("Workflow State", state):
		return
	frappe.get_doc({"doctype": "Workflow State", "workflow_state_name": state, "style": style}).insert(
		ignore_permissions=True
	)


def ensure_workflow_action(action: str):
	if frappe.db.exists("Workflow Action Master", action):
		return
	frappe.get_doc({"doctype": "Workflow Action Master", "workflow_action_name": action}).insert(
		ignore_permissions=True
	)


def ensure_workflow(name: str, document_type: str, state_field: str, states: list[tuple], transitions: list[tuple]):
	if not frappe.db.exists("DocType", document_type):
		return
	doc = frappe.get_doc("Workflow", name) if frappe.db.exists("Workflow", name) else frappe.new_doc("Workflow")
	doc.workflow_name = name
	doc.document_type = document_type
	doc.is_active = 1
	doc.override_status = 0
	doc.send_email_alert = 0
	doc.workflow_state_field = state_field
	doc.set("states", [])
	for state, doc_status, allow_edit in states:
		row = doc.append("states", {})
		row.state = state
		row.doc_status = str(doc_status)
		row.allow_edit = allow_edit
		row.send_email = 0
	doc.set("transitions", [])
	for state, action, next_state, allowed in transitions:
		row = doc.append("transitions", {})
		row.state = state
		row.action = action
		row.next_state = next_state
		row.allowed = allowed
		row.allow_self_approval = 1
		row.send_email_to_creator = 0
	if doc.is_new():
		doc.insert(ignore_permissions=True)
	else:
		doc.save(ignore_permissions=True)

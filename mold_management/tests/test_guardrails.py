import unittest
from types import SimpleNamespace
from unittest.mock import patch

from mold_management.services.guardrails import (
	RESOLUTION_CREATE_RECEIPT,
	RESOLUTION_OPEN_RELATED,
	get_action_guardrail,
)


class TestGuardrails(unittest.TestCase):
	@patch("mold_management.services.guardrails._get_open_internal_work", return_value=None)
	@patch("mold_management.services.guardrails._get_open_issue_context", return_value={"name": "AM-0001"})
	@patch("mold_management.services.guardrails._get_open_outsource_doc", return_value=None)
	@patch("mold_management.services.guardrails._", side_effect=lambda value, *args, **kwargs: value)
	@patch("mold_management.services.guardrails.frappe")
	def test_outsource_is_blocked_when_mold_is_issued(
		self,
		mocked_frappe,
		_mock_translate,
		_mock_open_outsource,
		_mock_open_issue,
		_mock_open_internal,
	):
		mold = SimpleNamespace(
			name="MDINJ-220426-001",
			linked_asset="AST-0001",
			status="Issued",
			current_holder_summary="Issued to EMP-0001 / Alice",
		)
		asset = SimpleNamespace(name="AST-0001", custodian="EMP-0001", docstatus=1)
		mocked_frappe.get_doc.side_effect = lambda doctype, name: mold if doctype == "Mold" else asset

		result = get_action_guardrail("MDINJ-220426-001", "Outsource")

		self.assertFalse(result["allowed"])
		self.assertEqual(result["resolution_action"], RESOLUTION_CREATE_RECEIPT)
		self.assertEqual(result["reference_doctype"], "Asset Movement")
		self.assertEqual(result["reference_name"], "AM-0001")

	@patch("mold_management.services.guardrails._get_open_internal_work", return_value=None)
	@patch("mold_management.services.guardrails._get_open_issue_context", return_value=None)
	@patch("mold_management.services.guardrails._get_open_outsource_doc", return_value=None)
	@patch("mold_management.services.guardrails._", side_effect=lambda value, *args, **kwargs: value)
	@patch("mold_management.services.guardrails.frappe")
	def test_pending_asset_link_blocks_lifecycle_actions(
		self,
		mocked_frappe,
		_mock_translate,
		_mock_open_outsource,
		_mock_open_issue,
		_mock_open_internal,
	):
		mold = SimpleNamespace(
			name="MDINJ-220426-002",
			linked_asset="",
			status="Pending Asset Link",
			current_holder_summary="",
		)
		mocked_frappe.get_doc.return_value = mold

		result = get_action_guardrail("MDINJ-220426-002", "Transfer")

		self.assertFalse(result["allowed"])
		self.assertEqual(result["code"], "asset_required")

	@patch("mold_management.services.guardrails._", side_effect=lambda value, *args, **kwargs: value)
	@patch("mold_management.services.guardrails.frappe")
	def test_draft_asset_blocks_lifecycle_actions_until_submission(
		self,
		mocked_frappe,
		_mock_translate,
	):
		mold = SimpleNamespace(
			name="MDINJ-220426-003",
			linked_asset="AST-0002",
			status="Pending Asset Link",
			current_holder_summary="",
		)
		asset = SimpleNamespace(name="AST-0002", docstatus=0)
		mocked_frappe.get_doc.side_effect = lambda doctype, name: mold if doctype == "Mold" else asset

		result = get_action_guardrail("MDINJ-220426-003", "Transfer")

		self.assertFalse(result["allowed"])
		self.assertEqual(result["code"], "asset_submit_required")
		self.assertEqual(result["reference_doctype"], "Asset")
		self.assertEqual(result["reference_name"], "AST-0002")
		self.assertEqual(result["resolution_action"], RESOLUTION_OPEN_RELATED)

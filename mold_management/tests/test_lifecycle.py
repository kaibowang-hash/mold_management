import unittest
from types import SimpleNamespace
from unittest.mock import patch

from mold_management.services.lifecycle import _get_current_version, sanitize_lifecycle_values, sync_mold_lifecycle


class TestLifecycle(unittest.TestCase):
	def test_datetime_fields_are_coerced_to_none(self):
		values = {
			"status": "Active",
			"last_transfer_on": "",
			"last_issue_on": None,
			"last_alteration_on": "",
			"current_transaction_type": "",
		}

		cleaned = sanitize_lifecycle_values(values)

		self.assertEqual(cleaned["status"], "Active")
		self.assertIsNone(cleaned["last_transfer_on"])
		self.assertIsNone(cleaned["last_issue_on"])
		self.assertIsNone(cleaned["last_alteration_on"])
		self.assertEqual(cleaned["current_transaction_type"], "")

	@patch("mold_management.services.lifecycle.get_latest_submitted_version", return_value="B0")
	def test_current_version_prefers_latest_submitted_alteration(self, _mocked_latest_version):
		mold = SimpleNamespace(name="MOLD-001", current_version="A3")

		self.assertEqual(_get_current_version(mold), "B0")

	@patch("mold_management.services.lifecycle.get_latest_submitted_version", return_value="A0")
	def test_current_version_preserves_higher_master_value_for_legacy_data(self, _mocked_latest_version):
		mold = SimpleNamespace(name="MOLD-002", current_version="C2")

		self.assertEqual(_get_current_version(mold), "C2")

	@patch("mold_management.services.lifecycle.sync_mold_storage_location")
	@patch("mold_management.services.lifecycle._get_current_holder_summary", return_value="")
	@patch("mold_management.services.lifecycle._get_recent_activity_dates", return_value={})
	@patch("mold_management.services.lifecycle._get_current_transaction_fields", return_value={})
	@patch("mold_management.services.lifecycle._get_current_version", return_value="A0")
	@patch("mold_management.services.lifecycle.frappe")
	def test_sync_mold_lifecycle_keeps_pending_for_draft_asset(
		self,
		mocked_frappe,
		_mock_current_version,
		_mock_current_transaction,
		_mock_recent_activity,
		_mock_holder_summary,
		_mock_sync_storage,
	):
		mold = SimpleNamespace(
			name="MOLD-003",
			linked_asset="AST-0003",
			default_warehouse="WH-A",
			default_location="LOC-A",
			default_storage_bin="BIN-A",
			current_version="A0",
		)
		asset = SimpleNamespace(name="AST-0003", docstatus=0)
		mocked_frappe.get_doc.side_effect = lambda doctype, name: mold if doctype == "Mold" else asset

		sync_mold_lifecycle("MOLD-003")

		values = mocked_frappe.db.set_value.call_args.args[2]
		self.assertEqual(values["status"], "Pending Asset Link")
		self.assertEqual(values["linked_asset"], "AST-0003")
		self.assertEqual(values["current_location"], "LOC-A")
		self.assertEqual(values["current_warehouse"], "WH-A")
		self.assertEqual(values["current_storage_bin"], "BIN-A")

	@patch("mold_management.services.lifecycle.sync_mold_storage_location")
	@patch("mold_management.services.lifecycle._get_current_holder_summary", return_value="")
	@patch("mold_management.services.lifecycle._get_current_storage_bin", return_value="")
	@patch("mold_management.services.lifecycle._get_current_warehouse", return_value="")
	@patch("mold_management.services.lifecycle._has_open_maintenance", return_value=False)
	@patch("mold_management.services.lifecycle._has_pending_repair", return_value=False)
	@patch("mold_management.services.lifecycle._has_open_outsource", return_value=False)
	@patch("mold_management.services.lifecycle._get_recent_activity_dates", return_value={})
	@patch("mold_management.services.lifecycle._get_current_transaction_fields", return_value={})
	@patch("mold_management.services.lifecycle._get_current_version", return_value="A0")
	@patch("mold_management.services.lifecycle.frappe")
	def test_sync_mold_lifecycle_activates_after_asset_submission(
		self,
		mocked_frappe,
		_mock_current_version,
		_mock_current_transaction,
		_mock_recent_activity,
		_mock_open_outsource,
		_mock_pending_repair,
		_mock_open_maintenance,
		_mock_current_warehouse,
		_mock_current_storage_bin,
		_mock_holder_summary,
		_mock_sync_storage,
	):
		mold = SimpleNamespace(
			name="MOLD-004",
			linked_asset="AST-0004",
			default_warehouse="WH-A",
			default_location="LOC-A",
			default_storage_bin="BIN-A",
			current_version="A0",
		)
		asset = SimpleNamespace(
			name="AST-0004",
			docstatus=1,
			location="LOC-B",
			custodian=None,
			journal_entry_for_scrap=None,
		)
		mocked_frappe.get_doc.side_effect = lambda doctype, name: mold if doctype == "Mold" else asset

		sync_mold_lifecycle("MOLD-004")

		values = mocked_frappe.db.set_value.call_args.args[2]
		self.assertEqual(values["status"], "Active")
		self.assertEqual(values["linked_asset"], "AST-0004")
		self.assertEqual(values["current_location"], "LOC-B")

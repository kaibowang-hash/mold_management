import unittest
from types import SimpleNamespace
from unittest.mock import patch

from mold_management.services.lifecycle import _get_current_version, sanitize_lifecycle_values


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

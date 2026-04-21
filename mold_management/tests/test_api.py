import unittest
from types import SimpleNamespace
from unittest.mock import patch

from mold_management.api.mold import get_mold_by_barcode


class TestMoldAPI(unittest.TestCase):
	@patch("mold_management.api.mold.frappe")
	def test_get_mold_by_barcode_returns_summary(self, mocked_frappe):
		mocked_frappe.db.exists.return_value = True
		mocked_frappe.get_doc.return_value = SimpleNamespace(
			name="MDINJ-210426-001",
			mold_name="Front Bezel Mold",
			status="Active",
			linked_asset="AST-0001",
			current_version="A3",
		)

		result = get_mold_by_barcode.__wrapped__("MDINJ-210426-001")

		self.assertEqual(result["name"], "MDINJ-210426-001")
		self.assertEqual(result["mold_name"], "Front Bezel Mold")
		self.assertEqual(result["status"], "Active")
		self.assertEqual(result["linked_asset"], "AST-0001")
		self.assertEqual(result["current_version"], "A3")
		mocked_frappe.db.exists.assert_called_once_with("Mold", "MDINJ-210426-001")
		mocked_frappe.get_doc.assert_called_once_with("Mold", "MDINJ-210426-001")

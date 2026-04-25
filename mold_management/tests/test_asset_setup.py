import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from mold_management.services.asset_setup import (
	_allows_zero_value_asset,
	_create_asset_for_mold,
	_get_purchase_amount,
	apply_mold_defaults,
	get_required_asset_item,
)


class TestAssetSetup(unittest.TestCase):
	def test_company_owned_molds_use_company_asset_item(self):
		mold = SimpleNamespace(ownership_type="Company")
		settings = SimpleNamespace(mold_asset_item="ITEM-COMP", customer_mold_asset_item="ITEM-CUST")

		self.assertEqual(get_required_asset_item(mold, settings), "ITEM-COMP")

	def test_customer_owned_molds_use_customer_asset_item(self):
		mold = SimpleNamespace(ownership_type="Customer")
		settings = SimpleNamespace(mold_asset_item="ITEM-COMP", customer_mold_asset_item="ITEM-CUST")

		self.assertEqual(get_required_asset_item(mold, settings), "ITEM-CUST")

	def test_company_owned_mold_uses_asset_value_as_purchase_amount(self):
		mold = SimpleNamespace(ownership_type="Company", asset_value=12800)

		self.assertEqual(_get_purchase_amount(mold), 12800)

	def test_customer_owned_mold_allows_zero_value_for_customer_asset_item(self):
		mold = SimpleNamespace(ownership_type="Customer")
		settings = SimpleNamespace(mold_asset_item="ITEM-COMP", customer_mold_asset_item="ITEM-CUST")

		self.assertTrue(_allows_zero_value_asset(mold, settings))

	@patch("mold_management.services.asset_setup.frappe")
	def test_apply_mold_defaults_keeps_status_pending_for_draft_asset(self, mocked_frappe):
		mold = SimpleNamespace(
			linked_asset="AST-0001",
			status="Active",
			default_warehouse="",
			default_location="",
			default_storage_bin="",
		)
		settings = SimpleNamespace(
			default_mold_warehouse="WH-A",
			default_mold_location="LOC-A",
			default_mold_storage_bin="BIN-A",
		)
		mocked_frappe.db.get_value.return_value = 0

		apply_mold_defaults(mold, settings)

		self.assertEqual(mold.status, "Pending Asset Link")
		self.assertEqual(mold.default_warehouse, "WH-A")
		self.assertEqual(mold.default_location, "LOC-A")
		self.assertEqual(mold.default_storage_bin, "BIN-A")

	@patch("mold_management.services.asset_setup._", side_effect=lambda value, *args, **kwargs: value)
	@patch("mold_management.services.asset_setup.frappe")
	def test_create_asset_for_mold_keeps_new_asset_as_draft(self, mocked_frappe, _mock_translate):
		mold = SimpleNamespace(
			name="MOLD-001",
			mold_name="Front Bezel Mold",
			linked_asset="",
			company="JCE",
			available_for_use_date="2026-04-25",
			asset_value=12800,
			ownership_type="Company",
			customer=None,
			default_location="LOC-A",
			default_warehouse="WH-A",
			default_storage_bin="BIN-A",
		)
		settings = SimpleNamespace(
			mold_asset_item="ITEM-COMP",
			customer_mold_asset_item="ITEM-CUST",
			own_asset_category="CAT-COMP",
			customer_asset_category="CAT-CUST",
			default_mold_location="LOC-A",
			default_mold_warehouse="WH-A",
			default_mold_storage_bin="BIN-A",
		)
		asset = MagicMock()
		asset.name = "AST-0001"
		mocked_frappe.get_doc.return_value = asset
		mocked_frappe.db.get_value.return_value = None

		result = _create_asset_for_mold(mold, settings)

		asset.insert.assert_called_once_with(ignore_permissions=True)
		asset.submit.assert_not_called()
		mocked_frappe.db.set_value.assert_called_once_with(
			"Mold",
			"MOLD-001",
			{"linked_asset": "AST-0001"},
			update_modified=False,
		)
		self.assertEqual(result, {"doctype": "Asset", "name": "AST-0001"})

	@patch("mold_management.services.asset_setup.frappe")
	def test_create_asset_for_mold_reuses_existing_asset_link(self, mocked_frappe):
		mold = SimpleNamespace(name="MOLD-001", linked_asset="")
		settings = SimpleNamespace()
		mocked_frappe.db.get_value.return_value = "AST-LEGACY"

		result = _create_asset_for_mold(mold, settings)

		mocked_frappe.get_doc.assert_not_called()
		mocked_frappe.db.set_value.assert_called_once_with(
			"Mold",
			"MOLD-001",
			{"linked_asset": "AST-LEGACY"},
			update_modified=False,
		)
		self.assertEqual(result, {"doctype": "Asset", "name": "AST-LEGACY"})

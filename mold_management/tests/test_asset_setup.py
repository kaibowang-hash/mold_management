import unittest
from types import SimpleNamespace

from mold_management.services.asset_setup import (
	_allows_zero_value_asset,
	_get_purchase_amount,
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

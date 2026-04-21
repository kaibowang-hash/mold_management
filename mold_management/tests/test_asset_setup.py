import unittest
from types import SimpleNamespace

from mold_management.services.asset_setup import get_required_asset_item


class TestAssetSetup(unittest.TestCase):
	def test_company_owned_molds_use_company_asset_item(self):
		mold = SimpleNamespace(ownership_type="Company")
		settings = SimpleNamespace(mold_asset_item="ITEM-COMP", customer_mold_asset_item="ITEM-CUST")

		self.assertEqual(get_required_asset_item(mold, settings), "ITEM-COMP")

	def test_customer_owned_molds_use_customer_asset_item(self):
		mold = SimpleNamespace(ownership_type="Customer")
		settings = SimpleNamespace(mold_asset_item="ITEM-COMP", customer_mold_asset_item="ITEM-CUST")

		self.assertEqual(get_required_asset_item(mold, settings), "ITEM-CUST")

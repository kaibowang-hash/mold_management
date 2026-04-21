import unittest
from unittest.mock import patch

from mold_management.mold_management.doctype.mold.mold import get_mold_name_prefix, make_mold_name


class TestMoldNaming(unittest.TestCase):
	def test_prefix_uses_ddmmyy(self):
		self.assertEqual(get_mold_name_prefix("2026-04-21"), "MDINJ-210426-")

	@patch("mold_management.mold_management.doctype.mold.mold.getseries", return_value="001")
	def test_name_uses_daily_series(self, mocked_getseries):
		self.assertEqual(make_mold_name("2026-04-21"), "MDINJ-210426-001")
		mocked_getseries.assert_called_once_with("MDINJ-210426-", 3)

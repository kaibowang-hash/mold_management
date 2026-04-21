import unittest

from mold_management.setup.resources import STANDARD_CUSTOM_FIELDS, get_standard_custom_field_names


class TestResources(unittest.TestCase):
	def test_standard_custom_fields_use_owned_prefix(self):
		for fields in STANDARD_CUSTOM_FIELDS.values():
			for field in fields:
				self.assertTrue(field["fieldname"].startswith("custom_mold_management_"))

	def test_standard_custom_field_names_are_deterministic(self):
		names = get_standard_custom_field_names()
		self.assertIn("Asset-custom_mold_management_mold", names)
		self.assertIn("Asset Movement Item-custom_mold_management_target_warehouse", names)

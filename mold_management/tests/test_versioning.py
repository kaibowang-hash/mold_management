import unittest

from mold_management.constants import ALTERATION_MAJOR, ALTERATION_MINOR
from mold_management.services.versioning import get_next_version, normalize_version, version_sort_key


class TestVersioning(unittest.TestCase):
	def test_normalize_defaults(self):
		self.assertEqual(normalize_version(None), "A0")
		self.assertEqual(normalize_version("b3"), "B3")

	def test_minor_version_increments_number(self):
		self.assertEqual(get_next_version("A0", ALTERATION_MINOR), "A1")
		self.assertEqual(get_next_version("C9", ALTERATION_MINOR), "C10")

	def test_major_version_increments_letter_and_resets_minor(self):
		self.assertEqual(get_next_version("A7", ALTERATION_MAJOR), "B0")
		self.assertEqual(get_next_version("D0", ALTERATION_MAJOR), "E0")

	def test_version_sort_key_orders_versions(self):
		versions = ["B0", "A9", "A10", "A2"]
		self.assertEqual(sorted(versions, key=version_sort_key), ["A2", "A9", "A10", "B0"])

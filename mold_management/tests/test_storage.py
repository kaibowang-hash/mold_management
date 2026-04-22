import unittest

from mold_management.services.storage import _build_storage_code


class TestStorage(unittest.TestCase):
	def test_build_storage_code_includes_slot_coordinates(self):
		code = _build_storage_code("WH-A", "LOC-1", "BIN-01")

		self.assertEqual(code, "WH-A :: LOC-1 :: BIN-01")

	def test_build_storage_code_handles_empty_location(self):
		code = _build_storage_code("WH-A", "", "BIN-01")

		self.assertEqual(code, "WH-A :: NO-LOCATION :: BIN-01")

import unittest

from mold_management.services.dashboard import group_storage_board_rows


class TestDashboard(unittest.TestCase):
	def test_group_storage_board_rows_groups_by_warehouse_and_location(self):
		rows = [
			{
				"warehouse": "WH-A",
				"location": "LOC-1",
				"storage_bin": "BIN-01",
				"current_mold": "MOLD-001",
			},
			{
				"warehouse": "WH-A",
				"location": "LOC-1",
				"storage_bin": "BIN-02",
				"current_mold": "",
			},
			{
				"warehouse": "WH-A",
				"location": "LOC-2",
				"storage_bin": "BIN-03",
				"current_mold": "MOLD-002",
			},
			{
				"warehouse": "WH-B",
				"location": "",
				"storage_bin": "BIN-10",
				"current_mold": "",
			},
		]

		grouped = group_storage_board_rows(rows)

		self.assertEqual(len(grouped), 2)
		self.assertEqual(grouped[0]["warehouse_label"], "WH-A")
		self.assertEqual(len(grouped[0]["locations"]), 2)
		self.assertEqual(grouped[0]["locations"][0]["location_label"], "LOC-1")
		self.assertEqual(grouped[0]["locations"][0]["row_count"], 2)
		self.assertEqual(grouped[1]["locations"][0]["location_label"], "Unassigned Location")


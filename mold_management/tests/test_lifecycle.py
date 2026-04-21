import unittest

from mold_management.services.lifecycle import sanitize_lifecycle_values


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

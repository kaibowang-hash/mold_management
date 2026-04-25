import unittest
from types import SimpleNamespace
from unittest.mock import patch

from mold_management.mold_management.doctype.mold.mold import (
	normalize_mold_product_rows,
	validate_mold_product_configuration,
	validate_schedulable_product_item_groups,
)


def raise_value_error(message):
	raise ValueError(message)


class TestMoldOutputRules(unittest.TestCase):
	def setUp(self):
		self.translate_patcher = patch(
			"mold_management.mold_management.doctype.mold.mold._",
			side_effect=lambda value, *args, **kwargs: value,
		)
		self.translate_patcher.start()

	def tearDown(self):
		self.translate_patcher.stop()

	def test_non_family_normalization_syncs_output_qty_and_defaults_cavity_output(self):
		row = SimpleNamespace(output_qty=None, cavity_output_qty=None)

		normalize_mold_product_rows([row], is_family_mold=False, cavity_count=4)

		self.assertEqual(row.output_qty, 4)
		self.assertEqual(row.cavity_output_qty, 1)

	def test_family_normalization_only_defaults_cavity_output(self):
		rows = [
			SimpleNamespace(output_qty=2, cavity_output_qty=None),
			SimpleNamespace(output_qty=2, cavity_output_qty=3),
		]

		normalize_mold_product_rows(rows, is_family_mold=True, cavity_count=4)

		self.assertEqual(rows[0].output_qty, 2)
		self.assertEqual(rows[0].cavity_output_qty, 1)
		self.assertEqual(rows[1].cavity_output_qty, 3)

	def test_non_family_requires_exactly_one_product_row(self):
		with self.assertRaisesRegex(ValueError, "Non-family molds require exactly one Mold Product row."):
			validate_mold_product_configuration(
				cavity_count=4,
				is_family_mold=False,
				mold_products=[],
				throw=raise_value_error,
			)

	def test_cavity_count_must_be_positive(self):
		with self.assertRaisesRegex(ValueError, "Cavity Count must be greater than zero."):
			validate_mold_product_configuration(
				cavity_count=0,
				is_family_mold=False,
				mold_products=[SimpleNamespace(output_qty=1, cavity_output_qty=1)],
				throw=raise_value_error,
			)

	def test_family_requires_two_rows(self):
		with self.assertRaisesRegex(ValueError, "Family Mold requires at least two Mold Product rows."):
			validate_mold_product_configuration(
				cavity_count=4,
				is_family_mold=True,
				mold_products=[SimpleNamespace(output_qty=4, cavity_output_qty=1)],
				throw=raise_value_error,
			)

	def test_family_requires_output_qty_on_each_row(self):
		with self.assertRaisesRegex(
			ValueError,
			"Output Qty is required for each Mold Product row when Family Mold is enabled.",
		):
			validate_mold_product_configuration(
				cavity_count=4,
				is_family_mold=True,
				mold_products=[
					SimpleNamespace(output_qty=2, cavity_output_qty=1),
					SimpleNamespace(output_qty=None, cavity_output_qty=1),
				],
				throw=raise_value_error,
			)

	def test_family_sum_of_output_qty_must_match_cavity_count(self):
		with self.assertRaisesRegex(ValueError, "Sum of Output Qty must equal Cavity Count for Family Mold."):
			validate_mold_product_configuration(
				cavity_count=4,
				is_family_mold=True,
				mold_products=[
					SimpleNamespace(output_qty=1, cavity_output_qty=1),
					SimpleNamespace(output_qty=2, cavity_output_qty=1),
				],
				throw=raise_value_error,
			)

	def test_cavity_output_qty_must_be_positive(self):
		with self.assertRaisesRegex(ValueError, "Cavity Output Qty must be greater than zero."):
			validate_mold_product_configuration(
				cavity_count=4,
				is_family_mold=False,
				mold_products=[SimpleNamespace(output_qty=4, cavity_output_qty=0)],
				throw=raise_value_error,
			)

	def test_valid_family_configuration_passes(self):
		validate_mold_product_configuration(
			cavity_count=4,
			is_family_mold=True,
			mold_products=[
				SimpleNamespace(output_qty=1, cavity_output_qty=1),
				SimpleNamespace(output_qty=3, cavity_output_qty=2),
			],
			throw=raise_value_error,
		)

	def test_schedulable_product_groups_allow_aps_outputs(self):
		validate_schedulable_product_item_groups(
			[
				SimpleNamespace(idx=1, item_code="ITEM-PLASTIC"),
				SimpleNamespace(idx=2, item_code="ITEM-SUB"),
			],
			{
				"ITEM-PLASTIC": "Plastic Part",
				"ITEM-SUB": "Sub-assemblies",
			},
			throw=raise_value_error,
		)

	def test_schedulable_product_groups_reject_non_aps_outputs(self):
		with self.assertRaisesRegex(ValueError, "Only <strong>Plastic Part, Sub-assemblies</strong> can be selected"):
			validate_schedulable_product_item_groups(
				[SimpleNamespace(idx=1, item_code="ITEM-RAW")],
				{"ITEM-RAW": "Raw Material"},
				throw=raise_value_error,
			)

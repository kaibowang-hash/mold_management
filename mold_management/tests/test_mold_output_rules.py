import unittest
from types import SimpleNamespace
from unittest.mock import patch

from mold_management.mold_management.doctype.mold.mold import (
	get_food_grade_warning_rows,
	is_food_grade_warning_value,
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
		row = SimpleNamespace(output_qty=None, cavity_output_qty=None, output_group=None)

		normalize_mold_product_rows([row], is_family_mold=False, cavity_count=4)

		self.assertEqual(row.output_qty, 4)
		self.assertEqual(row.cavity_output_qty, 1)
		self.assertEqual(row.output_group, "Default")

	def test_family_normalization_only_defaults_cavity_output(self):
		rows = [
			SimpleNamespace(output_qty=2, cavity_output_qty=None, output_group=None),
			SimpleNamespace(output_qty=2, cavity_output_qty=3, output_group="A"),
		]

		normalize_mold_product_rows(rows, is_family_mold=True, cavity_count=4)

		self.assertEqual(rows[0].output_qty, 2)
		self.assertEqual(rows[0].cavity_output_qty, 1)
		self.assertEqual(rows[0].output_group, "Default")
		self.assertEqual(rows[1].cavity_output_qty, 3)

	def test_non_family_requires_at_least_one_product_row(self):
		with self.assertRaisesRegex(ValueError, "Mold requires at least one Mold Product row."):
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
				mold_products=[SimpleNamespace(output_qty=1, cavity_output_qty=1, output_group="Default")],
				throw=raise_value_error,
			)

	def test_family_requires_two_rows(self):
		with self.assertRaisesRegex(ValueError, "Family Mold output group Default requires at least two Mold Product rows."):
			validate_mold_product_configuration(
				cavity_count=4,
				is_family_mold=True,
				mold_products=[SimpleNamespace(output_qty=4, cavity_output_qty=1, output_group="Default")],
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
					SimpleNamespace(output_qty=2, cavity_output_qty=1, output_group="Default"),
					SimpleNamespace(output_qty=None, cavity_output_qty=1, output_group="Default"),
				],
				throw=raise_value_error,
			)

	def test_family_sum_of_output_qty_must_match_cavity_count(self):
		with self.assertRaisesRegex(ValueError, "Sum of Output Qty must equal Cavity Count for Family Mold output group Default."):
			validate_mold_product_configuration(
				cavity_count=4,
				is_family_mold=True,
				mold_products=[
					SimpleNamespace(output_qty=1, cavity_output_qty=1, output_group="Default"),
					SimpleNamespace(output_qty=2, cavity_output_qty=1, output_group="Default"),
				],
				throw=raise_value_error,
			)

	def test_cavity_output_qty_must_be_positive(self):
		with self.assertRaisesRegex(ValueError, "Cavity Output Qty must be greater than zero."):
			validate_mold_product_configuration(
				cavity_count=4,
				is_family_mold=False,
				mold_products=[SimpleNamespace(output_qty=4, cavity_output_qty=0, output_group="Default")],
				throw=raise_value_error,
			)

	def test_non_family_allows_multiple_alternative_output_groups(self):
		validate_mold_product_configuration(
			cavity_count=4,
			is_family_mold=False,
			mold_products=[
				SimpleNamespace(output_qty=4, cavity_output_qty=1, output_group="Black"),
				SimpleNamespace(output_qty=4, cavity_output_qty=1, output_group="White"),
			],
			throw=raise_value_error,
		)

	def test_valid_family_configuration_passes(self):
		validate_mold_product_configuration(
			cavity_count=4,
			is_family_mold=True,
			mold_products=[
				SimpleNamespace(output_qty=1, cavity_output_qty=1, output_group="Default"),
				SimpleNamespace(output_qty=3, cavity_output_qty=2, output_group="Default"),
			],
			throw=raise_value_error,
		)

	def test_valid_family_configuration_passes_per_output_group(self):
		validate_mold_product_configuration(
			cavity_count=4,
			is_family_mold=True,
			mold_products=[
				SimpleNamespace(output_qty=1, cavity_output_qty=1, output_group="Black"),
				SimpleNamespace(output_qty=3, cavity_output_qty=1, output_group="Black"),
				SimpleNamespace(output_qty=2, cavity_output_qty=1, output_group="White"),
				SimpleNamespace(output_qty=2, cavity_output_qty=1, output_group="White"),
			],
			throw=raise_value_error,
		)

	def test_food_grade_warning_ignores_empty_and_na_values(self):
		for value in ("", None, "NA", "N/A", " n/a "):
			self.assertFalse(is_food_grade_warning_value(value))
		self.assertTrue(is_food_grade_warning_value("FDA 21CFR"))

	def test_food_grade_warning_rows_expose_item_and_food_grade(self):
		rows = get_food_grade_warning_rows(
			[
				SimpleNamespace(item_code="ITEM-FDA", item_name="FDA Item", food_grade="FDA 21CFR", output_group="Blue"),
				SimpleNamespace(item_code="ITEM-NA", item_name="NA Item", food_grade="N/A", output_group="Blue"),
			]
		)

		self.assertEqual(rows, [{"item_code": "ITEM-FDA", "item_name": "FDA Item", "food_grade": "FDA 21CFR", "output_group": "Blue"}])

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

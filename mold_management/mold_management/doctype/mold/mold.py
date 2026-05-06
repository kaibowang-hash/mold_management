from math import isclose

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.naming import getseries
from frappe.utils import flt, getdate

from mold_management.constants import (
	LIFECYCLE_FIELDS,
	MOLD_STATUS_ACTIVE,
	MOLD_STATUS_PENDING_ASSET_LINK,
)
from mold_management.services.asset_setup import apply_mold_defaults, validate_asset_matches_mold
from mold_management.services.lifecycle import sync_mold_lifecycle
from mold_management.services.versioning import normalize_version

APS_ALLOWED_ITEM_GROUPS = ("Plastic Part", "Sub-assemblies")
DEFAULT_OUTPUT_GROUP = "Default"
FOOD_GRADE_EMPTY_VALUES = {"", "NA", "N/A"}


class Mold(Document):
	def autoname(self):
		self.name = make_mold_name()

	def validate(self):
		self._set_defaults()
		self._normalize_product_rows()
		self._sync_food_grade_snapshots()
		self._validate_ownership()
		self._validate_cavity_count()
		self._validate_product_rules()
		self._validate_schedulable_products()
		self._validate_lifecycle_fields()
		self._validate_asset_link()

	def on_submit(self):
		sync_mold_lifecycle(self.name)

	def on_trash(self):
		if self.linked_asset:
			frappe.throw(_("Unlink the linked Asset before deleting this mold."))

	def _set_defaults(self):
		settings = frappe.get_single("Mold Management Settings")
		apply_mold_defaults(self, settings)
		if not self.status:
			self.status = MOLD_STATUS_PENDING_ASSET_LINK if not self.linked_asset else MOLD_STATUS_ACTIVE
		self.current_version = normalize_version(self.current_version or "A0")
		if not self.default_storage_bin and self.current_storage_bin:
			self.default_storage_bin = self.current_storage_bin

	def _validate_ownership(self):
		if self.ownership_type == "Customer" and not self.customer:
			frappe.throw(_("Customer is required when ownership type is Customer."))
		if self.ownership_type == "Company":
			self.customer = ""

	def _normalize_product_rows(self):
		normalize_mold_product_rows(
			self.get("mold_products") or [],
			is_family_mold=bool(self.is_family_mold),
			cavity_count=self.cavity_count,
		)

	def _sync_food_grade_snapshots(self):
		rows = self.get("mold_products") or []
		item_codes = sorted({row.item_code for row in rows if row.item_code})
		if not item_codes or not frappe.db.exists("DocType", "Item"):
			return
		if not frappe.get_meta("Item").has_field("custom_food_grade"):
			return

		food_grade_by_item = dict(
			frappe.get_all(
				"Item",
				filters={"name": ["in", item_codes]},
				fields=["name", "custom_food_grade"],
				as_list=True,
			)
		)
		for row in rows:
			if row.item_code:
				row.food_grade = food_grade_by_item.get(row.item_code) or ""

	def _validate_cavity_count(self):
		if self.cavity_count in (None, ""):
			frappe.throw(_("Cavity Count is required."))
		if flt(self.cavity_count) <= 0:
			frappe.throw(_("Cavity Count must be greater than zero."))

	def _validate_product_rules(self):
		validate_mold_product_configuration(
			cavity_count=self.cavity_count,
			is_family_mold=bool(self.is_family_mold),
			mold_products=self.get("mold_products") or [],
		)

	def _validate_schedulable_products(self):
		rows = self.get("mold_products") or []
		item_codes = sorted({row.item_code for row in rows if row.item_code})
		if not item_codes or not frappe.db.exists("DocType", "Item"):
			return

		item_groups_by_code = {
			row.name: row.item_group
			for row in frappe.get_all(
				"Item",
				filters={"name": ["in", item_codes]},
				fields=["name", "item_group"],
			)
		}
		validate_schedulable_product_item_groups(rows, item_groups_by_code)

	def _validate_lifecycle_fields(self):
		if self.is_new() or self.docstatus != 1:
			return

		previous = self.get_doc_before_save()
		if not previous:
			return

		for fieldname in LIFECYCLE_FIELDS:
			if previous.get(fieldname) != self.get(fieldname):
				frappe.throw(
					_("Lifecycle field {0} can only be updated by system actions.").format(
						frappe.bold(self.meta.get_label(fieldname))
					)
				)

	def _validate_asset_link(self):
		if not self.linked_asset:
			return

		asset = frappe.get_doc("Asset", self.linked_asset)
		validate_asset_matches_mold(self, asset)


def validate_schedulable_product_item_groups(mold_products, item_groups_by_code: dict[str, str], throw=None):
	throw = throw or frappe.throw
	for row in mold_products or []:
		item_code = _get_row_value(row, "item_code")
		if not item_code:
			continue

		item_group = item_groups_by_code.get(item_code)
		if item_group in APS_ALLOWED_ITEM_GROUPS:
			continue

		throw(
			_(
				"Mold Product row {0} item {1} belongs to item group {2}. Only {3} can be selected for mold outputs."
			).format(
				frappe.bold(_get_row_value(row, "idx") or "?"),
				frappe.bold(item_code),
				frappe.bold(item_group or _("(blank)")),
				frappe.bold(", ".join(_(group) for group in APS_ALLOWED_ITEM_GROUPS)),
			)
		)


@frappe.whitelist()
def get_overview(mold_name: str):
	doc = frappe.get_doc("Mold", mold_name)
	return {
		"name": doc.name,
		"linked_asset": doc.linked_asset,
		"status": doc.status,
		"current_version": doc.current_version,
		"current_warehouse": doc.current_warehouse,
		"current_location": doc.current_location,
		"current_storage_bin": doc.current_storage_bin,
		"current_holder_summary": doc.current_holder_summary,
	}


def get_mold_name_prefix(posting_date=None) -> str:
	date_value = getdate(posting_date or frappe.utils.today())
	return f"MDINJ-{date_value.strftime('%d%m%y')}-"


def make_mold_name(posting_date=None) -> str:
	prefix = get_mold_name_prefix(posting_date)
	return f"{prefix}{getseries(prefix, 3)}"


def normalize_mold_product_rows(
	mold_products,
	*,
	is_family_mold: bool,
	cavity_count,
):
	rows = mold_products or []
	cavity_count_value = flt(cavity_count)

	for row in rows:
		if _get_row_value(row, "cavity_output_qty") in (None, ""):
			_set_row_value(row, "cavity_output_qty", 1)
		if not (_get_row_value(row, "output_group") or "").strip():
			_set_row_value(row, "output_group", DEFAULT_OUTPUT_GROUP)

	if not is_family_mold and cavity_count_value > 0:
		for row in rows:
			if _get_row_value(row, "output_qty") in (None, ""):
				_set_row_value(row, "output_qty", cavity_count_value)

	return rows


def validate_mold_product_configuration(
	*,
	cavity_count,
	is_family_mold: bool,
	mold_products,
	throw=None,
):
	throw = throw or frappe.throw
	rows = mold_products or []

	if cavity_count in (None, ""):
		throw(_("Cavity Count is required."))

	cavity_count_value = flt(cavity_count)
	if cavity_count_value <= 0:
		throw(_("Cavity Count must be greater than zero."))

	if is_family_mold:
		grouped_rows = _group_mold_product_rows(rows)
		if not grouped_rows:
			throw(_("Family Mold requires at least two Mold Product rows."))

		for output_group, group_rows in grouped_rows.items():
			if len(group_rows) < 2:
				throw(_("Family Mold output group {0} requires at least two Mold Product rows.").format(output_group))

			total_output = 0.0
			for row in group_rows:
				output_qty = flt(_get_row_value(row, "output_qty"))
				cavity_output_qty = flt(_get_row_value(row, "cavity_output_qty"))
				if output_qty <= 0:
					throw(_("Output Qty is required for each Mold Product row when Family Mold is enabled."))
				if cavity_output_qty <= 0:
					throw(_("Cavity Output Qty must be greater than zero."))
				total_output += output_qty

			if not isclose(total_output, cavity_count_value, rel_tol=0, abs_tol=1e-9):
				throw(_("Sum of Output Qty must equal Cavity Count for Family Mold output group {0}.").format(output_group))
		return

	if not rows:
		throw(_("Mold requires at least one Mold Product row."))

	for row in rows:
		cavity_output_qty = flt(_get_row_value(row, "cavity_output_qty"))
		if cavity_output_qty <= 0:
			throw(_("Cavity Output Qty must be greater than zero."))


def get_food_grade_warning_rows(mold_products) -> list[dict]:
	rows = []
	for row in mold_products or []:
		food_grade = _get_row_value(row, "food_grade")
		if not is_food_grade_warning_value(food_grade):
			continue
		rows.append(
			{
				"item_code": _get_row_value(row, "item_code"),
				"item_name": _get_row_value(row, "item_name"),
				"food_grade": food_grade,
				"output_group": _get_row_value(row, "output_group") or DEFAULT_OUTPUT_GROUP,
			}
		)
	return rows


def is_food_grade_warning_value(value) -> bool:
	return (str(value or "").strip().upper() not in FOOD_GRADE_EMPTY_VALUES)


def _group_mold_product_rows(rows) -> dict[str, list]:
	grouped_rows = {}
	for row in rows or []:
		output_group = (_get_row_value(row, "output_group") or DEFAULT_OUTPUT_GROUP).strip() or DEFAULT_OUTPUT_GROUP
		grouped_rows.setdefault(output_group, []).append(row)
	return grouped_rows


def _get_row_value(row, fieldname: str):
	if hasattr(row, "get"):
		return row.get(fieldname)
	return getattr(row, fieldname, None)


def _set_row_value(row, fieldname: str, value):
	if isinstance(row, dict):
		row[fieldname] = value
	else:
		setattr(row, fieldname, value)

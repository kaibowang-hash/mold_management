import frappe
from frappe import _
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

from mold_management.setup.resources import STANDARD_CUSTOM_FIELDS, get_standard_custom_field_names
from mold_management.services.workspace import ensure_workspace_resources, remove_workspace_resources


def ensure_standard_customizations():
	create_custom_fields(STANDARD_CUSTOM_FIELDS, update=True)
	frappe.clear_cache()


def ensure_single_defaults():
	settings = frappe.get_single("Mold Management Settings")
	if not settings.customer_mold_asset_item and settings.mold_asset_item:
		settings.customer_mold_asset_item = settings.mold_asset_item
	settings.flags.ignore_mandatory = True
	settings.save(ignore_permissions=True)
	ensure_workspace_resources()


def ensure_safe_to_uninstall():
	blockers = []
	for doctype in (
		"Mold",
		"Mold Alteration",
		"Mold Outsource",
		"Mold Spare Part",
		"Mold Spare Part Usage",
		"Mold Storage Location",
		"Mold Storage Log",
	):
		if frappe.db.count(doctype):
			blockers.append(doctype)

	if frappe.get_meta("Asset").has_field("custom_mold_management_mold") and frappe.db.sql(
		"""
		select name
		from `tabAsset`
		where ifnull(custom_mold_management_mold, '') != ''
		limit 1
		"""
	):
		blockers.append("Asset links")

	if blockers:
		raise frappe.ValidationError(
			_(
				"Cannot uninstall Mold Management while business data still exists: {0}"
			).format(", ".join(blockers))
		)


def remove_standard_customizations():
	for name in get_standard_custom_field_names():
		if frappe.db.exists("Custom Field", name):
			frappe.delete_doc("Custom Field", name, force=1, ignore_permissions=True)

	remove_workspace_resources()
	frappe.clear_cache()

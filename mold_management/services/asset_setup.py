from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import today

from mold_management.constants import (
	ASSET_SETUP_MODE_CREATE,
	ASSET_SETUP_MODE_LINK,
	MOLD_STATUS_ACTIVE,
	MOLD_STATUS_PENDING_ASSET_LINK,
)


def apply_mold_defaults(mold, settings=None):
	settings = settings or frappe.get_single("Mold Management Settings")

	if not mold.default_warehouse:
		mold.default_warehouse = settings.default_mold_warehouse
	if not mold.default_location:
		mold.default_location = settings.default_mold_location
	if not mold.default_storage_bin:
		mold.default_storage_bin = settings.default_mold_storage_bin

	if not mold.linked_asset:
		mold.status = MOLD_STATUS_PENDING_ASSET_LINK
	elif not mold.status or mold.status == MOLD_STATUS_PENDING_ASSET_LINK:
		mold.status = MOLD_STATUS_ACTIVE


def get_asset_setup_context(mold) -> dict:
	settings = frappe.get_single("Mold Management Settings")
	return {
		"mold_name": mold.name,
		"linked_asset": mold.linked_asset,
		"ownership_type": mold.ownership_type,
		"allowed_asset_item": get_required_asset_item(mold, settings),
		"company_asset_item": settings.mold_asset_item,
		"customer_asset_item": settings.customer_mold_asset_item,
		"asset_category": get_required_asset_category(mold, settings),
		"requires_asset_value": mold.ownership_type == "Company",
		"default_warehouse": mold.default_warehouse or settings.default_mold_warehouse,
		"default_location": mold.default_location or settings.default_mold_location,
		"default_storage_bin": mold.default_storage_bin or settings.default_mold_storage_bin,
	}


def get_required_asset_item(mold, settings=None) -> str:
	settings = settings or frappe.get_single("Mold Management Settings")
	return settings.customer_mold_asset_item if mold.ownership_type == "Customer" else settings.mold_asset_item


def get_required_asset_category(mold, settings=None) -> str:
	settings = settings or frappe.get_single("Mold Management Settings")
	return settings.customer_asset_category if mold.ownership_type == "Customer" else settings.own_asset_category


def validate_asset_matches_mold(mold, asset, settings=None):
	settings = settings or frappe.get_single("Mold Management Settings")
	required_item = get_required_asset_item(mold, settings)
	required_category = get_required_asset_category(mold, settings)

	if required_item and asset.item_code != required_item:
		frappe.throw(
			_(
				"Asset {0} uses Item {1}. Only Item {2} is allowed for mold assets."
			).format(asset.name, asset.item_code or "-", required_item)
		)

	if required_category and asset.asset_category != required_category:
		frappe.throw(
			_(
				"Asset {0} uses Asset Category {1}. Required category for this mold is {2}."
			).format(asset.name, asset.asset_category or "-", required_category)
		)

	existing_mold = asset.custom_mold_management_mold
	if existing_mold and existing_mold != mold.name:
		frappe.throw(_("Asset {0} is already linked to Mold {1}.").format(asset.name, existing_mold))

	if mold.linked_asset and mold.linked_asset != asset.name:
		frappe.throw(
			_(
				"Mold {0} is already linked to Asset {1}. Unlink it first before linking another asset."
			).format(mold.name, mold.linked_asset)
		)


def setup_asset_for_mold(mold_name: str, setup_mode: str, asset_name: str | None = None) -> dict:
	mold = frappe.get_doc("Mold", mold_name)
	settings = frappe.get_single("Mold Management Settings")
	apply_mold_defaults(mold, settings)

	if setup_mode == ASSET_SETUP_MODE_CREATE:
		return _create_asset_for_mold(mold, settings)
	if setup_mode == ASSET_SETUP_MODE_LINK:
		return _link_asset_for_mold(mold, asset_name, settings)

	frappe.throw(_("Unsupported asset setup mode: {0}").format(setup_mode))


def _create_asset_for_mold(mold, settings) -> dict:
	if mold.linked_asset:
		return {"doctype": "Asset", "name": mold.linked_asset}

	required_item = get_required_asset_item(mold, settings)
	_require_value(required_item, _("Asset Item must be configured in Mold Management Settings for this ownership type."))
	if mold.ownership_type == "Company":
		_require_value(mold.asset_value, _("Asset Value must be set on the Mold before creating an Asset."))

	asset_category = get_required_asset_category(mold, settings)
	_require_value(asset_category, _("Asset Category is missing in Mold Management Settings."))

	location = mold.default_location or settings.default_mold_location
	_require_value(location, _("Default Mold Location must be configured before creating an Asset."))

	asset = frappe.get_doc(
		{
			"doctype": "Asset",
			"asset_name": mold.mold_name,
			"item_code": required_item,
			"company": mold.company,
			"asset_category": asset_category,
			"location": location,
			"purchase_date": mold.available_for_use_date or today(),
			"available_for_use_date": mold.available_for_use_date or today(),
			"gross_purchase_amount": mold.asset_value if mold.ownership_type == "Company" else 0,
			"is_existing_asset": 1,
			"calculate_depreciation": 0,
			"asset_owner": mold.ownership_type,
			"asset_owner_company": mold.company if mold.ownership_type == "Company" else None,
			"customer": mold.customer if mold.ownership_type == "Customer" else None,
			"custom_mold_management_mold": mold.name,
		}
	)
	asset.insert(ignore_permissions=True)
	asset.submit()

	frappe.db.set_value(
		"Mold",
		mold.name,
		{
			"linked_asset": asset.name,
			"current_location": asset.location,
			"current_warehouse": mold.default_warehouse or settings.default_mold_warehouse,
			"current_storage_bin": mold.default_storage_bin or settings.default_mold_storage_bin,
		},
		update_modified=False,
	)
	return {"doctype": "Asset", "name": asset.name}


def _link_asset_for_mold(mold, asset_name: str | None, settings) -> dict:
	_require_value(asset_name, _("Asset is required when linking an existing asset."))
	asset = frappe.get_doc("Asset", asset_name)
	validate_asset_matches_mold(mold, asset, settings)

	frappe.db.set_value("Asset", asset.name, "custom_mold_management_mold", mold.name, update_modified=False)
	frappe.db.set_value("Mold", mold.name, "linked_asset", asset.name, update_modified=False)
	return {"doctype": "Asset", "name": asset.name}


def _require_value(value, message: str):
	if not value:
		frappe.throw(message)

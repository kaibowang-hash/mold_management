import frappe
from frappe.model.document import Document


class MoldManagementSettings(Document):
	def get_minor_change_roles(self) -> list[str]:
		return [role.strip() for role in (self.minor_change_roles or "").splitlines() if role.strip()]


@frappe.whitelist()
def get_settings():
	doc = frappe.get_single("Mold Management Settings")
	return {
		"mold_asset_item": doc.mold_asset_item,
		"customer_mold_asset_item": doc.customer_mold_asset_item,
		"default_mold_warehouse": doc.default_mold_warehouse,
		"default_mold_location": doc.default_mold_location,
		"default_mold_storage_bin": doc.default_mold_storage_bin,
		"own_asset_category": doc.own_asset_category,
		"customer_asset_category": doc.customer_asset_category,
		"default_maintenance_team": doc.default_maintenance_team,
		"minor_change_roles": doc.get_minor_change_roles(),
	}

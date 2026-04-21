import frappe

from mold_management.services.customizations import (
	ensure_safe_to_uninstall,
	remove_standard_customizations,
)


def before_uninstall():
	ensure_safe_to_uninstall()
	remove_standard_customizations()
	frappe.clear_cache()

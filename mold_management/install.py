import frappe

from mold_management.services.customizations import ensure_single_defaults
from mold_management.services.workspace import ensure_workspace_resources


def after_install():
	ensure_single_defaults()
	frappe.clear_cache()


def after_migrate():
	ensure_workspace_resources()
	frappe.clear_cache()

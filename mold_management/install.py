import frappe

from mold_management.services.customizations import (
	backfill_mold_product_metadata,
	ensure_single_defaults,
	ensure_standard_customizations,
)
from mold_management.services.workflows import ensure_mold_workflows
from mold_management.services.workspace import ensure_workspace_resources


def after_install():
	ensure_standard_customizations()
	ensure_mold_workflows()
	backfill_mold_product_metadata()
	ensure_single_defaults()
	frappe.clear_cache()


def after_migrate():
	ensure_standard_customizations()
	ensure_mold_workflows()
	backfill_mold_product_metadata()
	ensure_workspace_resources()
	frappe.clear_cache()

from frappe.model.document import Document

from mold_management.services.molding_conditions import (
	activate_condition_sheet,
	cancel_condition_sheet,
	set_condition_defaults,
	sync_condition_header,
	sync_mold_condition_links,
	validate_condition_sheet,
)


class InjectionMoldingConditionSheet(Document):
	def validate(self):
		set_condition_defaults(self)
		sync_condition_header(self)
		validate_condition_sheet(self)

	def on_submit(self):
		activate_condition_sheet(self)

	def on_cancel(self):
		cancel_condition_sheet(self)

	def on_update(self):
		sync_mold_condition_links(self.mold)

import frappe
from frappe import _
from frappe.model.document import Document

from mold_management.services.lifecycle import sync_mold_lifecycle


class MoldOutsource(Document):
	def validate(self):
		self._sync_header()
		self._validate_destination()
		self._validate_return_fields()

	def on_submit(self):
		self.db_set("outsource_status", "Open", update_modified=False)
		sync_mold_lifecycle(self.mold)

	def on_cancel(self):
		self.db_set("outsource_status", "Cancelled", update_modified=False)
		sync_mold_lifecycle(self.mold)

	def _sync_header(self):
		mold = frappe.get_doc("Mold", self.mold)
		self.linked_asset = mold.linked_asset
		self.company = mold.company

	def _validate_destination(self):
		if self.destination_type == "Supplier" and not self.supplier:
			frappe.throw(_("Supplier is required for supplier outsource destinations."))
		if self.destination_type == "Customer" and not self.customer:
			frappe.throw(_("Customer is required for customer outsource destinations."))
		if self.destination_type == "Other" and not self.destination_name:
			frappe.throw(_("Destination Name is required when destination type is Other."))

	def _validate_return_fields(self):
		if self.actual_return_date and not self.return_result:
			frappe.throw(_("Return Result is required when Actual Return Date is set."))


@frappe.whitelist()
def mark_returned(name: str, actual_return_date: str, return_result: str):
	doc = frappe.get_doc("Mold Outsource", name)
	if doc.docstatus != 1:
		frappe.throw(_("Only submitted outsource documents can be returned."))

	frappe.db.set_value(
		"Mold Outsource",
		doc.name,
		{
			"actual_return_date": actual_return_date,
			"return_result": return_result,
			"outsource_status": "Returned",
		},
	)
	sync_mold_lifecycle(doc.mold)
	return {"name": doc.name, "mold": doc.mold}

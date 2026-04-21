import frappe
from frappe import _
from frappe.model.document import Document


class MoldSparePart(Document):
	def validate(self):
		self._validate_rows()
		self._validate_alternative_part()

	def _validate_rows(self):
		seen = set()
		for row in self.get("applicable_molds") or []:
			if row.mold in seen:
				frappe.throw(_("Mold {0} is listed more than once in Applicable Molds.").format(row.mold))
			seen.add(row.mold)

	def _validate_alternative_part(self):
		if self.alternative_part and self.alternative_part == self.name:
			frappe.throw(_("Alternative Part cannot point to the same Mold Spare Part."))


import re

import frappe
from frappe import _

from mold_management.constants import ALTERATION_MAJOR, ALTERATION_MINOR

VERSION_RE = re.compile(r"^([A-Z])(\d+)$")


def normalize_version(version: str | None) -> str:
	if not version:
		return "A0"

	version = version.strip().upper()
	match = VERSION_RE.match(version)
	if not match:
		frappe.throw(_("Version must follow the format A0, A1, B0, etc."))
	return version


def split_version(version: str) -> tuple[str, int]:
	match = VERSION_RE.match(normalize_version(version))
	if not match:
		frappe.throw(_("Invalid mold version: {0}").format(version))
	return match.group(1), int(match.group(2))


def get_next_version(current_version: str | None, alteration_type: str) -> str:
	major, minor = split_version(current_version or "A0")

	if alteration_type == ALTERATION_MINOR:
		return f"{major}{minor + 1}"

	if alteration_type == ALTERATION_MAJOR:
		if major == "Z":
			frappe.throw(_("Major version cannot move beyond Z."))
		return f"{chr(ord(major) + 1)}0"

	frappe.throw(_("Unsupported alteration type: {0}").format(alteration_type))


def version_sort_key(version: str | None) -> tuple[int, int]:
	major, minor = split_version(version or "A0")
	return ord(major), minor

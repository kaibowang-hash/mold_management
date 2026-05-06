APP_NAME = "mold_management"
APP_TITLE = "Mold Management"
MODULE_NAME = "Mold Management"

MOLD_STATUS_PENDING_ASSET_LINK = "Pending Asset Link"
MOLD_STATUS_ACTIVE = "Active"
MOLD_STATUS_ISSUED = "Issued"
MOLD_STATUS_UNDER_MAINTENANCE = "Under Maintenance"
MOLD_STATUS_UNDER_EXTERNAL_MAINTENANCE = "Under External Maintenance"
MOLD_STATUS_OUTSOURCED = "Outsourced"
MOLD_STATUS_SCRAPPED = "Scrapped"

MOLD_STATUSES = [
	MOLD_STATUS_PENDING_ASSET_LINK,
	MOLD_STATUS_ACTIVE,
	MOLD_STATUS_ISSUED,
	MOLD_STATUS_UNDER_MAINTENANCE,
	MOLD_STATUS_UNDER_EXTERNAL_MAINTENANCE,
	MOLD_STATUS_OUTSOURCED,
	MOLD_STATUS_SCRAPPED,
]

MOLD_STORAGE_STATUS_AVAILABLE = "Available"
MOLD_STORAGE_STATUSES = [MOLD_STORAGE_STATUS_AVAILABLE, *MOLD_STATUSES]

MOLD_TYPE_OPTIONS = [
	"INJ",
	"Hot Runner",
	"Cold Runner",
	"Insert",
	"2K / Overmold",
	"Unscrewing",
	"Stack",
	"Other",
]

LIFECYCLE_FIELDS = (
	"status",
	"linked_asset",
	"current_version",
	"current_warehouse",
	"current_location",
	"current_storage_bin",
	"current_holder_summary",
	"current_transaction_type",
	"current_transaction_ref",
	"last_transfer_on",
	"last_issue_on",
	"last_receipt_on",
	"last_repair_on",
	"last_maintenance_on",
	"last_outsource_on",
	"last_alteration_on",
)

LIFECYCLE_DATETIME_FIELDS = (
	"last_transfer_on",
	"last_issue_on",
	"last_receipt_on",
	"last_repair_on",
	"last_maintenance_on",
	"last_outsource_on",
	"last_alteration_on",
)

ALTERATION_MAJOR = "Major"
ALTERATION_MINOR = "Minor"
OUTSOURCE_TYPE_EXTERNAL_MAINTENANCE = "External Maintenance"

ASSET_SETUP_MODE_CREATE = "Create New Asset"
ASSET_SETUP_MODE_LINK = "Link Existing Asset"

ROLE_MOLD_KEEPER = "Mold Keeper"
ROLE_MOLD_TECHNICIAN = "Mold Technician"
ROLE_MOLD_MANAGER = "Mold Manager"

MOLD_WORKFLOW_STATUS_DRAFT = "Draft"
MOLD_WORKFLOW_STATUS_PENDING_WORK = "Pending Work"
MOLD_WORKFLOW_STATUS_IN_PROGRESS = "In Progress"
MOLD_WORKFLOW_STATUS_READY_FOR_ACCEPTANCE = "Ready for Acceptance"
MOLD_WORKFLOW_STATUS_REWORK_REQUIRED = "Rework Required"
MOLD_WORKFLOW_STATUS_ACCEPTED = "Accepted"
MOLD_WORKFLOW_STATUS_CANCELLED = "Cancelled"

MOLD_WORKFLOW_STATUSES = [
	MOLD_WORKFLOW_STATUS_DRAFT,
	MOLD_WORKFLOW_STATUS_PENDING_WORK,
	MOLD_WORKFLOW_STATUS_IN_PROGRESS,
	MOLD_WORKFLOW_STATUS_READY_FOR_ACCEPTANCE,
	MOLD_WORKFLOW_STATUS_REWORK_REQUIRED,
	MOLD_WORKFLOW_STATUS_ACCEPTED,
	MOLD_WORKFLOW_STATUS_CANCELLED,
]

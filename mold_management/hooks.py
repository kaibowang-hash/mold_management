app_name = "mold_management"
app_title = "Mold Management"
app_publisher = "JCE"
app_description = "Mold lifecycle and tooling management for ERPNext"
app_email = "kaibo_wang@whjichen.cn"
app_license = "mit"

# Apps
# ------------------

required_apps = ["erpnext"]

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "mold_management",
# 		"logo": "/assets/mold_management/logo.png",
# 		"title": "Mold Management",
# 		"route": "/mold_management",
# 		"has_permission": "mold_management.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/mold_management/css/mold_management.css"
# app_include_js = "/assets/mold_management/js/mold_management.js"

# include js, css files in header of web template
# web_include_css = "/assets/mold_management/css/mold_management.css"
# web_include_js = "/assets/mold_management/js/mold_management.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "mold_management/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
	"Item": "public/js/item.js",
	"Asset": "public/js/asset.js",
	"Asset Movement": "public/js/asset_movement.js",
	"Asset Repair": "public/js/asset_repair.js",
	"Asset Maintenance Log": "public/js/asset_maintenance_log.js",
}
doctype_list_js = {
	"Mold": "public/js/mold_list.js",
	"Mold Storage Location": "public/js/mold_storage_location_list.js",
}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "mold_management/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "mold_management.utils.jinja_methods",
# 	"filters": "mold_management.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "mold_management.install.before_install"
after_install = "mold_management.install.after_install"
after_migrate = "mold_management.install.after_migrate"

# Uninstallation
# ------------

before_uninstall = "mold_management.uninstall.before_uninstall"
# after_uninstall = "mold_management.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "mold_management.utils.before_app_install"
# after_app_install = "mold_management.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "mold_management.utils.before_app_uninstall"
# after_app_uninstall = "mold_management.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "mold_management.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Asset": {
		"on_submit": "mold_management.services.lifecycle.handle_asset_change",
		"on_change": "mold_management.services.lifecycle.handle_asset_change",
		"on_update_after_submit": "mold_management.services.lifecycle.handle_asset_change",
	},
	"Asset Movement": {
		"on_submit": "mold_management.services.lifecycle.handle_asset_movement_change",
		"on_cancel": "mold_management.services.lifecycle.handle_asset_movement_change",
	},
	"Asset Repair": {
		"after_insert": "mold_management.services.lifecycle.handle_asset_repair_change",
		"on_update": "mold_management.services.lifecycle.handle_asset_repair_change",
		"on_submit": "mold_management.services.lifecycle.handle_asset_repair_change",
		"on_cancel": "mold_management.services.lifecycle.handle_asset_repair_change",
	},
	"Asset Maintenance Log": {
		"after_insert": "mold_management.services.lifecycle.handle_asset_maintenance_log_change",
		"on_update": "mold_management.services.lifecycle.handle_asset_maintenance_log_change",
		"on_submit": "mold_management.services.lifecycle.handle_asset_maintenance_log_change",
		"on_cancel": "mold_management.services.lifecycle.handle_asset_maintenance_log_change",
	},
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"mold_management.tasks.all"
# 	],
# 	"daily": [
# 		"mold_management.tasks.daily"
# 	],
# 	"hourly": [
# 		"mold_management.tasks.hourly"
# 	],
# 	"weekly": [
# 		"mold_management.tasks.weekly"
# 	],
# 	"monthly": [
# 		"mold_management.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "mold_management.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "mold_management.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "mold_management.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["mold_management.utils.before_request"]
# after_request = ["mold_management.utils.after_request"]

# Job Events
# ----------
# before_job = ["mold_management.utils.before_job"]
# after_job = ["mold_management.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"mold_management.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

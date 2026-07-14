from . import __version__ as app_version

app_name = "unicommerce"
app_title = "Unicommerce"
app_publisher = "Aerele"
app_description = "Standalone Unicommerce integration for ERPNext"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "developers@aerele.in"
app_license = "GNU GPL v3.0"
required_apps = ["frappe/erpnext", "ecommerce_core"]

# Includes in <head>
# ------------------

# only Unicommerce-specific client scripts; the generic ecommerce_transactions.js
# is registered by ecommerce_core.
doctype_js = {
	"Sales Order": "public/js/unicommerce/sales_order.js",
	"Sales Invoice": "public/js/unicommerce/sales_invoice.js",
	"Item": "public/js/unicommerce/item.js",
	"Stock Entry": "public/js/unicommerce/stock_entry.js",
	"Pick List": "public/js/unicommerce/pick_list.js",
}

# Installation
# ------------

after_install = "unicommerce.install.after_install"
before_uninstall = "unicommerce.uninstall.before_uninstall"

# Document Events
# ---------------
# Unicommerce-specific handlers only. Common guards (tax template / price list) live in ecommerce_core.

doc_events = {
	"Item": {
		"validate": "unicommerce.unicommerce.product.validate_item",
	},
	"Sales Order": {
		"on_update_after_submit": "unicommerce.unicommerce.order.update_shipping_info",
		"on_cancel": "unicommerce.unicommerce.status_updater.ignore_pick_list_on_sales_order_cancel",
	},
	"Stock Entry": {
		"validate": "unicommerce.unicommerce.grn.validate_stock_entry_for_grn",
		"on_submit": "unicommerce.unicommerce.grn.upload_grn",
		"on_cancel": "unicommerce.unicommerce.grn.prevent_grn_cancel",
	},
	"Pick List": {"validate": "unicommerce.unicommerce.pick_list.validate"},
	"Sales Invoice": {
		"on_submit": "unicommerce.unicommerce.invoice.on_submit",
		"on_cancel": "unicommerce.unicommerce.invoice.on_cancel",
	},
}

# Scheduled Tasks
# ---------------

scheduler_events = {
	"hourly_long": [
		"unicommerce.unicommerce.product.upload_new_items",
		"unicommerce.unicommerce.status_updater.update_sales_order_status",
		"unicommerce.unicommerce.status_updater.update_shipping_package_status",
	],
	"cron": {
		# Every five minutes
		"*/5 * * * *": [
			"unicommerce.unicommerce.order.sync_new_orders",
			"unicommerce.unicommerce.inventory.update_inventory_on_unicommerce",
			"unicommerce.unicommerce.delivery_note.prepare_delivery_note",
		],
	},
}

# Testing
# -------
# The test runner fetches `before_tests` for the app under test, so each integration
# app must declare it; the actual bootstrap lives in ecommerce_core.
before_tests = "ecommerce_core.utils.before_test.before_tests"

"""Feeds the Ecommerce Core dashboard with Unicommerce orders, payments and stock pushes.

Orders also surface the connector's platform details (channel, facility, invoice,
package, shipping, tracking) with the dashboard's provider-neutral labels — the
native Unicommerce names stay on the documents themselves — and the widget gets
a Channel filter built from the channels seen on imported orders.
"""

import frappe
from ecommerce_core.dashboard import queries
from ecommerce_core.dashboard.adapter import DashboardAdapter
from frappe import _

from unicommerce.unicommerce.constants import (
	CHANNEL_ID_FIELD,
	FACILITY_CODE_FIELD,
	INVOICE_CODE_FIELD,
	IS_COD_CHECKBOX,
	ORDER_CODE_FIELD,
	SETTINGS_DOCTYPE,
	SHIPPING_METHOD_FIELD,
	SHIPPING_PACKAGE_CODE_FIELD,
	SHIPPING_PACKAGE_STATUS_FIELD,
	SHIPPING_PROVIDER_CODE,
	TRACKING_CODE_FIELD,
)

# Older than any Bin.modified, so the next inventory run picks the item up.
STALE_SYNC_TIMESTAMP = "2000-01-01 00:00:00"

# (fieldname, dashboard label) pairs: Sales Order columns and Sales Invoice columns of its
# latest invoice. Fields absent from a site's doctypes are skipped by the shared helpers.
ORDER_DETAILS = [
	(CHANNEL_ID_FIELD, "Channel"),
	(FACILITY_CODE_FIELD, "Facility Code"),
]
INVOICE_DETAILS = [
	(INVOICE_CODE_FIELD, "Platform Invoice"),
	(SHIPPING_PACKAGE_CODE_FIELD, "Package"),
	(SHIPPING_PROVIDER_CODE, "Shipping Provider"),
	(SHIPPING_METHOD_FIELD, "Shipping Method"),
	(TRACKING_CODE_FIELD, "Tracking Number"),
	(SHIPPING_PACKAGE_STATUS_FIELD, "Package Status"),
]
# The same facts as columns in the shared orders table; key = details key (the fieldname).
ORDER_COLUMNS = [
	{"key": CHANNEL_ID_FIELD, "label": "Channel", "width": "110px"},
	{"key": FACILITY_CODE_FIELD, "label": "Facility Code", "width": "130px"},
	{"key": INVOICE_CODE_FIELD, "label": "Platform Invoice", "width": "120px"},
	{"key": SHIPPING_PACKAGE_CODE_FIELD, "label": "Package", "width": "120px"},
	{"key": SHIPPING_PROVIDER_CODE, "label": "Shipping Provider", "width": "120px"},
	{"key": SHIPPING_METHOD_FIELD, "label": "Shipping Method", "width": "140px"},
	{"key": TRACKING_CODE_FIELD, "label": "Tracking Number", "width": "150px"},
	{"key": SHIPPING_PACKAGE_STATUS_FIELD, "label": "Package Status", "width": "140px"},
]
# Dashboard filter key -> Sales Order fieldname it filters on.
ORDER_FILTER_FIELDS = {
	"channel": CHANNEL_ID_FIELD,
	"facility": FACILITY_CODE_FIELD,
}


def _distinct_values(fieldname: str) -> list[str]:
	"""Distinct non-empty values of a Sales Order column, for the dropdown filters."""
	return sorted(
		value
		for value in frappe.get_all(
			"Sales Order", filters={fieldname: ("is", "set")}, pluck=fieldname, distinct=True
		)
		if value
	)


class UnicommerceDashboardAdapter(DashboardAdapter):
	def is_enabled(self) -> bool:
		return frappe.get_cached_doc(SETTINGS_DOCTYPE).is_enabled()

	def get_recent_orders(self, limit, search=None, status=None, filters=None):
		return queries.recent_sales_orders(
			ORDER_CODE_FIELD,
			limit,
			search,
			status,
			extra_fields=ORDER_DETAILS,
			invoice_fields=INVOICE_DETAILS,
			filter_fields=ORDER_FILTER_FIELDS,
			filters=filters,
		)

	def count_orders(self, search=None, status=None, filters=None):
		return queries.count_sales_orders(
			ORDER_CODE_FIELD, search, status, filter_fields=ORDER_FILTER_FIELDS, filters=filters
		)

	def get_order_filter_options(self):
		options = []
		for key, label, fieldname in (
			("channel", "Channel", CHANNEL_ID_FIELD),
			("facility", "Facility Code", FACILITY_CODE_FIELD),
		):
			values = _distinct_values(fieldname)
			if values:
				options.append({"key": key, "label": label, "options": [(v, v) for v in values]})
		return options

	def get_order_columns(self):
		return ORDER_COLUMNS

	def get_pending_payments(self, limit, search=None, status=None):
		return queries.pending_sales_invoices(
			ORDER_CODE_FIELD, limit, search, status, cod_field=IS_COD_CHECKBOX
		)

	def count_pending_payments(self, search=None, status=None):
		return queries.count_pending_sales_invoices(
			ORDER_CODE_FIELD, search, status, cod_field=IS_COD_CHECKBOX
		)

	def get_pending_summary(self):
		return queries.pending_sales_invoice_summary(ORDER_CODE_FIELD)

	def push_inventory(self, ecommerce_items):
		settings = frappe.get_cached_doc(SETTINGS_DOCTYPE)
		if not settings.enable_inventory_sync:
			frappe.throw(_("Inventory sync is disabled in Unicommerce Settings."))

		for name in ecommerce_items:
			frappe.db.set_value(
				"Ecommerce Item", name, "inventory_synced_on", STALE_SYNC_TIMESTAMP, update_modified=False
			)

		frappe.enqueue(
			"unicommerce.unicommerce.inventory.update_inventory_on_unicommerce",
			queue="short",
			job_id="unicommerce_dashboard_inventory_push",
			deduplicate=True,
			force=True,
			enqueue_after_commit=True,
		)
		return _("Stock push to Unicommerce queued")

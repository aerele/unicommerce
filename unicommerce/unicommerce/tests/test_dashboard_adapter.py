# Copyright (c) 2026, Aerele Technologies and contributors
# For license information, please see license.txt

"""Tests for the Unicommerce dashboard adapter's declarations and feeds."""

from ecommerce_core.dashboard.adapter import DashboardAdapter
from frappe.tests import IntegrationTestCase

from unicommerce.unicommerce.dashboard import (
	INVOICE_DETAILS,
	ORDER_COLUMNS,
	ORDER_DETAILS,
	ORDER_FILTER_FIELDS,
	UnicommerceDashboardAdapter,
)


class TestUnicommerceDashboardAdapter(IntegrationTestCase):
	def test_adapter_implements_the_dashboard_contract(self):
		adapter = UnicommerceDashboardAdapter()
		self.assertIsInstance(adapter, DashboardAdapter)
		for method in (
			"get_recent_orders",
			"count_orders",
			"get_pending_payments",
			"count_pending_payments",
			"get_pending_summary",
			"get_order_columns",
			"get_order_filter_options",
			"push_inventory",
		):
			self.assertTrue(adapter.implements(method), method)

	def test_columns_cover_every_declared_detail(self):
		column_keys = {column["key"] for column in ORDER_COLUMNS}
		detail_keys = {fieldname for fieldname, _label in ORDER_DETAILS + INVOICE_DETAILS}
		self.assertEqual(column_keys, detail_keys)
		for column in ORDER_COLUMNS:
			self.assertTrue(column["label"])

	def test_order_filters_are_declared_for_channel_and_facility(self):
		self.assertEqual(set(ORDER_FILTER_FIELDS), {"channel", "facility"})

	def test_recent_orders_is_a_list_for_any_site(self):
		self.assertIsInstance(UnicommerceDashboardAdapter().get_recent_orders(limit=5), list)

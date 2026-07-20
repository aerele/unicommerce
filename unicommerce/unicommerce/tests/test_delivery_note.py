import base64
import unittest
from typing import ClassVar

import frappe
import responses
from erpnext.stock.doctype.stock_entry.stock_entry_utils import make_stock_entry
from frappe.test_runner import make_test_records

from unicommerce.unicommerce.constants import (
	FACILITY_CODE_FIELD,
	INVOICE_CODE_FIELD,
	ORDER_CODE_FIELD,
	SHIPPING_PACKAGE_CODE_FIELD,
)
from unicommerce.unicommerce.delivery_note import create_delivery_note
from unicommerce.unicommerce.invoice import bulk_generate_invoices, create_sales_invoice
from unicommerce.unicommerce.order import create_order
from unicommerce.unicommerce.tests.test_client import TestCaseApiClient
from unicommerce.unicommerce.tests.utils import (
	allow_multi_currency_invoicing,
	allow_repeated_line_items,
)


class TestDeliveryNote(TestCaseApiClient):
	# Defer stock to the Delivery Note so the Sales Order stays deliverable.
	config: ClassVar = {**TestCaseApiClient.config, "delivery_note": 1}

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		# Create the RAINFOREST channel this test needs instead of relying on
		# another test to create and commit it first (which made this test flaky).
		make_test_records("Unicommerce Channel")

	@allow_repeated_line_items
	@allow_multi_currency_invoicing
	def test_create_invoice_and_delivery_note(self):
		"""Use mocked invoice json to create and assert synced fields"""
		from unicommerce.unicommerce import invoice

		# HACK to allow invoicing test
		invoice.INVOICED_STATE.append("CREATED")
		self.responses.add(
			responses.POST,
			"https://demostaging.unicommerce.com/services/rest/v1/oms/shippingPackage/createInvoiceAndAllocateShippingProvider",
			status=200,
			json=self.load_fixture("create_invoice_and_assign_shipper"),
			match=[responses.json_params_matcher({"shippingPackageCode": "TEST00949"})],
		)
		self.responses.add(
			responses.POST,
			"https://demostaging.unicommerce.com/services/rest/v1/invoice/details/get",
			status=200,
			json=self.load_fixture("invoice-SDU0026"),
			match=[responses.json_params_matcher({"shippingPackageCode": "TEST00949", "return": False})],
		)
		self.responses.add(
			responses.GET,
			"https://example.com",
			status=200,
			body=base64.b64decode(self.load_fixture("invoice_label_response")["label"]),
		)

		order = self.load_fixture("order-SO5906")["saleOrderDTO"]
		so = create_order(order, client=self.client)
		make_stock_entry(item_code="MC-100", qty=15, to_warehouse="Stores - WP", rate=42)

		bulk_generate_invoices(sales_orders=[so.name], client=self.client)

		sales_invoice_code = frappe.db.get_value("Sales Invoice", {INVOICE_CODE_FIELD: "SDU0026"})

		if not sales_invoice_code:
			self.fail("Sales invoice not generated")

		si = frappe.get_doc("Sales Invoice", sales_invoice_code)
		dn = create_delivery_note(so, si)
		self.assertEqual(dn.unicommerce_order_code, so.unicommerce_order_code)

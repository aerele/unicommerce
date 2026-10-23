import json

import frappe
import responses
from ecommerce_core.ecommerce_core.doctype.ecommerce_item import ecommerce_item

from unicommerce.product_sync import UnicommerceProductSyncAdapter
from unicommerce.unicommerce.constants import MODULE_NAME
from unicommerce.unicommerce.tests.test_client import TestCaseApiClient

SEARCH_URL = "https://demostaging.unicommerce.com/services/rest/v1/product/itemType/search"

SEARCH_PAGE = {
	"successful": True,
	"totalRecords": 8,
	"elements": [
		{"skuCode": "SKU-001", "name": "Amrutam Honey 500g", "enabled": True},
		{"skuCode": "SKU-002", "name": None, "enabled": True},
	],
}


class TestUnicommerceProductSyncAdapter(TestCaseApiClient):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.adapter = UnicommerceProductSyncAdapter(client=cls.client)

	def search_mock(self, body=SEARCH_PAGE, **kwargs):
		return self.responses.add(responses.POST, SEARCH_URL, status=200, json=body, **kwargs)

	def test_is_enabled_reflects_settings(self):
		"""requirement: the page only shows the provider when Unicommerce is enabled"""
		self.assertTrue(self.adapter.is_enabled())

	def test_get_products_maps_one_page(self):
		"""requirement: listing returns provider products with an opaque offset cursor"""
		self.search_mock()

		page = self.adapter.get_products(limit=2)

		self.assertEqual(
			[
				{"id": "SKU-001", "name": "Amrutam Honey 500g", "sku": "SKU-001"},
				{"id": "SKU-002", "name": "SKU-002", "sku": "SKU-002"},
			],
			page["products"],
		)
		self.assertEqual(page["total"], 8)
		self.assertEqual(page["next_cursor"], "o:2")
		self.assertEqual(
			{"searchOptions": {"displayStart": 0, "displayLength": 2, "getCount": True}},
			json.loads(self.responses.calls[0].request.body),
		)

	def test_get_products_follows_offset_cursor(self):
		"""requirement: the cursor resumes listing at the recorded offset"""
		self.search_mock()

		page = self.adapter.get_products(limit=2, cursor="o:6")

		request_body = json.loads(self.responses.calls[0].request.body)
		self.assertEqual(6, request_body["searchOptions"]["displayStart"])
		# 6 + 2 >= totalRecords: no further page
		self.assertIsNone(page["next_cursor"])

	def test_get_products_without_total_falls_back_to_page_length(self):
		"""requirement: a missing totalRecords does not break pagination"""
		self.search_mock(body={"successful": True, "elements": SEARCH_PAGE["elements"]})

		full_page = self.adapter.get_products(limit=2)
		last_page = self.adapter.get_products(limit=3)

		self.assertEqual(full_page["next_cursor"], "o:2")
		self.assertIsNone(full_page["total"])
		self.assertIsNone(last_page["next_cursor"])

	def test_get_products_passes_search_keyword(self):
		"""requirement: the page's search box filters the remote catalog"""
		body = {
			"keyword": "honey",
			"searchOptions": {"displayStart": 0, "displayLength": 2, "getCount": True},
		}
		self.search_mock(match=[responses.json_params_matcher(body)])

		self.adapter.get_products(limit=2, search="honey")

	def test_get_products_failure_raises(self):
		"""requirement: a failed search surfaces as an error instead of an empty catalog"""
		self.search_mock(body={"successful": False, "errors": [{"message": "boom"}]})

		self.assertRaises(frappe.ValidationError, self.adapter.get_products, 2)

	def test_get_provider_count(self):
		"""requirement: the stats card shows the remote catalog size"""
		self.search_mock()

		self.assertEqual(8, self.adapter.get_provider_count())

	def test_sync_product_creates_item_and_mapping(self):
		"""requirement: single sync imports the SKU and reports 'created'"""
		result = self.adapter.sync_product("TITANIUM_WATCH")

		self.assertEqual("created", result["action"])
		self.assertEqual("TITANIUM_WATCH", result["item_code"])
		self.assertTrue(frappe.db.exists("Item", "TITANIUM_WATCH"))
		self.assertTrue(ecommerce_item.is_synced(MODULE_NAME, "TITANIUM_WATCH"))

	def test_sync_product_of_synced_sku_is_a_no_op(self):
		"""requirement: re-syncing a mapped SKU does not fail and reports 'skipped'"""
		self.adapter.sync_product("TITANIUM_WATCH")

		result = self.adapter.sync_product("TITANIUM_WATCH")

		self.assertEqual("skipped", result["action"])
		self.assertEqual(1, frappe.db.count("Item", {"item_code": "TITANIUM_WATCH"}))

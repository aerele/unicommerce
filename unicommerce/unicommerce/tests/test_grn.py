import json

import frappe
import responses

from unicommerce.unicommerce.constants import SETTINGS_DOCTYPE
from unicommerce.unicommerce.tests.test_client import TestCaseApiClient
from unicommerce.unicommerce.tests.utils import TestCase

ADJUST_URL = "https://demostaging.unicommerce.com/services/rest/v1/inventory/adjust/bulk"


class TestGRNBatchAdjustment(TestCaseApiClient):
	"""Payload building for create_batch_inventory_adjustment (per batch group)."""

	def setUp(self):
		super().setUp()
		settings = frappe.get_doc(SETTINGS_DOCTYPE)
		settings.set("batch_group_configs", [])
		# BATCH1 requires only Mfg + Vendor Batch Number
		settings.append(
			"batch_group_configs",
			{"batch_group_code": "BATCH1", "attr_mfd": 1, "attr_vendor_batch_number": 1},
		)
		# TEST_BATCH also requires Expiry Date
		settings.append(
			"batch_group_configs",
			{
				"batch_group_code": "TEST_BATCH",
				"attr_mfd": 1,
				"attr_expiry_date": 1,
				"attr_vendor_batch_number": 1,
			},
		)
		settings.flags.ignore_validate = True
		settings.flags.ignore_mandatory = True
		settings.save()

	def _capture_adjust_request(self):
		"""Register the bulk-adjust endpoint and return a dict that captures the sent body."""
		captured = {}

		def callback(request):
			captured["body"] = json.loads(request.body)
			return (200, {}, json.dumps({"successful": True, "inventoryAdjustmentResponses": []}))

		self.responses.add_callback(
			responses.POST, ADJUST_URL, callback=callback, content_type="application/json"
		)
		return captured

	def test_batch_details_use_group_attributes(self):
		"""Each item's batchDetails contains only the attributes its batch group requires."""
		captured = self._capture_adjust_request()

		adjustments = [
			{
				"itemSKU": "SKU1",
				"quantity": 5,
				"batchGroupCode": "BATCH1",
				"vendorBatchNumber": "VB1",
				"mrp": 100,
				"mfd": 111,
				"expiryDate": 222,
			},
			{
				"itemSKU": "SKU2",
				"quantity": 3,
				"batchGroupCode": "TEST_BATCH",
				"vendorBatchNumber": "VB2",
				"mrp": 200,
				"mfd": 333,
				"expiryDate": 444,
			},
		]
		self.client.create_batch_inventory_adjustment(adjustments, facility_code="Test-123")

		sent = {a["itemSKU"]: a for a in captured["body"]["inventoryAdjustments"]}

		# BATCH1 -> only mfd + vendorBatchNumber (no expiryDate, no mrp)
		self.assertEqual(set(sent["SKU1"]["batchDetails"]), {"mfd", "vendorBatchNumber"})
		self.assertEqual(sent["SKU1"]["batchDetails"]["mfd"], 111)
		self.assertEqual(sent["SKU1"]["batchDetails"]["vendorBatchNumber"], "VB1")

		# TEST_BATCH -> mfd + expiryDate + vendorBatchNumber
		self.assertEqual(set(sent["SKU2"]["batchDetails"]), {"mfd", "expiryDate", "vendorBatchNumber"})
		self.assertEqual(sent["SKU2"]["batchDetails"]["expiryDate"], 444)

		# forceAllocate is sent at the body level
		self.assertFalse(captured["body"]["forceAllocate"])

	def test_no_batch_code_is_sent(self):
		"""batchCode must not appear at the top level or inside batchDetails."""
		captured = self._capture_adjust_request()

		self.client.create_batch_inventory_adjustment(
			[{"itemSKU": "SKU1", "quantity": 1, "batchGroupCode": "BATCH1", "mfd": 1}],
			facility_code="Test-123",
		)
		adjustment = captured["body"]["inventoryAdjustments"][0]
		self.assertNotIn("batchCode", adjustment)
		self.assertNotIn("batchCode", adjustment["batchDetails"])

	def test_unconfigured_group_is_skipped(self):
		"""Items whose batch group has no config are skipped, not sent."""
		captured = self._capture_adjust_request()

		adjustments = [
			{
				"itemSKU": "SKU1",
				"quantity": 1,
				"batchGroupCode": "BATCH1",
				"mfd": 1,
				"vendorBatchNumber": "VB1",
			},
			{"itemSKU": "SKUX", "quantity": 1, "batchGroupCode": "UNKNOWN", "mfd": 1},
		]
		response = self.client.create_batch_inventory_adjustment(adjustments, facility_code="Test-123")

		sent_skus = [a["itemSKU"] for a in captured["body"]["inventoryAdjustments"]]
		self.assertEqual(sent_skus, ["SKU1"])
		self.assertTrue(any("SKUX" in entry for entry in response.get("skipped", [])))

	def test_all_items_unconfigured_returns_failure(self):
		"""When no item has a configured batch group, no API call is made and it fails."""
		response = self.client.create_batch_inventory_adjustment(
			[{"itemSKU": "SKUX", "quantity": 1, "batchGroupCode": "UNKNOWN"}],
			facility_code="Test-123",
		)
		self.assertFalse(response["successful"])
		self.assertTrue(any("SKUX" in entry for entry in response["errors"]))


class TestGRNSettingsValidation(TestCase):
	"""validate_auto_grn_settings guards for the batch group config table."""

	def _settings_with_rows(self, rows):
		settings = frappe.get_doc(SETTINGS_DOCTYPE)
		settings.use_stock_entry_for_grn = 1
		settings.vendor_code = "ERP"
		settings.set("batch_group_configs", [])
		for row in rows:
			settings.append("batch_group_configs", row)
		return settings

	def test_empty_table_is_rejected(self):
		settings = self._settings_with_rows([])
		self.assertRaises(frappe.ValidationError, settings.validate_auto_grn_settings)

	def test_row_without_attributes_is_rejected(self):
		settings = self._settings_with_rows([{"batch_group_code": "BATCH1"}])
		self.assertRaises(frappe.ValidationError, settings.validate_auto_grn_settings)

	def test_duplicate_batch_group_codes_are_rejected(self):
		settings = self._settings_with_rows(
			[
				{"batch_group_code": "BATCH1", "attr_mfd": 1},
				{"batch_group_code": "BATCH1", "attr_mfd": 1},
			]
		)
		self.assertRaises(frappe.ValidationError, settings.validate_auto_grn_settings)

	def test_valid_config_passes(self):
		settings = self._settings_with_rows([{"batch_group_code": "BATCH1", "attr_mfd": 1}])
		# should not raise
		settings.validate_auto_grn_settings()

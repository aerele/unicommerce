import frappe
from frappe import _
from frappe.utils import cint, get_datetime

from unicommerce.unicommerce.api_client import UnicommerceAPIClient
from unicommerce.unicommerce.constants import (
	GRN_STOCK_ENTRY_TYPE,
	ITEM_BATCH_GROUP_FIELD,
	MODULE_NAME,
	SETTINGS_DOCTYPE,
)
from unicommerce.unicommerce.utils import create_unicommerce_log


def is_unicommerce_grn(stock_entry) -> bool:
	if stock_entry.stock_entry_type != GRN_STOCK_ENTRY_TYPE:
		return False

	grn_enabled = frappe.db.get_single_value(SETTINGS_DOCTYPE, "use_stock_entry_for_grn")
	if not grn_enabled:
		frappe.throw(
			_("Auto GRN not enabled in Unicommerce settings. Can not use Stock Entry Type: {}").format(
				GRN_STOCK_ENTRY_TYPE
			)
		)
	return True


def validate_stock_entry_for_grn(doc, method=None):
	stock_entry = doc
	if not is_unicommerce_grn(stock_entry):
		return

	settings = frappe.get_doc(SETTINGS_DOCTYPE)

	if not settings.is_enabled():
		return

	get_facility_code(stock_entry, settings)


def get_facility_code(stock_entry, unicommerce_settings) -> str:
	"""Validate that facility has single warehouse and return facility code."""

	target_warehouses = {d.t_warehouse for d in stock_entry.items}
	if len(target_warehouses) > 1:
		frappe.throw(
			_("{} only supports one target warehouse (unicommerce facility)").format(GRN_STOCK_ENTRY_TYPE)
		)

	warehouse = next(iter(target_warehouses))
	warehouse_mapping = unicommerce_settings.get_erpnext_to_integration_wh_mapping(all_wh=True)

	facility = warehouse_mapping.get(warehouse)
	if not facility:
		msg = _("{} warehouse does not have Unicommerce facilities mapped to it.").format(warehouse)
		frappe.throw(msg, title="Unmapped Unicommerce Facility")

	return facility


def upload_grn(doc, method=None):
	stock_entry = doc
	if not is_unicommerce_grn(stock_entry):
		return

	frappe.enqueue(
		"unicommerce.unicommerce.grn.process_grn_background",
		queue="short",
		stock_entry_name=stock_entry.name,
		enqueue_after_commit=True,
	)

	frappe.msgprint(_("GRN processing has been queued. You will be notified once it's completed."))


def process_grn_background(stock_entry_name: str):
	"""Process GRN in background - creates inventory adjustment in Unicommerce"""
	try:
		stock_entry = frappe.get_doc("Stock Entry", stock_entry_name)

		if not is_unicommerce_grn(stock_entry):
			create_unicommerce_log(
				status="Error",
				message=f"Stock Entry {stock_entry_name} is not a valid GRN",
				make_new=True,
			)
			return

		settings = frappe.get_doc(SETTINGS_DOCTYPE)
		facility_code = get_facility_code(stock_entry, settings)

		inventory_adjustments = _prepare_inventory_adjustments(stock_entry)
		response = UnicommerceAPIClient().create_batch_inventory_adjustment(
			inventory_adjustments, facility_code
		)

		def _log_failure(message):
			create_unicommerce_log(
				status="Failure",
				message=message,
				request_data=inventory_adjustments,
				response_data=response,
				make_new=True,
			)

		if not response or not response.get("successful"):
			_log_failure(f"GRN inventory adjustment failed for {stock_entry_name}")
			return

		# Item-level errors (e.g. batch attributes not matching the batch group) plus
		# items skipped because their batch group has no attribute config.
		failed_items = [
			f"SKU {r.get('itemSKU')}: {r.get('message', 'Unknown error')}"
			for r in response.get("inventoryAdjustmentResponses", [])
			if not r.get("successful")
		]
		failed_items += response.get("skipped", [])

		if failed_items:
			_log_failure(f"GRN partial failure for {stock_entry_name}: {', '.join(failed_items)}")
		else:
			stock_entry.add_comment("Comment", "GRN successfully synced to Unicommerce")

	except Exception as e:
		create_unicommerce_log(
			status="Error",
			message=f"GRN processing error for {stock_entry_name}",
			exception=e,
			rollback=True,
			make_new=True,
		)


def _prepare_inventory_adjustments(stock_entry) -> list:
	"""Prepare inventory adjustment data directly from stock entry items
	Uses batched database queries for optimal performance
	returns: list of inventory adjustment dictionaries
	"""

	vendor_invoice_number = stock_entry.name
	item_codes = [item.item_code for item in stock_entry.items]
	batch_numbers = [item.batch_no for item in stock_entry.items if item.batch_no]

	# Batch query: Get all SKUs at once
	sku_map = frappe._dict()
	if item_codes:
		sku_data = frappe.db.get_all(
			"Ecommerce Item",
			filters={"erpnext_item_code": ("in", item_codes), "integration": MODULE_NAME},
			fields=["erpnext_item_code", "integration_item_code"],
		)
		sku_map = {row.erpnext_item_code: row.integration_item_code for row in sku_data}

	# Batch query: Get all batch details at once
	batch_details_map = frappe._dict()
	if batch_numbers:
		batch_data = frappe.db.get_all(
			"Batch",
			filters={"name": ("in", batch_numbers)},
			fields=["name", "manufacturing_date", "expiry_date"],
		)
		batch_details_map = {row.name: row for row in batch_data}

	# Batch query: Get MRP, cost, country of origin and batch group code per item
	item_map = frappe._dict()
	if item_codes:
		item_data = frappe.db.get_values(
			"Item",
			{"name": ("in", item_codes)},
			["name", "standard_rate", "valuation_rate", "country_of_origin", ITEM_BATCH_GROUP_FIELD],
			as_dict=True,
		)
		item_map = {row.name: row for row in item_data}

	inventory_adjustments = []

	for item in stock_entry.items:
		sku = sku_map.get(item.item_code)
		if not sku:
			frappe.throw(_("Item {} does not have associated Unicommerce SKU.").format(item.item_code))

		batch = batch_details_map.get(item.batch_no) if item.batch_no else None
		item_detail = item_map.get(item.item_code) or frappe._dict()

		inventory_adjustments.append(
			{
				"itemSKU": sku,
				"quantity": cint(item.qty),
				"remarks": f"Vendor Invoice: {vendor_invoice_number}",
				"batchGroupCode": item_detail.get(ITEM_BATCH_GROUP_FIELD),
				"vendorBatchNumber": item.batch_no or "",
				"mrp": item_detail.standard_rate,
				"cost": item_detail.valuation_rate,
				"coo": item_detail.country_of_origin,
				"mfd": _to_epoch_millis(batch.manufacturing_date) if batch else None,
				"expiryDate": _to_epoch_millis(batch.expiry_date) if batch else None,
			}
		)

	return inventory_adjustments


def _to_epoch_millis(value) -> int | None:
	"""Convert a date/datetime to a Unix epoch timestamp in milliseconds."""
	if not value:
		return None
	return int(get_datetime(value).timestamp() * 1000)


def prevent_grn_cancel(doc, method=None):
	if not is_unicommerce_grn(doc):
		return

	msg = _("This Stock Entry can not be cancelled.")
	msg += _("To undo this stock entry you need to move the Stock back") + " "
	msg += _("and remove stock from Unicommerce.")

	frappe.throw(msg, title="GRN Stock Entry can not be cancelled")

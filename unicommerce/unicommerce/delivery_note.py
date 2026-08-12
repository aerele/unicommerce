import frappe

from unicommerce.unicommerce.api_client import UnicommerceAPIClient
from unicommerce.unicommerce.constants import ORDER_CODE_FIELD, SETTINGS_DOCTYPE
from unicommerce.unicommerce.utils import create_unicommerce_log


@frappe.whitelist()
def prepare_delivery_note():
	try:
		settings = frappe.get_cached_doc(SETTINGS_DOCTYPE)
		if not settings.delivery_note:
			return

		client = UnicommerceAPIClient()

		days_to_sync = min(settings.get("order_status_days") or 2, 14)
		minutes = days_to_sync * 24 * 60

		# find all Facilities
		enabled_facilities = list(settings.get_integration_to_erpnext_wh_mapping().keys())
		enabled_channels = frappe.db.get_list(
			"Unicommerce Channel", filters={"enabled": 1}, pluck="channel_id"
		)

		for facility in enabled_facilities:
			updated_packages = client.search_shipping_packages(updated_since=minutes, facility_code=facility)
			valid_packages = [p for p in updated_packages if p.get("channel") in enabled_channels]
			shipped_packages = [p for p in valid_packages if p["status"] in ["DISPATCHED"]]
			if not shipped_packages:
				continue

			# Batch-fetch existence data once per facility instead of querying per package.
			package_codes = [p["code"] for p in shipped_packages]
			order_codes = [p["saleOrderCode"] for p in shipped_packages]

			shipments_with_dn = set(
				frappe.get_all(
					"Delivery Note",
					filters={"unicommerce_shipment_id": ("in", package_codes)},
					pluck="unicommerce_shipment_id",
				)
			)
			existing_so_codes = set(
				frappe.get_all(
					"Sales Order", filters={ORDER_CODE_FIELD: ("in", order_codes)}, pluck=ORDER_CODE_FIELD
				)
			)
			codes_with_invoice = set(
				frappe.get_all(
					"Sales Invoice", filters={ORDER_CODE_FIELD: ("in", order_codes)}, pluck=ORDER_CODE_FIELD
				)
			)

			for order in shipped_packages:
				order_code = order["saleOrderCode"]
				if order["code"] in shipments_with_dn:
					continue
				if order_code not in existing_so_codes or order_code not in codes_with_invoice:
					continue
				sales_order = frappe.get_doc("Sales Order", {ORDER_CODE_FIELD: order_code})
				sales_invoice = frappe.get_doc("Sales Invoice", {ORDER_CODE_FIELD: order_code})
				create_delivery_note(sales_order, sales_invoice)
	except Exception as e:
		create_unicommerce_log(status="Error", exception=e, rollback=True)


def create_delivery_note(so, sales_invoice):
	# Create the delivery note
	from erpnext.selling.doctype.sales_order.mapper import make_delivery_note

	try:
		res = make_delivery_note(source_name=so.name)
		res.unicommerce_order_code = sales_invoice.unicommerce_order_code
		res.unicommerce_shipment_id = sales_invoice.unicommerce_shipping_package_code
		res.save()
		res.submit()
		log = create_unicommerce_log(method="create_delivery_note", make_new=True)
		frappe.flags.request_id = log.name
		create_unicommerce_log(
			status="Success", message=f"Delivery Note {res.name} created for Sales Order {so.name}"
		)
		frappe.flags.request_id = None
		return res
	except Exception as e:
		create_unicommerce_log(status=f"Error: {so.name}", exception=e, rollback=True)

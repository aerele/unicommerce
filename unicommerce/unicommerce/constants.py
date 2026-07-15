import re

SETTINGS_DOCTYPE = "Unicommerce Settings"
MODULE_NAME = "unicommerce"

DEFAULT_WEIGHT_UOM = "Gram"
UNICOMMERCE_SKU_PATTERN = re.compile(r"[A-Za-z0-9._\-/]{3,45}")


# Custom fields
ITEM_SYNC_CHECKBOX = "sync_with_unicommerce"
ORDER_CODE_FIELD = "unicommerce_order_code"
CHANNEL_ID_FIELD = "unicommerce_channel_id"
ORDER_STATUS_FIELD = "unicommerce_order_status"
ORDER_INVOICE_STATUS_FIELD = "unicommerce_invoicing_status"
ORDER_ITEM_CODE_FIELD = "unicommerce_order_item_code"
ORDER_ITEM_BATCH_NO = "unicommerce_batch_code"
PRODUCT_CATEGORY_FIELD = "unicommerce_product_category"
FACILITY_CODE_FIELD = "unicommerce_facility_code"
INVOICE_CODE_FIELD = "unicommerce_invoice_code"
SHIPPING_PACKAGE_CODE_FIELD = "unicommerce_shipping_package_code"
RETURN_CODE_FIELD = "unicommerce_return_code"
TRACKING_CODE_FIELD = "unicommerce_tracking_code"
SHIPPING_PROVIDER_CODE = "unicommerce_shipping_provider"
MANIFEST_GENERATED_CHECK = "unicommerce_manifest_generated"
ADDRESS_JSON_FIELD = "unicommerce_raw_billing_address"
CUSTOMER_CODE_FIELD = "unicommerce_customer_code"
PACKAGE_TYPE_FIELD = "unicommerce_package_type"
ITEM_LENGTH_FIELD = "unicommerce_item_length"
ITEM_WIDTH_FIELD = "unicommerce_item_width"
ITEM_HEIGHT_FIELD = "unicommerce_item_height"
ITEM_BATCH_GROUP_FIELD = "unicommerce_batch_group_code"
SHIPPING_PACKAGE_STATUS_FIELD = "unicommerce_shipping_package_status"
IS_COD_CHECKBOX = "unicommerce_is_cod"
SHIPPING_METHOD_FIELD = "unicommerce_shipping_method"
UNICOMMERCE_SHIPPING_ID = "unicommerce_shipment_id"
PICKLIST_ORDER_DETAILS_FIELD = "order_details"

GRN_STOCK_ENTRY_TYPE = "GRN on Unicommerce"


# Tax -> Unicommerce tax amount field mapping
TAX_FIELDS_MAPPING = {
	"igst": "integratedGst",
	"cgst": "centralGst",
	"sgst": "stateGst",
	"ugst": "unionTerritoryGst",
	"tcs": "tcsAmount",
	"cash_on_delivery_charges": "cashOnDeliveryCharges",
	"gift_wrap_charges": "giftWrapCharges",
	"shipping_charges": "shippingCharges",
	"shipping_method_charges": "shippingMethodCharges",
}

# Tax -> Unicommerce tax "rate" field mapping
TAX_RATE_FIELDS_MAPPING = {
	"igst": "integratedGstPercentage",
	"cgst": "centralGstPercentage",
	"sgst": "stateGstPercentage",
	"ugst": "unionTerritoryGstPercentage",
}

# field name for accounts in Unicommerce channels
CHANNEL_TAX_ACCOUNT_FIELD_MAP = {
	"igst": "igst_account",
	"cgst": "cgst_account",
	"sgst": "sgst_account",
	"ugst": "ugst_account",
	"tcs": "tcs_account",
	"cash_on_delivery_charges": "cod_account",
	"gift_wrap_charges": "gift_wrap_account",
	"shipping_charges": "fnf_account",
	"shipping_method_charges": "fnf_account",
}

"""Product Sync adapter for the shared Ecommerce Core page.

Registered through the ``ecommerce_product_sync_providers`` hook (see hooks.py).
A thin facade over the existing Unicommerce item import: the page's listing and
search use the tenant-level itemType search API, syncing reuses
``import_product_from_unicommerce``.
"""

from __future__ import annotations

import frappe
from ecommerce_core.ecommerce_core.doctype.ecommerce_item import ecommerce_item
from ecommerce_core.product_sync.adapter import ProductSyncAdapter
from frappe import _
from frappe.utils import cint

from unicommerce.unicommerce.api_client import UnicommerceAPIClient
from unicommerce.unicommerce.constants import MODULE_NAME, SETTINGS_DOCTYPE
from unicommerce.unicommerce.product import import_product_from_unicommerce


class UnicommerceProductSyncAdapter(ProductSyncAdapter):
	"""Contract implementation for ``ecommerce_core.product_sync``."""

	def __init__(self, client: UnicommerceAPIClient | None = None):
		self._client = client

	def is_enabled(self) -> bool:
		return bool(frappe.db.get_single_value(SETTINGS_DOCTYPE, "enable_unicommerce"))

	@property
	def client(self) -> UnicommerceAPIClient:
		# Created lazily: adapters are instantiated on every request, but the
		# client loads the settings and refreshes tokens in its constructor.
		if self._client is None:
			self._client = UnicommerceAPIClient()
		return self._client

	def get_products(self, limit: int, cursor: str | None = None, search: str | None = None) -> dict:
		# The opaque cursor is an "o:<offset>" token: the itemType search API
		# paginates with DataTables-style displayStart/displayLength.
		start = _decode_offset_cursor(cursor)
		response = self._search(keyword=search, start=start, length=limit)

		elements = response.get("elements") or []
		total = response.get("totalRecords")
		total = cint(total) if total is not None else None

		if total is None:
			has_more = len(elements) == limit
		else:
			has_more = start + limit < total

		return {
			"products": [
				{
					"id": element["skuCode"],
					"name": element.get("name") or element["skuCode"],
					"sku": element["skuCode"],
				}
				for element in elements
			],
			"total": total,
			"next_cursor": f"o:{start + limit}" if has_more else None,
		}

	def get_provider_count(self) -> int:
		response = self._search(start=0, length=1)
		total = response.get("totalRecords")
		return cint(total) if total is not None else 0

	def sync_product(self, product_id: str) -> dict:
		# The importer only creates (existing mappings short-circuit inside
		# create_ecommerce_item), so an already synced SKU is a no-op sync.
		was_synced = ecommerce_item.is_synced(MODULE_NAME, integration_item_code=product_id)
		import_product_from_unicommerce(product_id, client=self.client)
		return {
			"action": "skipped" if was_synced else "created",
			"item_code": product_id,
		}

	def _search(self, keyword: str | None, start: int, length: int) -> dict:
		response = self.client.search_item_types(keyword=keyword, start=start, length=length)
		if response is None:
			# The client already logged the API error with the request details.
			frappe.throw(_("Unicommerce item search failed. Check the Unicommerce error logs."))

		return response


def _decode_offset_cursor(cursor: str | None) -> int:
	if not cursor or not str(cursor).startswith("o:"):
		return 0
	try:
		return max(int(str(cursor)[2:]), 0)
	except ValueError:
		return 0

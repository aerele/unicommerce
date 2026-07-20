import frappe

try:
	from frappe.tests import IntegrationTestCase
except ImportError:
	from frappe.tests.utils import FrappeTestCase as IntegrationTestCase

from ecommerce_core.utils.taxation import get_dummy_tax_category, validate_tax_template

from unicommerce import hooks

GUARD = "ecommerce_core.utils.taxation.validate_tax_template"


class TestTaxationGuard(IntegrationTestCase):
	def test_guard_is_wired_to_item_validate(self):
		"""The shared tax-template guard must run on Item validate."""
		self.assertIn(GUARD, hooks.doc_events["Item"]["validate"])

	def test_dummy_tax_category_rejected_on_item(self):
		"""Using the dummy tax category in an item tax row is blocked."""
		dummy = get_dummy_tax_category()
		item = frappe.get_doc(
			{
				"doctype": "Item",
				"item_code": "_Test Dummy Tax Guard Item",
				"item_group": "All Item Groups",
				"taxes": [{"tax_category": dummy}],
			}
		)
		self.assertRaises(frappe.ValidationError, validate_tax_template, item)

	def test_normal_tax_category_allowed(self):
		"""An item without the dummy category passes the guard."""
		item = frappe.get_doc(
			{
				"doctype": "Item",
				"item_code": "_Test Plain Tax Guard Item",
				"item_group": "All Item Groups",
			}
		)
		validate_tax_template(item)  # must not raise

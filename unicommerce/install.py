import frappe

from unicommerce.unicommerce.doctype.unicommerce_settings.unicommerce_settings import (
	setup_custom_fields,
)


def after_install():
	"""Create Unicommerce custom fields and finish monolith → standalone handoff helpers."""
	setup_custom_fields()
	_reassign_shared_doctypes_module()
	frappe.clear_cache()


def after_migrate():
	"""Keep custom fields present after migrate (idempotent)."""
	setup_custom_fields(update=True)


def _reassign_shared_doctypes_module():
	"""If Ecommerce Item / Integration Log still point at old monolith module, re-home them.

	Safe when ecommerce_core owns those doctypes (standalone install).
	"""
	if "ecommerce_core" not in frappe.get_installed_apps():
		return

	for doctype, module in (
		("Ecommerce Item", "Ecommerce Core"),
		("Ecommerce Integration Log", "Ecommerce Core"),
	):
		if not frappe.db.exists("DocType", doctype):
			continue
		current = frappe.db.get_value("DocType", doctype, "module")
		if current and current != module and frappe.db.exists("Module Def", module):
			frappe.db.set_value("DocType", doctype, "module", module, update_modified=False)

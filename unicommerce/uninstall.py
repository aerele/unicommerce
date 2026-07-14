import frappe


def before_uninstall():
	# Remove only this integration's logs; ecommerce_core owns the doctype and other
	# integrations may still be using it.
	frappe.db.delete("Ecommerce Integration Log", {"integration": "unicommerce"})

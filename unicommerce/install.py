from unicommerce.unicommerce.doctype.unicommerce_settings.unicommerce_settings import (
	setup_custom_fields,
)


def after_install():
	"""Create Unicommerce custom fields on ERPNext doctypes."""
	setup_custom_fields()

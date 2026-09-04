<div align="center">
<img src="unicommerce/public/images/unicommerce.svg" alt="Unicommerce" height="80">
<h1>Unicommerce for ERPNext</h1>
<p>A standalone integration that connects ERPNext with Unicommerce Uniware.</p>

<p>
<a href="https://integrations.frappe.cloud/integrations/ecommerce-integration/unicommerce/overview">Documentation</a> ·
<a href="https://github.com/aerele/unicommerce/issues">Report an Issue</a> ·
<a href="https://github.com/aerele/unicommerce/pulls">Contribute</a>
</p>
<p>
<a href="https://github.com/aerele/unicommerce/actions/workflows/ci.yml"><img src="https://github.com/aerele/unicommerce/actions/workflows/ci.yml/badge.svg?branch=develop" alt="CI"></a>
<a href="https://github.com/aerele/unicommerce/actions/workflows/linters.yml"><img src="https://github.com/aerele/unicommerce/actions/workflows/linters.yml/badge.svg?branch=develop" alt="Linters"></a>
<a href="license.txt"><img src="https://img.shields.io/badge/License-GPL_v3-blue.svg" alt="License: GPL v3"></a>
</p>
</div>

## Overview

Unicommerce for ERPNext connects ERPNext with marketplaces managed through
[Unicommerce Uniware](https://unicommerce.com/). It brings catalogue, inventory,
order, invoice, fulfilment, cancellation, and return workflows into ERPNext while
preserving Unicommerce identifiers on the relevant transactions.

This app depends on [`ecommerce_core`](https://github.com/aerele/ecommerce-core),
which provides shared ecommerce item mapping, integration logs, scheduling, and
inventory utilities.

## Key Features

| Workflow | Direction | What the app does |
| --- | --- | --- |
| Item catalogue | ERPNext → Unicommerce | Uploads selected ERPNext Items and updates existing Unicommerce SKUs. Items missing while importing an order can also be created in ERPNext. |
| Inventory | ERPNext → Unicommerce | Pushes whole-number stock levels from mapped ERPNext Warehouses to Unicommerce facilities. |
| Sales orders | Unicommerce → ERPNext | Imports new or date-range historical orders from enabled channels and creates the required customers and items. |
| Invoices and fulfilment | Two-way workflow | Imports completed invoices or generates invoices and shipping labels from ERPNext, depending on the configured workflow. |
| Delivery notes | Unicommerce → ERPNext | Optionally creates Delivery Notes when shipments are processed in Unicommerce. |
| Status, cancellations, and returns | Unicommerce → ERPNext | Updates order and package status, handles full or partial cancellations, and creates draft return Credit Notes for RTO and customer-initiated returns. |
| Shipment manifests | ERPNext → Unicommerce | Creates and closes manifests, marks packages as dispatched, and attaches the manifest PDF in ERPNext. |
| Goods receipt (GRN) | ERPNext → Unicommerce | Optionally uploads Material Transfer Stock Entries through the Unicommerce Auto GRN API, including configured batch attributes. |

Synchronization runs through Frappe background jobs. Results and failures are
recorded in **Ecommerce Integration Log** for monitoring and retry.

## Compatibility

| Component | Supported version |
| --- | --- |
| Python | 3.10 or later |
| Frappe Framework | `>=16.0.0-dev, <=17.0.0-dev` |
| ERPNext | `>=16.0.0-dev, <=17.0.0-dev` |
| Unicommerce | `develop` |
| Ecommerce Core | Matching `develop` branch |

## Installation

You need an existing Bench with Frappe Framework and ERPNext. From the bench
directory, get the dependency and this app:

```bash
bench get-app ecommerce_core https://github.com/aerele/ecommerce-core.git --branch develop
bench get-app unicommerce https://github.com/aerele/unicommerce.git --branch develop
```

Install both apps on your site in dependency order:

```bash
bench --site <site-name> install-app ecommerce_core
bench --site <site-name> install-app unicommerce
```

Replace `<site-name>` with your site, for example `erp.example.com`.

## Configuration

Complete the ERPNext setup wizard and ensure that the scheduler and background
workers are running before enabling synchronization.

### 1. Connect Unicommerce

Open **Unicommerce Settings** from the Desk search bar, then:

1. Select **Enable Unicommerce**.
2. Enter the Unicommerce site hostname without `https://`, your username,
   password, and client ID.
3. Set the default Customer Group and Sales Order and Sales Invoice naming
   series.
4. Save the document. Successful authentication populates the read-only access
   token, refresh token, token type, and expiry fields.

If authentication fails, verify the credentials and ask Unicommerce support
whether the ERPNext server IP must be allowlisted.

### 2. Map warehouses

In **Warehouse Mapping**, add one row for each Unicommerce facility:

- Map the facility code to an ERPNext Warehouse.
- Select the Return Warehouse used for returns and credit notes.
- Set Company and Dispatch Addresses where required.
- Enable each mapping that should participate in synchronization.

Mappings must be unique and one-to-one. Inventory in ERPNext is treated as the
source of truth. The integration sends whole-number quantities to the `DEFAULT`
shelf in Unicommerce.

### 3. Configure sales channels

Create one **Unicommerce Channel** document for each channel ID to import. Set
the Company, default Warehouse, Customer Group, Cost Center, tax and charge
accounts, payment settings, naming series, and shipping responsibility. Enable
the channel only after all mandatory accounting defaults are complete.

Only orders belonging to enabled channels are imported. Facility mappings select
the ERPNext Warehouse used for their line items and inventory updates.

### 4. Enable the required workflows

- **Item sync:** Enable **Upload new items to Unicommerce**, set a Default Item
  Group, and select **Sync Item with Unicommerce** on each Item to upload.
- **Inventory sync:** Enable it, choose a sync frequency, and enable the required
  warehouse mappings.
- **Completed-order workflow:** Enable **Only Sync Completed Orders** to import
  orders and their invoices after processing is complete in Unicommerce.
- **ERPNext fulfilment workflow:** Leave the completed-order option disabled,
  then generate invoices from a synced Sales Order or Pick List and create a
  Unicommerce Shipment Manifest before dispatch.
- **Delivery Notes:** Enable **Import Delivery Notes from Unicommerce on
  Shipment** when fulfilment happens in Unicommerce.
- **Auto GRN:** Enable **Use Stock Entry for GRN**, enter the vendor code, and
  configure every Unicommerce batch group and its required attributes.

For field mappings and illustrated workflows, see the
[Unicommerce integration guide](https://integrations.frappe.cloud/integrations/ecommerce-integration/unicommerce/overview).

## Operations

- Use **Last Order Sync** and **Last Inventory Sync** in Unicommerce Settings to
  verify scheduler activity.
- Review **Ecommerce Integration Log** for request details, failures, and retries.
- Do not change an ERPNext Item Code after it has been mapped to a Unicommerce
  SKU; Unicommerce SKU codes are immutable.
- Configure the ERPNext scheduler and long workers. Order and inventory jobs are
  checked every five minutes and run according to their configured frequencies;
  item uploads and status updates run hourly.

## Development

Set up a Frappe bench with matching `develop` branches, install the apps as shown
above, and enable developer mode on the test site:

```bash
bench --site <site-name> set-config developer_mode 1
bench --site <site-name> migrate
```

Run the server tests from the bench directory:

```bash
bench --site <site-name> run-tests --app unicommerce
```

Install and run the repository checks before opening a pull request:

```bash
cd apps/unicommerce
pre-commit install
pre-commit run --all-files
```

## Contributing

Contributions are welcome. Please open an
[issue](https://github.com/aerele/unicommerce/issues) for bugs or proposed
changes, keep pull requests focused, add tests for changed behaviour, and target
the `develop` branch.

## License

This project is licensed under the [GNU General Public License v3.0](license.txt).

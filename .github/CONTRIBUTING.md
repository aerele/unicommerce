### Introduction (For First-Time Contributors)

Thank you for your interest in raising an issue with Unicommerce for ERPNext. An issue can be either a bug report or a feature request.

By reporting bugs, you contribute directly to improving the integration. Bug reports help developers identify and fix issues quickly before they affect more users.

Feature requests are also valuable. They help shape the future of the product by introducing new ideas and improvements based on real-world use cases.

When raising an issue, keep in mind that developers do not have access to your environment. Therefore, provide as much relevant information as possible.

If you are suggesting a feature, clearly describe what you expect and how it should behave.

> ⚠️ The issue tracker is not the right place for general questions or discussions.
> Please use the forum instead: https://discuss.frappe.io

---

### Reply and Closing Policy

If your issue is unclear or does not meet the guidelines, it may be closed.

If that happens, please provide the requested information and reopen the issue.

---

### General Issue Guidelines

1. **Search existing issues:**
   Before creating a new issue, check if it already exists. You can support existing issues with a 👍 or contribute additional details or mockups.

2. **Report issues separately:**
   Do not combine multiple unrelated issues into a single report.

3. **Be concise:**
   Avoid long explanations. Use bullet points and screenshots where possible.

4. **Redact credentials:**
   Unicommerce Settings holds a username, password, client ID, and access tokens. Remove them from screenshots, log output, and API payloads before attaching anything.

---

### Bug Report Guidelines

1. **Steps to reproduce:**
   Clearly list the steps required to reproduce the issue. If the issue cannot be reproduced, it cannot be fixed.

2. **Version numbers:**
   Include the Frappe, ERPNext, Ecommerce Core, and Unicommerce versions. The issue may already be fixed in a newer release.

3. **Clear title:**
   Use a descriptive title (e.g., "Sales Order not created for cancelled Unicommerce order" instead of "Sync not working").

4. **Screenshots:**
   Add screenshots or screen recordings (e.g., `.gif`) to illustrate the issue.

5. **Ecommerce Integration Log:**
   Most sync failures are recorded there. Attach the relevant log entry, including the request and the traceback.

---

### Feature Request Guidelines

1. **Clarity:**
   Clearly describe the expected behavior. Avoid vague statements.

2. **Proposed solution:**
   Suggest how the feature should work.

3. **Mockups:**
   Provide mockups or examples whenever possible.

---

### What if my issue is closed?

Don't worry. Review the feedback, provide the required information, and reopen the issue.

---

### Contributing Code

1. **Set up a bench** with matching `develop` branches of Frappe and ERPNext, install [`ecommerce_core`](https://github.com/aerele/ecommerce-core) followed by this app, and enable developer mode on your test site.

2. **Target the `develop` branch.** All pull requests are merged into `develop`.

3. **Run the tests** before opening a pull request:

   ```bash
   bench --site <site-name> run-tests --app unicommerce
   ```

4. **Run the linters.** This repository uses `pre-commit` with `ruff` and `prettier`:

   ```bash
   cd apps/unicommerce
   pre-commit install
   pre-commit run --all-files
   ```

5. **Keep pull requests focused** and add tests for changed behaviour.

6. **Do not commit credentials or customer data**, including Unicommerce API responses that contain customer names, addresses, or phone numbers.

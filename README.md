### Mold Management

Mold lifecycle and tooling management for ERPNext

This app is designed to stay isolated from standard ERPNext and other custom apps:

- No global `app_include_js`
- No standard controller overrides
- Standard custom fields are created and removed only by this app's install hooks
- Uninstall is blocked while mold business data is still active

### Installation

Install this app into an ERPNext v15 bench with the [bench](https://github.com/frappe/bench) CLI:

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app $URL_OF_THIS_REPO --branch main
bench install-app mold_management
```

### Production Deploy

Typical production install flow:

```bash
cd /home/frappe/frappe-bench
bench get-app https://github.com/<your-org-or-user>/mold_management.git --branch main
bench --site <your-site> install-app mold_management
bench --site <your-site> migrate
bench restart
```

Before uninstalling, remove mold business data first. This app intentionally blocks uninstall when submitted mold records, linked assets, or mold transaction data still exist.

### Contributing

This app uses `pre-commit` for code formatting and linting. Please [install pre-commit](https://pre-commit.com/#installation) and enable it for this repository:

```bash
cd apps/mold_management
pre-commit install
```

Pre-commit is configured to use the following tools for checking and formatting your code:

- ruff
- eslint
- prettier
- pyupgrade

### License

mit

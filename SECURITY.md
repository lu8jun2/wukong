# Security Policy

## Reporting

Do not file secrets, credentials, or private machine data in public issues. Share only sanitized reproductions.

## Public Release Rules

- never publish tokens, cookies, auth headers, or local secrets
- never publish private task dumps or machine state
- never publish private project outputs
- never publish live control documents from private projects
- fail closed on unavailable Product Design runtime with `BLOCKED_PRODUCT_DESIGN_PLUGIN_UNAVAILABLE`

## Verification

Run the local redaction scan before release packaging and keep evidence inside `release-evidence/` using relative paths only.


# Contributing

## Scope

- Keep Wukong coordinator-only.
- Keep worker execution and independent verification separate.
- Keep public text path-neutral and secret-free.
- Do not add claims that Product Design runtime is available unless you can prove it in public.

## Required Checks

```bash
python -m unittest discover -s tests -v
python scripts/redaction_scan.py --root . --out release-evidence/redaction-scan.json
python scripts/check_readme_links.py --root . --readme README.md --out release-evidence/readme-link-check.json
python <plugin-creator-root>/scripts/validate_plugin.py .
```

## Review Bar

- contract change explained
- tests updated when behavior changes
- redaction scan clean
- no private paths or machine state
- documentation updated when public behavior changes

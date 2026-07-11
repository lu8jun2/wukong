# macOS Install

1. Install Python 3.11+.
2. Copy or clone the bundle locally.
3. From the bundle root run:

```bash
python3 -m unittest discover -s tests -v
python3 scripts/redaction_scan.py --root . --out release-evidence/redaction-scan.json
python3 scripts/check_readme_links.py --root . --readme README.md --out release-evidence/readme-link-check.json
```

4. If you use Codex plugin validation locally, run the validator against this bundle root.


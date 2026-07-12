# macOS Install

1. Install Python 3.11+.
2. Copy or clone the bundle locally.
3. Verify the full role-reference tree exists:

```bash
test -f skills/multi-agent-wukong/references/team-roles.md
test -f skills/multi-agent-wukong/references/agency-agent-role-map.md
test -f skills/multi-agent-wukong/references/agency-agent-role-map.json
```

4. From the bundle root run:

```bash
python3 -m unittest discover -s tests -v
python3 scripts/redaction_scan.py --root . --out release-evidence/redaction-scan.json
python3 scripts/check_readme_links.py --root . --readme README.md --out release-evidence/readme-link-check.json
```

5. If you use Codex plugin validation locally, run the validator against this bundle root.
6. Treat a missing role-reference file as an invalid install; Wukong role selection depends on `team-roles.md` plus `agency-agent-role-map.md` and `agency-agent-role-map.json`.

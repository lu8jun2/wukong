# macOS Install

This public repository is a passive bundle until activation runs.

## Activate

```bash
python3 scripts/activate_wukong.py --codex-home ~/.codex
python3 scripts/activate_wukong.py --codex-home ~/.codex --verify
python3 scripts/activate_wukong.py --codex-home ~/.codex --project-root <project-root> --bootstrap-doc
python3 scripts/activate_wukong.py --codex-home ~/.codex --project-root <project-root> --verify
```

- `ACTIVATED` means the user skills were installed and the managed AGENTS block was merged.
- `VALIDATED` means the installed surface was checked without writing.
- Project activation requires `--project-root`.
- Missing project `AGENTS.md` or `docs/wukong/PROJECT-CONTROL.md` fails closed unless `--bootstrap-doc` is explicitly present.

## Validate

```bash
python3 -m unittest discover -s tests -v
python3 scripts/redaction_scan.py --root . --out release-evidence/redaction-scan.json
python3 scripts/check_readme_links.py --root . --readme README.md --out release-evidence/readme-link-check.json
```

The document-driven loop remains:

`PROJECT-CONTROL -> task package -> Subagent -> historian -> verifier -> update`

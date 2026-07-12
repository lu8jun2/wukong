# Wukong

Wukong is a coordinator contract and public Codex skill bundle. It is not an official OpenAI product.

## What This Bundle Ships

- `AGENTS.md`: the public activation contract that is merged into `~/.codex/AGENTS.md`
- `skills/wukong-always/`: the always-on activated entry skill
- `skills/multi-agent-wukong/`: the coordinator contract, routing rules, schemas, and local validators
- `skills/codex-history/`: the historian companion skill
- `docs/`: install notes, activation notes, and the public `PROJECT-CONTROL` template
- `examples/`: project bootstrap examples
- `tests/`: bundle, contract, activation, and gate tests

## Passive bundle vs activated install

This repository is a passive bundle until activation runs.

- Passive bundle: files exist locally, but Codex has not been wired to use them.
- ACTIVATED: `scripts/activate_wukong.py` has installed the user skills and merged the managed AGENTS block.
- VALIDATED: `scripts/activate_wukong.py --verify` confirmed the activated user/project surface without writing.

## Activation

### Windows

```powershell
python -X utf8 scripts/activate_wukong.py --codex-home ~/.codex
python -X utf8 scripts/activate_wukong.py --codex-home ~/.codex --verify
python -X utf8 scripts/activate_wukong.py --codex-home ~/.codex --project-root <project-root> --bootstrap-doc
python -X utf8 scripts/activate_wukong.py --codex-home ~/.codex --project-root <project-root> --verify
```

### macOS and Linux

```bash
python3 scripts/activate_wukong.py --codex-home ~/.codex
python3 scripts/activate_wukong.py --codex-home ~/.codex --verify
python3 scripts/activate_wukong.py --codex-home ~/.codex --project-root <project-root> --bootstrap-doc
python3 scripts/activate_wukong.py --codex-home ~/.codex --project-root <project-root> --verify
```

Project activation requires `--project-root`. If `AGENTS.md` or `docs/wukong/PROJECT-CONTROL.md` is missing, activation fails closed unless `--bootstrap-doc` is explicitly present.

## Document-Driven Loop

The activated operating loop is:

`PROJECT-CONTROL -> task package -> Subagent -> historian -> verifier -> update`

That means:

1. Wukong starts with dialogue, clarification, and user confirmation.
2. The live project control document is required before substantive work.
3. A task package carries authorization, control-document CAS, external capability evaluation, and no-recursion.
4. A Subagent executes the work.
5. The historian merges the handoff.
6. An independent verifier checks the result.
7. Wukong summarizes only after the historian merge and verifier evidence exist.

## Validation

Run the public checks from the bundle root:

```bash
python -m unittest discover -s tests -v
python scripts/redaction_scan.py --root . --out release-evidence/redaction-scan.json
python scripts/check_readme_links.py --root . --readme README.md --out release-evidence/readme-link-check.json
python scripts/build_manifest.py --root . --out release-evidence/MANIFEST.json
```

If you have a local plugin validator, run it against this bundle root after the test pass.

## Constraints

- Wukong is coordinator-only.
- Substantive work always goes to Subagents.
- Independent verification is required.
- Historian merge before final user summary is required.
- Chang'e design-start tasks stay fail-closed until Product Design invocation evidence exists.
- The public bundle stays path-neutral and secret-free.

## Project Bootstrap

Use [docs/PROJECT-CONTROL.template.md](docs/PROJECT-CONTROL.template.md) for the first live control document and [examples/project-AGENTS.example.md](examples/project-AGENTS.example.md) for the first project `AGENTS.md`. The activation script can create both only when `--bootstrap-doc` is explicitly requested.

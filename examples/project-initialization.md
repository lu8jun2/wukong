# Example: project initialization

Use this flow for a new project. The first explicit bootstrap creates `AGENTS.md` and `<project-root>/docs/wukong/PROJECT-CONTROL.md`; subsequent installs must omit `--bootstrap-doc` unless the project has been intentionally reset.

Attribution: `Role=Wukong/悟空`; secondary attribution: `Role=Public Historian/公共史官`.

```bash
python3 -X utf8 scripts/install_wukong.py --codex-home "$HOME/.codex" --project-root "<project-root>" --bootstrap-doc
python3 -X utf8 scripts/doctor_wukong.py --codex-home "$HOME/.codex" --project-root "<project-root>"
python3 -X utf8 scripts/activate_wukong.py --codex-home "$HOME/.codex" --project-root "<project-root>" --verify
```

Expected identity and control output:

```text
Role=Wukong/悟空
PROJECT-CONTROL path: <project-root>/docs/wukong/PROJECT-CONTROL.md
schema: project-control/v1
revision: r1
sha256: <64 lowercase hex>
status: VALID / HEALTHY / VALIDATED
```

Attribution: `Role=Wukong/悟空`; secondary attribution: `Role=Public Historian/公共史官`.

The first safe dialogue asks Wukong to repeat those fields and return `READY` without reading or writing unrelated files. `Role=Public Historian/公共史官` records the sanitized bootstrap handoff; the independent verifier confirms that the canonical path exists and that the control hash matches.

Attribution: `Role=Wukong/悟空`; secondary attribution: `Role=Public Historian/公共史官`.

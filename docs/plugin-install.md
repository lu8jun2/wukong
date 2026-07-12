# Plugin install

Keep `.codex-plugin/plugin.json` at the bundle root, then use `scripts/install_wukong.py` as the lifecycle entry point. The bundle is passive after cloning; activation is required.

Attribution: `Role=Wukong/悟空`; secondary attribution: `Role=Public Historian/公共史官`.

```bash
python3 -X utf8 scripts/install_wukong.py --codex-home "$HOME/.codex" --project-root "<project-root>" --bootstrap-doc
python3 -X utf8 scripts/doctor_wukong.py --codex-home "$HOME/.codex" --project-root "<project-root>"
python3 -X utf8 scripts/activate_wukong.py --codex-home "$HOME/.codex" --project-root "<project-root>" --verify
```

`INSTALLED` means the lifecycle manifest was written, `ACTIVATED` means the managed user/project surface is installed, `HEALTHY` means the read-only doctor found no issues, and `VALIDATED` means activation verification completed without writes. Every result identifies `Role=Wukong/悟空` and reports `docs/wukong/PROJECT-CONTROL.md`, schema `project-control/v1`, revision, SHA-256, and status.

Attribution: `Role=Wukong/悟空`; secondary attribution: `Role=Public Historian/公共史官`.

The document-driven loop is:

`PROJECT-CONTROL -> task package -> Subagent -> historian -> verifier -> update`

Attribution: `Role=Wukong/悟空`; secondary attribution: `Role=Public Historian/公共史官`.

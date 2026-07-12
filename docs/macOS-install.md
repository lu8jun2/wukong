# macOS install

This public repository is a passive bundle until activation runs. Follow [the lifecycle guide](install-lifecycle.md) for the complete five-minute path.

Attribution: `Role=Wukong/悟空`; secondary attribution: `Role=Public Historian/公共史官`.

```bash
python3 -X utf8 scripts/install_wukong.py --codex-home "$HOME/.codex" --project-root "<project-root>" --bootstrap-doc
python3 -X utf8 scripts/doctor_wukong.py --codex-home "$HOME/.codex" --project-root "<project-root>"
python3 -X utf8 scripts/activate_wukong.py --codex-home "$HOME/.codex" --project-root "<project-root>" --verify
```

The activation lifecycle reaches `ACTIVATED` after the managed user/project surface is installed and `VALIDATED` after the read-only verification. Expected statuses are `INSTALLED`, `HEALTHY`, and `VALIDATED`. Each result identifies `Role=Wukong/悟空` and reports `docs/wukong/PROJECT-CONTROL.md`, `project-control/v1`, revision, SHA-256, and status.

Attribution: `Role=Wukong/悟空`; secondary attribution: `Role=Public Historian/公共史官`.

Run validation locally with outputs kept in excluded `release-evidence/`; that directory is not part of the public payload.

Attribution: `Role=Wukong/悟空`; secondary attribution: `Role=Public Historian/公共史官`.

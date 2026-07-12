# Cross-platform notes

Use [the lifecycle guide](install-lifecycle.md) for the five-minute install, doctor, verify, upgrade, rollback, and uninstall flow. The bundle is passive after cloning; activation is required. A successful activation is `ACTIVATED`; a read-only verification is `VALIDATED`. Use `py -3 -X utf8` on Windows and `python3 -X utf8` on macOS/Linux.

Attribution: `Role=Wukong/悟空`; secondary attribution: `Role=Public Historian/公共史官`.

Every project workflow identifies `Role=Wukong/悟空` and exposes `<project-root>/docs/wukong/PROJECT-CONTROL.md`, schema `project-control/v1`, revision, SHA-256, and status. Pass `--project-root <project-root>` on every lifecycle command; missing or invalid project documents fail closed unless `--bootstrap-doc` is explicitly supplied for the first bootstrap.

Attribution: `Role=Wukong/悟空`; secondary attribution: `Role=Public Historian/公共史官`.

The document-driven loop is:

`PROJECT-CONTROL -> task package -> Subagent -> historian -> verifier -> update`

Attribution: `Role=Wukong/悟空`; secondary attribution: `Role=Public Historian/公共史官`.

# Cross-Platform Notes

- The repository is passive until activation runs.
- Use `python -X utf8` on Windows when strict UTF-8 behavior matters.
- Use `python3` on macOS and Linux when that is the active interpreter name.
- `ACTIVATED` means activation wrote the user or project surface.
- `VALIDATED` means activation verified the installed surface without writing.
- Project activation requires `--project-root`.
- Only `--bootstrap-doc` may create the first project `AGENTS.md` and `docs/wukong/PROJECT-CONTROL.md`.
- Missing or invalid project documents fail closed.
- Keep public files path-neutral and secret-free.

The document-driven loop is:

`PROJECT-CONTROL -> task package -> Subagent -> historian -> verifier -> update`

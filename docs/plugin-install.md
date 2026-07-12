# Plugin Install

This repository is a passive bundle until activation runs.

## Local Install Flow

1. Keep `.codex-plugin/plugin.json` at the bundle root.
2. Activate the bundle:

```bash
python scripts/activate_wukong.py --codex-home ~/.codex
python scripts/activate_wukong.py --codex-home ~/.codex --verify
python scripts/activate_wukong.py --codex-home ~/.codex --project-root <project-root> --bootstrap-doc
```

3. Load the bundle through your local Codex plugin workflow.
4. Re-run the tests after any contract change.

`ACTIVATED` means the user surface was written. `VALIDATED` means the existing surface passed verification without writes.

The document-driven loop is:

`PROJECT-CONTROL -> task package -> Subagent -> historian -> verifier -> update`

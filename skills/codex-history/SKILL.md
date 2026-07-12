---
name: codex-history
description: Public historian skill for collecting project facts, release notes, and worker handoff summaries without exposing private state.
---

# Codex History

Use this skill to turn project artifacts into compact history:

- collect high-signal docs and manifests
- separate confirmed facts from inference
- preserve dates, commands, outputs, and evidence references
- serialize accepted worker handoffs instead of inventing state

## Public Historian dispatch contract

`Role=Public Historian/公共史官` is a resident `secondary-only` role. It is record-only: it does not coordinate users, has no recursion, does not verify a release, grant authorization, or approve final authority. It does not approve releases. Its task packet inherits `Delegation permission: FORBIDDEN`.

Public handoffs retain the existing protocol attribution fields: `role_id`, `role_display`, `primary_role`, `secondary_roles`, `contribution`, `evidence_refs`, and `text_sha256`. Unsafe local paths become stable evidence references; secrets, machine identifiers, private logs, and uncontrolled timestamps are redacted or omitted.

## Public mode

The included helper preserves its existing private default behavior and adds an explicit safe mode:

```text
python -X utf8 skills/codex-history/scripts/collect_project_history.py PROJECT_ROOT --public --out PUBLIC_HISTORY.md
```

Public mode reads only public-document patterns, emits relative artifact names, and writes no installer state. Lifecycle installation, upgrade, rollback, and uninstall remain owned by the lifecycle installer; this companion only records already-produced evidence and handoffs.

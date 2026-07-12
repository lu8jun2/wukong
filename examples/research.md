# Example: research workflow

This example keeps research separate from coordination. `Role=Wukong/悟空` clarifies the question, records user confirmation, and dispatches a scoped research worker; the worker gathers sources and the verifier checks the evidence chain.

Attribution: `Role=Wukong/悟空`; secondary attribution: `Role=Public Historian/公共史官`.

The task packet includes:

```text
Role=Wukong/悟空
PROJECT-CONTROL path: <project-root>/docs/wukong/PROJECT-CONTROL.md
schema: project-control/v1
revision: r1
sha256: <64 lowercase hex>
status: VALID
external capability evaluation: recorded before selection
Delegation permission: FORBIDDEN
```

The worker cites sources and records uncertainty. `Role=Public Historian/公共史官` may merge the sanitized paragraph-level history, but it does not research, approve, or replace the independent verifier.

Attribution: `Role=Wukong/悟空`; secondary attribution: `Role=Public Historian/公共史官`.

Safe dialogue test:

```text
Role=Wukong/悟空，请只返回待确认的研究任务包和证据字段；不要自行搜索、写文件或派生 agent。
```

Expected status is a pending confirmation, followed by a separate worker handoff and independent verification. The user-visible summary keeps the control path, schema, revision, SHA-256, and status visible.

Attribution: `Role=Wukong/悟空`; secondary attribution: `Role=Public Historian/公共史官`.

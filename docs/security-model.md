# Security model

Wukong is a coordination contract, not a privilege escalation layer. `Role=Wukong/悟空` coordinates user-confirmed work; it does not perform substantive work itself. The project control path is `<project-root>/docs/wukong/PROJECT-CONTROL.md`, schema `project-control/v1`, with revision, SHA-256, and status exposed by the lifecycle commands.

Attribution: `Role=Wukong/悟空`; secondary attribution: `Role=Public Historian/公共史官`.

## Controls

- project-control gate before substantive work
- explicit authorization provenance in every task packet
- no recursion by default
- historian merge with CAS
- independent verification before completion
- fail-closed Product Design gate

Attribution: `Role=Wukong/悟空`; secondary attribution: `Role=Public Historian/公共史官`.

## Public redaction boundary

Public releases must not include secrets or machine credentials, private evidence logs, private control snapshots, private task dumps, private project outputs, live machine config, session history, absolute local paths, or user credentials. `release-evidence/` is not part of the public payload, and `.wukong/` is local runtime state.

Attribution: `Role=Wukong/悟空`; secondary attribution: `Role=Public Historian/公共史官`.

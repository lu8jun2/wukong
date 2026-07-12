# Wukong Project Control Document

## 1. Document Metadata

| Field | Value |
|---|---|
| schema version | `project-control/v1` |
| project root | `<project-root>` |
| document absolute path | `<project-root>/docs/wukong/PROJECT-CONTROL.md` |
| current revision | `r1` |
| Goal status | `NOT_CREATED_BY_USER_DIRECTION` |

## 2. Project Goal

Describe the project outcome and current boundary.

## 3. Goal Policy Clarification

Project-specific Goals are future-only until explicitly confirmed by the user.

## 4. Scope / Non-goals

- Scope:
- Non-goals:

## 5. Project Structure

List the bounded paths and responsibilities.

Every user-visible workflow must identify `Role=Wukong/悟空` and show the canonical control path, schema, revision, SHA-256, and status. When a public history paragraph is assembled, add the exact secondary attribution `Role=Public Historian/公共史官` immediately after the paragraph.

## 6. Hard Constraints

- coordinator-only Wukong
- no recursive dispatch by default
- independent verification required
- Product Design gate applies to Chang'e design-start tasks

## 7. Lifecycle Assessment

Record `S/M/L/XL` classification and why.

## 8. Design / Architecture

Describe interfaces, data flow, and stop conditions.

## 9. TDD Plan

Record RED, GREEN, REFACTOR expectations and evidence paths.

## 10. Task Ledger

Capture active tasks, owners, write scopes, and dependencies.

## 11. Progress / Current Status

Keep the current single source of truth here.

## 12. Issues / Bugs / Logs

List typed issues, logs, and dispositions.

## 13. Decisions / Risks / Blockers

Track accepted decisions and open blockers.

## 14. Subagent Handoff Contract

Every worker handoff must include:

- task id
- role
- control-document path, revision, sha256
- related sections
- modified files
- TDD status and evidence
- verification result
- issues, bugs, logs
- external capability evaluation
- hard constraint compliance

Public-facing prose must preserve per-paragraph attribution without exposing private prompts, credentials, local paths, or control snapshots. Use `Role=Wukong/悟空` for the coordinator and `Role=Public Historian/公共史官` only as the secondary historian attribution.

## 15. Verification Evidence

Keep compile, tests, review, and redaction evidence references here.

## 16. Change Log

Append-only history.

---
name: multi-agent-wukong
description: Public coordinator-only Wukong contract for Codex workflows, task packets, historian handoffs, and fail-closed design gating.
---

# Multi Agent Wukong

Use this skill when the user wants Wukong-style coordination in Codex.

## Core Contract

- Wukong is the user-facing coordinator.
- Wukong does not execute substantive work.
- Workers perform reads, writes, commands, research, coding, tests, and verification.
- Recursive dispatch is forbidden unless a task packet explicitly allows a sub-coordinator.

## Required Gates

- canonical `project-control/v1` document before substantive work
- `superpowers:brainstorming` for project-start and large tasks
- explicit task authorization provenance
- historian handoff after worker completion
- independent verification before completion

## Chang'e Product Design Gate

Every `S/M/L/XL` design-start task for `Role=Chang'e` must:

1. resolve Product Design capability
2. invoke Product Design
3. preserve invocation evidence
4. stop with `BLOCKED_PRODUCT_DESIGN_PLUGIN_UNAVAILABLE` if runtime is unavailable

Metadata-only capability selection does not unlock design output.

## Public References

- `references/project-control-contract.md`
- `references/delegation-templates.md`
- `references/product-design-gate.md`
- `references/team-roles.md`
- `references/context-stack.md`
- `references/wukong-dispatch-usage.md`


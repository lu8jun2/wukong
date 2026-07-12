# Wukong

> A coordinator-only public bundle that makes Wukong/悟空 visible, auditable, and safe to install in five minutes.

Attribution: `Role=Wukong/悟空`; secondary attribution: `Role=Public Historian/公共史官`; control reference: `docs/wukong/PROJECT-CONTROL.md`, schema `project-control/v1`, revision `r1`, SHA-256 recorded by the installer, status reported by `doctor_wukong.py`.

Wukong is a community/public Codex workflow bundle, not an official OpenAI product. Wukong coordinates dialogue, confirmation, dispatch, dependency tracking, and evidence summaries; scoped Subagents perform substantive work, and an independent verifier checks completion. This is the five-minute install path.

Attribution: `Role=Wukong/悟空`; secondary attribution: `Role=Public Historian/公共史官`.

## Passive bundle vs activated install

This repository is a passive bundle until activation runs.

- Passive bundle: files exist locally, but Codex has not been wired to use them.
- `ACTIVATED`: `scripts/activate_wukong.py` has installed the user skills and merged the managed AGENTS block.
- `VALIDATED`: `scripts/activate_wukong.py --verify` confirmed the activated user/project surface without writing.

Windows activation command: `python -X utf8 scripts/activate_wukong.py --codex-home "$HOME/.codex" --project-root "<project-root>" --bootstrap-doc`.

Attribution: `Role=Wukong/悟空`; secondary attribution: `Role=Public Historian/公共史官`.

## Document-driven loop

The activated operating loop is:

`PROJECT-CONTROL -> task package -> Subagent -> historian -> verifier -> update`

Wukong confirms and dispatches; the live project control document gates substantive work; the Public Historian merges the sanitized handoff before an independent verifier confirms completion.

Attribution: `Role=Wukong/悟空`; secondary attribution: `Role=Public Historian/公共史官`.

## Five-minute quickstart

The shortest supported path is: clone the bundle, run `scripts/install_wukong.py`, bootstrap a project control document, run the read-only doctor and activation verification, then perform one safe dialogue test. clone alone is passive; activation is required before Codex uses the Wukong contract.

Attribution: `Role=Wukong/悟空`; secondary attribution: `Role=Public Historian/公共史官`.

### 1. Clone the passive bundle

```bash
git clone <public-repository-url> wukong
cd wukong
```

Attribution: `Role=Wukong/悟空`; secondary attribution: `Role=Public Historian/公共史官`.

### 2. Install and bootstrap a project

Use Python 3.10 or newer. Replace `<project-root>` with the project you want Wukong to coordinate.

Attribution: `Role=Wukong/悟空`; secondary attribution: `Role=Public Historian/公共史官`.

| Host | Install command |
|---|---|
| Windows PowerShell | `py -3 -X utf8 scripts/install_wukong.py --codex-home "$HOME/.codex" --project-root "<project-root>" --bootstrap-doc` |
| macOS | `python3 -X utf8 scripts/install_wukong.py --codex-home "$HOME/.codex" --project-root "<project-root>" --bootstrap-doc` |
| Linux | `python3 -X utf8 scripts/install_wukong.py --codex-home "$HOME/.codex" --project-root "<project-root>" --bootstrap-doc` |

`--bootstrap-doc` is the explicit permission to create the first project `AGENTS.md` and `docs/wukong/PROJECT-CONTROL.md`. Without it, a project with missing control documents fails closed.

Attribution: `Role=Wukong/悟空`; secondary attribution: `Role=Public Historian/公共史官`.

Expected result is JSON with `status: "INSTALLED"`, `identity.name: "Wukong"`, and a `project_control` object containing:

```json
{
  "path": "<project-root>/docs/wukong/PROJECT-CONTROL.md",
  "schema": "project-control/v1",
  "revision": "r1",
  "sha256": "<64 lowercase hex>",
  "status": "VALID"
}
```

Attribution: `Role=Wukong/悟空`; secondary attribution: `Role=Public Historian/公共史官`.

### 3. Doctor and verify without writing

```bash
python3 -X utf8 scripts/doctor_wukong.py --codex-home "$HOME/.codex" --project-root "<project-root>"
python3 -X utf8 scripts/activate_wukong.py --codex-home "$HOME/.codex" --project-root "<project-root>" --verify
```

On Windows, use `py -3 -X utf8` in place of `python3 -X utf8`. The doctor reports `status: "HEALTHY"`; activation verification reports `status: "VALIDATED"` and `writes: []`. Both outputs repeat the Wukong identity and the control path, schema, revision, SHA-256, and status.

Attribution: `Role=Wukong/悟空`; secondary attribution: `Role=Public Historian/公共史官`.

### 4. Run the first safe dialogue test

In a fresh Codex conversation, send this read-only prompt:

```text
Role=Wukong/悟空，请只做安全自检：返回 READY，并复述
PROJECT-CONTROL 的 path、schema、revision、sha256、status；说明你不会直接执行实质工作，
不会读取或写入其他项目文件，也不会递归派发 agent。
```

Expected response: `Role=Wukong/悟空`, `READY`, the canonical path `docs/wukong/PROJECT-CONTROL.md`, schema `project-control/v1`, a revision, a 64-character SHA-256, and status `VALID` or `HEALTHY`. If the response claims to have changed files or dispatches recursively, stop and run the doctor again.

Attribution: `Role=Wukong/悟空`; secondary attribution: `Role=Public Historian/公共史官`.

## Lifecycle operations

The complete upgrade, rollback, uninstall, residual-file, compatibility, privacy, and troubleshooting policy is in [docs/install-lifecycle.md](docs/install-lifecycle.md). It defines the exact statuses `INSTALLED`, `UPGRADED`, `ROLLED_BACK`, and `UNINSTALLED`, plus the explicit `PROJECT-CONTROL` purge token.

Attribution: `Role=Wukong/悟空`; secondary attribution: `Role=Public Historian/公共史官`.

### Upgrade, rollback, and uninstall commands

```bash
# Upgrade from the new bundle, preserving the same Codex home and project.
python3 -X utf8 scripts/install_wukong.py --codex-home "$HOME/.codex" --project-root "<project-root>"

# Roll back the most recent upgrade from its owned hash backup.
python3 -X utf8 scripts/install_wukong.py --codex-home "$HOME/.codex" --project-root "<project-root>" --rollback

# Safe uninstall: remove only Wukong-owned unchanged files and preserve the project control document.
python3 -X utf8 scripts/uninstall_wukong.py --codex-home "$HOME/.codex" --project-root "<project-root>"

# Optional destructive project-control purge; the exact token is mandatory.
python3 -X utf8 scripts/uninstall_wukong.py --codex-home "$HOME/.codex" --project-root "<project-root>" --purge-project-control --confirm-purge PROJECT-CONTROL
```

Expected statuses are `UPGRADED`, `ROLLED_BACK`, `UNINSTALLED`, and, only for the final command, `project_control.status: "PURGED"`. The project-control path, schema, revision, SHA-256, and status remain part of every JSON result.

Attribution: `Role=Wukong/悟空`; secondary attribution: `Role=Public Historian/公共史官`.

## Public payload and privacy boundary

The public payload is path-neutral and secret-free. `release-evidence/` is not part of the public payload; `.wukong/` is local runtime state and is never a release input. Private control snapshots, conversation history, credentials, machine identifiers, absolute local paths, and private project outputs must stay outside the public bundle.

Attribution: `Role=Wukong/悟空`; secondary attribution: `Role=Public Historian/公共史官`.

Use the allowlisted source tree and `scripts/build_manifest.py` for release review. The manifest excludes `release-evidence/`; a clean redaction scan and independent read-only verification are required before publication.

Attribution: `Role=Wukong/悟空`; secondary attribution: `Role=Public Historian/公共史官`.

## Examples

- [Software development workflow](examples/software-development.md)
- [Research workflow](examples/research.md)
- [Project initialization workflow](examples/project-initialization.md)
- [Project control template](docs/PROJECT-CONTROL.template.md)

Attribution: `Role=Wukong/悟空`; secondary attribution: `Role=Public Historian/公共史官`.

## Governance contracts

- Wukong is coordinator-only and never performs substantive work.
- Delegation is `FORBIDDEN` by default; no recursion is allowed without an explicit authorized packet.
- Every substantive task requires user confirmation before dispatch.
- Every worker handoff goes to the Public Historian, and completion requires an independent verifier that did not implement the change.
- Chang'e design-start tasks remain fail-closed until Product Design invocation evidence exists.

Attribution: `Role=Wukong/悟空`; secondary attribution: `Role=Public Historian/公共史官`.

## Validation

Run the public checks against the explicit public payload root. Keep validation output in a local, excluded `release-evidence/` directory; do not commit it. The payload root excludes `docs/wukong/PROJECT-CONTROL.md`, `release-evidence/`, caches, private snapshots, and test fixtures.

Attribution: `Role=Wukong/悟空`; secondary attribution: `Role=Public Historian/公共史官`.

```bash
python3 -X utf8 -m unittest discover -s tests -v
python3 -X utf8 scripts/redaction_scan.py --root <public-payload-root> --out release-evidence/redaction-scan.json
python3 -X utf8 scripts/check_readme_links.py --root . --readme README.md --out release-evidence/readme-link-check.json
python3 -X utf8 scripts/build_manifest.py --root . --out release-evidence/MANIFEST.json
```

Attribution: `Role=Wukong/悟空`; secondary attribution: `Role=Public Historian/公共史官`.

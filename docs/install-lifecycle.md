# Wukong installation lifecycle

This guide is the authoritative five-minute lifecycle for `Role=Wukong/悟空`. It covers a clean supported host, a project bootstrap, a read-only health check, a safe dialogue smoke test, upgrade, rollback, uninstall, privacy, and recovery. The public bundle is passive after cloning; activation is required.

Attribution: `Role=Wukong/悟空`; secondary attribution: `Role=Public Historian/公共史官`; control reference: `docs/wukong/PROJECT-CONTROL.md`, schema `project-control/v1`, revision `r1`, SHA-256 from the command output, status from the doctor.

## 1. Five-minute quickstart

Start in the cloned bundle root and choose the command for your host. The commands use only the standard Python interpreter and a writable Codex home; they do not start a daemon, open a port, or send project content to a remote service.

Attribution: `Role=Wukong/悟空`; secondary attribution: `Role=Public Historian/公共史官`.

| Host | Prerequisite | Command |
|---|---|---|
| Windows PowerShell | Python 3.10+ and `py -3` | `py -3 -X utf8 scripts/install_wukong.py --codex-home "$HOME/.codex" --project-root "<project-root>" --bootstrap-doc` |
| macOS | Python 3.10+ and `python3` | `python3 -X utf8 scripts/install_wukong.py --codex-home "$HOME/.codex" --project-root "<project-root>" --bootstrap-doc` |
| Linux | Python 3.10+ and `python3` | `python3 -X utf8 scripts/install_wukong.py --codex-home "$HOME/.codex" --project-root "<project-root>" --bootstrap-doc` |

Attribution: `Role=Wukong/悟空`; secondary attribution: `Role=Public Historian/公共史官`.

The first run creates the managed user surface, records `.wukong/install-state.json` in the Codex home, and bootstraps the project control surface only because `--bootstrap-doc` is present. Expected JSON includes `status: "INSTALLED"`, `identity.name: "Wukong"`, and this control record:

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

Run both read-only checks immediately:

```bash
# macOS/Linux; use py -3 -X utf8 on Windows.
python3 -X utf8 scripts/doctor_wukong.py --codex-home "$HOME/.codex" --project-root "<project-root>"
python3 -X utf8 scripts/activate_wukong.py --codex-home "$HOME/.codex" --project-root "<project-root>" --verify
```

Expected results are `status: "HEALTHY"` from the doctor and `status: "VALIDATED"` with `writes: []` from activation verification. Both results identify `Role=Wukong/悟空` through their `identity.name` and expose the control path, schema, revision, SHA-256, and status. The project control path is always `<project-root>/docs/wukong/PROJECT-CONTROL.md`; the schema is `project-control/v1`.

Attribution: `Role=Wukong/悟空`; secondary attribution: `Role=Public Historian/公共史官`.

## 2. First safe dialogue test

Open a fresh Codex conversation and send a read-only request that explicitly forbids file access, writes, and recursion:

```text
Role=Wukong/悟空，请只做安全自检：返回 READY，并复述
PROJECT-CONTROL 的 path、schema、revision、sha256、status；说明你不会直接执行实质工作，
不会读取或写入其他项目文件，也不会递归派发 agent。
```

Attribution: `Role=Wukong/悟空`; secondary attribution: `Role=Public Historian/公共史官`.

The expected response contains `Role=Wukong/悟空`, `READY`, `docs/wukong/PROJECT-CONTROL.md`, `project-control/v1`, a revision, a 64-character lowercase SHA-256, and a status such as `VALID` or `HEALTHY`. A response that claims direct substantive work or recursive dispatch is a failed smoke test; stop and rerun the doctor before continuing.

Attribution: `Role=Wukong/悟空`; secondary attribution: `Role=Public Historian/公共史官`.

## 3. Upgrade

Identity: `Role=Wukong/悟空`; `PROJECT-CONTROL.md` path `<project-root>/docs/wukong/PROJECT-CONTROL.md`; schema `project-control/v1`; revision `r1`; `sha256` `<64 lowercase hex>`; `status` `VALID` before upgrade.

Attribution: `Role=Wukong/悟空`; secondary attribution: `Role=Public Historian/公共史官`.

Run the installer from the newer bundle with the same Codex home and project root. Do not pass `--bootstrap-doc` for an already bootstrapped project.

```bash
python3 -X utf8 scripts/install_wukong.py --codex-home "$HOME/.codex" --project-root "<project-root>"
```

Attribution: `Role=Wukong/悟空`; secondary attribution: `Role=Public Historian/公共史官`.

Expected result is `status: "UPGRADED"` with an owned hash backup. The upgrade preserves supported user data and refuses to overwrite an edited Wukong-owned file; a conflict returns a `BLOCKED_OWNERSHIP_CONFLICT` status and leaves the prior bytes intact. The result repeats the control `path`, `schema`, `revision`, `sha256`, and `status` so the upgrade can be correlated with the project revision.

Attribution: `Role=Wukong/悟空`; secondary attribution: `Role=Public Historian/公共史官`.

After an upgrade, run the doctor and activation verification from the quickstart. Do not delete the installer-owned backup directory until the new release is accepted.

Attribution: `Role=Wukong/悟空`; secondary attribution: `Role=Public Historian/公共史官`.

## 4. Rollback

Identity: `Role=Wukong/悟空`; `PROJECT-CONTROL.md` path `<project-root>/docs/wukong/PROJECT-CONTROL.md`; schema `project-control/v1`; revision `r1`; `sha256` `<64 lowercase hex>`; `status` `VALID` before rollback.

Attribution: `Role=Wukong/悟空`; secondary attribution: `Role=Public Historian/公共史官`.

Rollback uses the most recent installer-owned backup and checks hashes before changing files:

```bash
python3 -X utf8 scripts/install_wukong.py --codex-home "$HOME/.codex" --project-root "<project-root>" --rollback
```

Attribution: `Role=Wukong/悟空`; secondary attribution: `Role=Public Historian/公共史官`.

Expected result is `status: "ROLLED_BACK"` and the previous release identity. If a managed file was edited after the upgrade, rollback fails closed with `BLOCKED_ROLLBACK_CONFLICT`; preserve the evidence and resolve the user edit instead of forcing deletion. The rollback result still exposes control `path`, `schema`, `revision`, `sha256`, and `status`.

Attribution: `Role=Wukong/悟空`; secondary attribution: `Role=Public Historian/公共史官`.

## 5. Uninstall

Identity: `Role=Wukong/悟空`; `PROJECT-CONTROL.md` path `<project-root>/docs/wukong/PROJECT-CONTROL.md`; schema `project-control/v1`; revision `r1`; `sha256` `<64 lowercase hex>`; `status` `VALID` before uninstall.

Attribution: `Role=Wukong/悟空`; secondary attribution: `Role=Public Historian/公共史官`.

The default uninstall removes only unchanged Wukong-owned skills, the managed home `AGENTS.md` block, installer state, and owned backups. It preserves the project control document and any user edits.

```bash
python3 -X utf8 scripts/uninstall_wukong.py --codex-home "$HOME/.codex" --project-root "<project-root>"
```

Attribution: `Role=Wukong/悟空`; secondary attribution: `Role=Public Historian/公共史官`.

Expected result is `status: "UNINSTALLED"` and `project_control.status: "PRESERVED"`. The JSON still identifies Wukong and shows control `path`, `schema`, `revision`, `sha256`, and status. If an owned file or managed marker was edited, uninstall returns a blocking conflict and leaves that surface untouched.

Attribution: `Role=Wukong/悟空`; secondary attribution: `Role=Public Historian/公共史官`.

To remove the project control document as well, use the explicit purge token only after saving any required project history:

```bash
python3 -X utf8 scripts/uninstall_wukong.py --codex-home "$HOME/.codex" --project-root "<project-root>" --purge-project-control --confirm-purge PROJECT-CONTROL
```

The token must be exactly `PROJECT-CONTROL`. A missing or different token returns `BLOCKED_PURGE_CONFIRMATION_REQUIRED` and performs no cleanup. Purge is limited to the canonical `<project-root>/docs/wukong/PROJECT-CONTROL.md`; it does not delete arbitrary project files.

Attribution: `Role=Wukong/悟空`; secondary attribution: `Role=Public Historian/公共史官`.

## 6. Residual-file policy

Identity: `Role=Wukong/悟空`; `PROJECT-CONTROL.md` path `<project-root>/docs/wukong/PROJECT-CONTROL.md`; schema `project-control/v1`; revision `r1`; `sha256` `<64 lowercase hex>`; `status` `PRESERVED` by default or `PURGED` with the exact token.

Attribution: `Role=Wukong/悟空`; secondary attribution: `Role=Public Historian/公共史官`.

“No residue” means no Wukong-owned runtime surface remains after a successful default uninstall: no installed skill directories, managed home contract block, `.wukong/install-state.json`, or owned backup directory. The cloned bundle is not installer-owned and may be removed separately by the user.

Attribution: `Role=Wukong/悟空`; secondary attribution: `Role=Public Historian/公共史官`.

The default policy intentionally retains `<project-root>/docs/wukong/PROJECT-CONTROL.md` as user/project history and retains user-edited `AGENTS.md` content. Use the exact purge token for the control document only. The scripts create no service, listener, scheduled task, or hidden cache.

Attribution: `Role=Wukong/悟空`; secondary attribution: `Role=Public Historian/公共史官`.

## 7. Compatibility matrix

Identity: `Role=Wukong/悟空`; `PROJECT-CONTROL.md` path `<project-root>/docs/wukong/PROJECT-CONTROL.md`; schema `project-control/v1`; revision `r1`; `sha256` `<64 lowercase hex>`; `status` is returned in JSON on every supported host.

Attribution: `Role=Wukong/悟空`; secondary attribution: `Role=Public Historian/公共史官`.

| Surface | Windows | macOS | Linux |
|---|---|---|---|
| Interpreter | Python 3.10+ via `py -3` | Python 3.10+ via `python3` | Python 3.10+ via `python3` |
| Shell example | PowerShell | Terminal | POSIX shell |
| Codex home | `$HOME/.codex` | `$HOME/.codex` | `$HOME/.codex` |
| Project root | Any writable path | Any writable path | Any writable path |
| Lifecycle result | JSON on stdout; non-zero only for blocked states | Same | Same |

Attribution: `Role=Wukong/悟空`; secondary attribution: `Role=Public Historian/公共史官`.

The scripts use only the Python standard library. `git` is needed to clone the public bundle, but no GitHub credential, API key, or network call is needed by the local lifecycle commands after cloning. The public release describes support at the script contract level; verify the actual interpreter with `python --version` or `py -3 --version` before a timed run.

Attribution: `Role=Wukong/悟空`; secondary attribution: `Role=Public Historian/公共史官`.

## 8. Privacy and redaction

Identity: `Role=Wukong/悟空`; `PROJECT-CONTROL.md` path `<project-root>/docs/wukong/PROJECT-CONTROL.md`; schema `project-control/v1`; revision `r1`; `sha256` is the control CAS field; `status` must be visible without exposing private snapshots.

Attribution: `Role=Wukong/悟空`; secondary attribution: `Role=Public Historian/公共史官`.

The public payload is an allowlisted source bundle. `release-evidence/` is not part of the public payload, `.wukong/` is local runtime state, and private control snapshots must never be copied into the release tree. The payload must not contain credentials, tokens, cookies, private URLs, absolute local paths, machine identifiers, conversation history, private task dumps, or private project outputs.

Attribution: `Role=Wukong/悟空`; secondary attribution: `Role=Public Historian/公共史官`.

Run the redaction scanner and build the manifest for a release review. Keep their outputs in the excluded `release-evidence/` directory and do not publish the directory itself. The independent verifier checks the resulting allowlist, hashes, and absence of private control snapshots before approval.

Attribution: `Role=Wukong/悟空`; secondary attribution: `Role=Public Historian/公共史官`.

## 9. Troubleshooting

Identity: `Role=Wukong/悟空`; `PROJECT-CONTROL.md` path `<project-root>/docs/wukong/PROJECT-CONTROL.md`; schema `project-control/v1`; revision, `sha256`, and `status` are the first fields to compare when a command is blocked.

Attribution: `Role=Wukong/悟空`; secondary attribution: `Role=Public Historian/公共史官`.

**Clone appears to do nothing.** That is expected: clone alone is passive. Run `scripts/install_wukong.py`; then run `scripts/doctor_wukong.py` and `scripts/activate_wukong.py --verify`.

Attribution: `Role=Wukong/悟空`; secondary attribution: `Role=Public Historian/公共史官`.

**`BLOCKED_PROJECT_DOCS_MISSING`.** Supply `--project-root` and add `--bootstrap-doc` only for the first project bootstrap. Confirm that `<project-root>/docs/wukong/PROJECT-CONTROL.md` exists and has schema `project-control/v1`.

Attribution: `Role=Wukong/悟空`; secondary attribution: `Role=Public Historian/公共史官`.

**Doctor reports `DEGRADED` or control `CONFLICT`.** Do not reinstall over the conflict. Compare the recorded and current control `sha256`, inspect the reported `path`, and preserve the project revision before deciding whether to restore or accept a controlled change.

Attribution: `Role=Wukong/悟空`; secondary attribution: `Role=Public Historian/公共史官`.

**`BLOCKED_OWNERSHIP_CONFLICT` or `BLOCKED_ROLLBACK_CONFLICT`.** A managed file changed after installation. Keep the user edit, copy it to a user-owned location if needed, and retry only after resolving the ownership decision.

Attribution: `Role=Wukong/悟空`; secondary attribution: `Role=Public Historian/公共史官`.

**`BLOCKED_PURGE_CONFIRMATION_REQUIRED`.** The purge flag requires the exact case-sensitive token `PROJECT-CONTROL`. Without it, the command intentionally performs no cleanup.

Attribution: `Role=Wukong/悟空`; secondary attribution: `Role=Public Historian/公共史官`.

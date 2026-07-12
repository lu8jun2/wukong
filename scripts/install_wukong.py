from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_CONTROL_RELATIVE = Path("docs") / "wukong" / "PROJECT-CONTROL.md"
STATE_RELATIVE = Path(".wukong") / "install-state.json"
BACKUPS_RELATIVE = Path(".wukong") / "backups"
STATE_FORMAT = "wukong-install-state/v1"
IDENTITY_NAME = "Wukong"
PACKAGE_NAME = "wukong-public-staging"
LEGACY_BEGIN = "<!-- WUKONG_PUBLIC_CONTRACT:BEGIN -->"
LEGACY_END = "<!-- WUKONG_PUBLIC_CONTRACT:END -->"
SENTINEL_BEGIN = LEGACY_BEGIN
SENTINEL_END = LEGACY_END
USER_SKILLS = ("wukong-always", "multi-agent-wukong", "codex-history")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load helper: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _activation_module():
    return _load_module(Path(__file__).resolve().with_name("activate_wukong.py"), "wukong_lifecycle_activation")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _default_bundle_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _default_codex_home() -> Path:
    configured = os.environ.get("CODEX_HOME")
    if configured:
        return Path(configured).expanduser().resolve()
    return (Path.home() / ".codex").resolve()


def _state_path(codex_home: Path) -> Path:
    return codex_home / STATE_RELATIVE


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json_atomic(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        Path(temporary).replace(path)
    finally:
        if Path(temporary).exists():
            Path(temporary).unlink()


def _bundle_version(bundle_root: Path) -> str:
    manifest = _read_json(bundle_root / ".codex-plugin" / "plugin.json")
    version = manifest.get("version") if isinstance(manifest, dict) else None
    if not isinstance(version, str) or not version.strip():
        raise ValueError("bundle plugin manifest has no version")
    return version.strip()


def _within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _block_from_text(text: str, begin: str = LEGACY_BEGIN, end: str = LEGACY_END) -> str | None:
    if text.count(begin) != 1 or text.count(end) != 1:
        return None
    start = text.index(begin)
    finish = text.index(end) + len(end)
    if finish < start:
        return None
    return text[start:finish]


def _marker_error(text: str) -> str | None:
    begin_count = text.count(LEGACY_BEGIN)
    end_count = text.count(LEGACY_END)
    if begin_count != end_count or begin_count > 1:
        return "BLOCKED_MANAGED_MARKER_CONFLICT"
    return None


def _managed_block(bundle_root: Path) -> str:
    activate = _activation_module()
    return activate._managed_block((bundle_root / "AGENTS.md").read_text(encoding="utf-8"))


def _control_status(bundle_root: Path, project_root: Path | None) -> dict[str, Any]:
    if project_root is None:
        return {
            "path": None,
            "schema": None,
            "revision": None,
            "sha256": None,
            "status": "NOT_REQUESTED",
        }
    path = (project_root / PROJECT_CONTROL_RELATIVE).resolve()
    gate = _activation_module()._load_gate(bundle_root)
    snapshot = gate.read_snapshot(str(path))
    if snapshot.get("valid") is False:
        status = "MISSING" if not path.exists() else "CONFLICT"
        return {
            "path": str(path),
            "schema": None,
            "revision": None,
            "sha256": sha256(path) if path.exists() else None,
            "status": status,
            "code": snapshot.get("code", "BLOCKED_CONTROL_DOC_CORRUPT"),
        }
    validated = gate.validate_snapshot(
        snapshot,
        canonical_path=str(path),
        canonical_root=str(project_root),
        expected_schema=gate.SCHEMA,
        required_sections=_activation_module().REQUIRED_CONTROL_SECTIONS,
    )
    if not validated.get("valid"):
        return {
            "path": str(path),
            "schema": snapshot.get("schema"),
            "revision": snapshot.get("revision"),
            "sha256": snapshot.get("sha256"),
            "status": "CONFLICT",
            "code": validated.get("code", "BLOCKED_CONTROL_DOC_CORRUPT"),
        }
    return {
        "path": str(path),
        "schema": snapshot["schema"],
        "revision": snapshot["revision"],
        "sha256": snapshot["sha256"],
        "status": "VALID",
    }


def _load_state(codex_home: Path) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    path = _state_path(codex_home)
    if not path.exists():
        return None, None
    try:
        state = _read_json(path)
    except (OSError, ValueError, UnicodeError) as exc:
        return None, {"status": "BLOCKED", "code": "BLOCKED_INSTALL_STATE_CORRUPT", "message": str(exc)}
    if not isinstance(state, dict) or state.get("format") != STATE_FORMAT or not isinstance(state.get("files"), list):
        return None, {
            "status": "BLOCKED",
            "code": "BLOCKED_INSTALL_STATE_CORRUPT",
            "message": "install-state manifest has an invalid format",
        }
    return state, None


def _state_files(state: dict[str, Any] | None, codex_home: Path, project_root: Path | None) -> dict[Path, dict[str, Any]]:
    if state is None:
        return {}
    roots = [codex_home]
    if project_root is not None:
        roots.append(project_root)
    result: dict[Path, dict[str, Any]] = {}
    for item in state["files"]:
        if not isinstance(item, dict) or not isinstance(item.get("path"), str) or not isinstance(item.get("installed_sha256"), str):
            raise ValueError("install-state file entry is malformed")
        path = Path(item["path"]).expanduser().resolve()
        if not any(_within(path, root) for root in roots):
            raise ValueError("install-state file escapes an owned root")
        result[path] = item
    return result


def _expected_skill_files(bundle_root: Path, codex_home: Path) -> list[tuple[Path, Path, str]]:
    output: list[tuple[Path, Path, str]] = []
    for skill_name in USER_SKILLS:
        source_root = bundle_root / "skills" / skill_name
        for source in sorted(source_root.rglob("*")):
            if source.is_file() and "__pycache__" not in source.parts and source.suffix != ".pyc":
                output.append((source, (codex_home / "skills" / skill_name / source.relative_to(source_root)).resolve(), "skill"))
    return output


def _preflight(
    *,
    bundle_root: Path,
    codex_home: Path,
    project_root: Path | None,
    state: dict[str, Any] | None,
    bootstrap_doc: bool,
) -> dict[str, Any]:
    activate = _activation_module()
    if project_root is not None:
        project_control = project_root / PROJECT_CONTROL_RELATIVE
        if not bootstrap_doc:
            project_state = activate._validate_project_surface(bundle_root, project_root)
            if project_state.get("status") == "BLOCKED":
                return project_state
        elif project_control.exists():
            project_state = activate._validate_project_surface(bundle_root, project_root)
            if project_state.get("status") == "BLOCKED":
                return project_state

    try:
        previous_files = _state_files(state, codex_home, project_root)
    except ValueError as exc:
        return {"status": "BLOCKED", "code": "BLOCKED_INSTALL_STATE_CORRUPT", "message": str(exc)}

    home_agents = (codex_home / "AGENTS.md").resolve()
    current_agents = home_agents.read_text(encoding="utf-8") if home_agents.exists() else ""
    marker_error = _marker_error(current_agents)
    if marker_error:
        return {"status": "BLOCKED", "code": marker_error, "message": "managed AGENTS markers are not well formed"}

    current_block = _block_from_text(current_agents)
    expected_block = _managed_block(bundle_root)
    if state is not None and current_block is not None:
        old_hash = state.get("managed_agents", {}).get("block_sha256")
        if isinstance(old_hash, str) and hashlib.sha256(current_block.encode("utf-8")).hexdigest() != old_hash:
            return {
                "status": "BLOCKED",
                "code": "BLOCKED_MANAGED_MARKER_CONFLICT",
                "message": "managed AGENTS block was edited outside the lifecycle manifest",
            }

    legacy_adopted = state is None and current_block is not None
    snapshots: list[dict[str, Any]] = []
    target_sources = _expected_skill_files(bundle_root, codex_home)
    for source, target, kind in target_sources:
        if target.is_symlink():
            return {"status": "BLOCKED", "code": "BLOCKED_OWNERSHIP_CONFLICT", "message": f"managed target is a symlink: {target}"}
        if target.exists():
            old = previous_files.get(target)
            if old is not None:
                if sha256(target) != old["installed_sha256"]:
                    return {"status": "BLOCKED", "code": "BLOCKED_OWNERSHIP_CONFLICT", "message": f"owned file was edited: {target}"}
            elif not legacy_adopted and target.read_bytes() != source.read_bytes():
                return {"status": "BLOCKED", "code": "BLOCKED_OWNERSHIP_CONFLICT", "message": f"unowned target exists: {target}"}
            snapshots.append({"path": str(target), "exists": True, "sha256": sha256(target), "kind": kind})

    if home_agents.exists():
        snapshots.append({"path": str(home_agents), "exists": True, "sha256": sha256(home_agents), "kind": "agents"})
    if project_root is not None:
        project_agents = (project_root / "AGENTS.md").resolve()
        if project_agents.exists():
            snapshots.append({"path": str(project_agents), "exists": True, "sha256": sha256(project_agents), "kind": "project-agents"})
    return {
        "status": "OK",
        "snapshots": snapshots,
        "legacy_adopted": legacy_adopted,
        "expected_block": expected_block,
    }


def _create_backup(codex_home: Path, snapshots: list[dict[str, Any]], previous_state: dict[str, Any] | None, version: str) -> Path | None:
    if not snapshots and previous_state is None:
        return None
    backup_root = codex_home / BACKUPS_RELATIVE
    backup_root.mkdir(parents=True, exist_ok=True)
    backup_dir = backup_root / f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')}-{version}"
    files: list[dict[str, Any]] = []
    for index, item in enumerate(snapshots):
        source = Path(item["path"])
        relative = Path("files") / f"{index:04d}.bin"
        target = backup_dir / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        files.append({**item, "backup": relative.as_posix()})
    backup_manifest = {
        "format": "wukong-backup/v1",
        "created_at": _now(),
        "previous_state": previous_state,
        "files": files,
    }
    _write_json_atomic(backup_dir / "backup-manifest.json", backup_manifest)
    return backup_dir


def _state_manifest(
    *,
    bundle_root: Path,
    codex_home: Path,
    project_root: Path | None,
    version: str,
    previous_state: dict[str, Any] | None,
    backup_dir: Path | None,
    legacy_adopted: bool,
    preexisting_paths: set[Path],
) -> dict[str, Any]:
    files: list[dict[str, Any]] = []
    prior = _state_files(previous_state, codex_home, project_root)
    for _source, target, kind in _expected_skill_files(bundle_root, codex_home):
        if target.exists():
            previous = prior.get(target, {})
            files.append(
                {
                    "path": str(target),
                    "kind": kind,
                    "ownership": "wukong",
                    "created_by_wukong": target not in preexisting_paths and not bool(previous),
                    "installed_sha256": sha256(target),
                }
            )
    home_agents = (codex_home / "AGENTS.md").resolve()
    if home_agents.exists():
        files.append(
            {
                "path": str(home_agents),
                "kind": "agents",
                "ownership": "managed-block",
                "created_by_wukong": home_agents not in preexisting_paths and home_agents not in prior,
                "installed_sha256": sha256(home_agents),
            }
        )
    if project_root is not None:
        project_agents = (project_root / "AGENTS.md").resolve()
        if project_agents.exists():
            files.append(
                {
                    "path": str(project_agents),
                    "kind": "project-agents",
                    "ownership": "wukong-bootstrap" if project_agents not in preexisting_paths and project_agents not in prior else "user-preserved",
                    "created_by_wukong": project_agents not in preexisting_paths and project_agents not in prior,
                    "installed_sha256": sha256(project_agents),
                }
            )
    block = _block_from_text(home_agents.read_text(encoding="utf-8")) if home_agents.exists() else None
    control = _control_status(bundle_root, project_root)
    manifest = {
        "format": STATE_FORMAT,
        "identity": {"name": IDENTITY_NAME, "package": PACKAGE_NAME, "version": version},
        "installed_at": previous_state.get("installed_at", _now()) if previous_state else _now(),
        "updated_at": _now(),
        "codex_home": str(codex_home),
        "project_root": str(project_root) if project_root is not None else None,
        "project_control": control,
        "managed_agents": {
            "path": str(home_agents),
            "begin": LEGACY_BEGIN,
            "end": LEGACY_END,
            "block_sha256": hashlib.sha256(block.encode("utf-8")).hexdigest() if block is not None else None,
        },
        "files": files,
        "backups": [str(backup_dir)] if backup_dir is not None else [],
        "ownership": "legacy-marker-adopted" if legacy_adopted else "wukong",
    }
    return manifest


def _public_result(
    *,
    status: str,
    bundle_root: Path,
    codex_home: Path,
    project_root: Path | None,
    version: str | None,
    changed: bool,
    code: str | None = None,
    message: str | None = None,
    **extra: Any,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "status": status,
        "changed": changed,
        "identity": {"name": IDENTITY_NAME, "package": PACKAGE_NAME, "version": version},
        "state_path": str(_state_path(codex_home)),
        "project_control": _control_status(bundle_root, project_root),
    }
    if code:
        result["code"] = code
    if message:
        result["message"] = message
    result.update(extra)
    return result


def _restore_backup(backup_dir: Path, current_state: dict[str, Any], codex_home: Path, project_root: Path | None) -> dict[str, Any]:
    manifest_path = backup_dir / "backup-manifest.json"
    if not manifest_path.exists():
        return {"status": "BLOCKED", "code": "BLOCKED_BACKUP_CORRUPT", "message": "backup manifest is missing"}
    try:
        backup = _read_json(manifest_path)
        previous = backup.get("previous_state")
        if not isinstance(backup, dict) or not isinstance(backup.get("files"), list) or not isinstance(previous, dict):
            raise ValueError("backup manifest has no previous state")
        current_files = _state_files(current_state, codex_home, project_root)
        backup_entries = {Path(item["path"]).resolve(): item for item in backup["files"]}
        for path, item in backup_entries.items():
            current = current_files.get(path)
            if current is not None and path.exists() and sha256(path) != current["installed_sha256"]:
                return {"status": "BLOCKED", "code": "BLOCKED_ROLLBACK_CONFLICT", "message": f"edited file blocks rollback: {path}"}
        previous_files = _state_files(previous, codex_home, project_root)
        for path, current in current_files.items():
            if path not in previous_files and path.exists() and sha256(path) != current["installed_sha256"]:
                return {"status": "BLOCKED", "code": "BLOCKED_ROLLBACK_CONFLICT", "message": f"edited new file blocks rollback: {path}"}
        for path, item in backup_entries.items():
            backup_file = backup_dir / item["backup"]
            if not _within(backup_file, backup_dir) or not backup_file.is_file():
                return {"status": "BLOCKED", "code": "BLOCKED_BACKUP_CORRUPT", "message": f"backup entry is invalid: {path}"}
            if sha256(backup_file) != item["sha256"]:
                return {"status": "BLOCKED", "code": "BLOCKED_BACKUP_CORRUPT", "message": f"backup hash mismatch: {path}"}
        for path, current in current_files.items():
            if path not in previous_files and path.exists():
                path.unlink()
        for path, item in backup_entries.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(backup_dir / item["backup"], path)
        return {"status": "OK", "previous_state": previous}
    except (OSError, KeyError, TypeError, ValueError, UnicodeError) as exc:
        return {"status": "BLOCKED", "code": "BLOCKED_BACKUP_CORRUPT", "message": str(exc)}


def _rollback(*, bundle_root: Path, codex_home: Path, project_root: Path | None, state: dict[str, Any]) -> dict[str, Any]:
    backups = state.get("backups")
    if not isinstance(backups, list) or not backups:
        return _public_result(
            status="BLOCKED",
            bundle_root=bundle_root,
            codex_home=codex_home,
            project_root=project_root,
            version=state.get("identity", {}).get("version"),
            changed=False,
            code="BLOCKED_ROLLBACK_UNAVAILABLE",
            message="no upgrade backup is recorded",
        )
    backup_dir = Path(backups[-1]).expanduser().resolve()
    if not _within(backup_dir, (codex_home / BACKUPS_RELATIVE).resolve()):
        return _public_result(
            status="BLOCKED",
            bundle_root=bundle_root,
            codex_home=codex_home,
            project_root=project_root,
            version=state.get("identity", {}).get("version"),
            changed=False,
            code="BLOCKED_BACKUP_CORRUPT",
            message="backup path is outside the owned backup directory",
        )
    restored = _restore_backup(backup_dir, state, codex_home, project_root)
    if restored.get("status") != "OK":
        return _public_result(
            status="BLOCKED",
            bundle_root=bundle_root,
            codex_home=codex_home,
            project_root=project_root,
            version=state.get("identity", {}).get("version"),
            changed=False,
            code=restored.get("code"),
            message=restored.get("message"),
        )
    previous = restored["previous_state"]
    previous["backups"] = []
    previous["updated_at"] = _now()
    _write_json_atomic(_state_path(codex_home), previous)
    return _public_result(
        status="ROLLED_BACK",
        bundle_root=bundle_root,
        codex_home=codex_home,
        project_root=project_root,
        version=previous.get("identity", {}).get("version"),
        changed=True,
        backups=[str(backup_dir)],
    )


def run_install(
    *,
    bundle_root: Path | str | None = None,
    codex_home: Path | str | None = None,
    project_root: Path | str | None = None,
    bootstrap_doc: bool = False,
    rollback: bool = False,
) -> dict[str, Any]:
    bundle = Path(bundle_root).resolve() if bundle_root is not None else _default_bundle_root()
    home = Path(codex_home).expanduser().resolve() if codex_home is not None else _default_codex_home()
    project = Path(project_root).resolve() if project_root is not None else None
    try:
        version = _bundle_version(bundle)
        state, state_error = _load_state(home)
        if state_error:
            return _public_result(status="BLOCKED", bundle_root=bundle, codex_home=home, project_root=project, version=version, changed=False, code=state_error["code"], message=state_error["message"])
        saved_project = state.get("project_root") if isinstance(state, dict) else None
        if project is not None and isinstance(saved_project, str) and project != Path(saved_project).resolve():
            return _public_result(status="BLOCKED", bundle_root=bundle, codex_home=home, project_root=project, version=version, changed=False, code="BLOCKED_INSTALL_STATE_CONFLICT", message="requested project root does not match the install manifest")
        if project is None and isinstance(saved_project, str) and saved_project:
            project = Path(saved_project).resolve()
        if rollback:
            if state is None:
                return _public_result(status="BLOCKED", bundle_root=bundle, codex_home=home, project_root=project, version=version, changed=False, code="BLOCKED_ROLLBACK_UNAVAILABLE", message="install-state manifest is missing")
            return _rollback(bundle_root=bundle, codex_home=home, project_root=project, state=state)

        preflight = _preflight(
            bundle_root=bundle,
            codex_home=home,
            project_root=project,
            state=state,
            bootstrap_doc=bootstrap_doc,
        )
        if preflight.get("status") == "BLOCKED":
            return _public_result(
                status="BLOCKED",
                bundle_root=bundle,
                codex_home=home,
                project_root=project,
                version=version,
                changed=False,
                code=preflight.get("code"),
                message=preflight.get("message"),
            )

        backup_dir = _create_backup(home, preflight.get("snapshots", []), state, version)
        activation = _activation_module()
        result = activation.run_activation(
            bundle_root=bundle,
            codex_home=home,
            project_root=project,
            bootstrap_doc=bootstrap_doc,
        )
        if result.get("status") == "BLOCKED":
            if backup_dir is not None and state is not None:
                _restore_backup(backup_dir, state, home, project)
            return _public_result(
                status="BLOCKED",
                bundle_root=bundle,
                codex_home=home,
                project_root=project,
                version=version,
                changed=False,
                code=result.get("code", "BLOCKED_ACTIVATION"),
                message=result.get("message", "activation failed"),
            )
        writes = result.get("writes", [])
        changed = bool(writes) or state is None or state.get("identity", {}).get("version") != version
        if not changed and state is not None:
            return _public_result(
                status="INSTALLED",
                bundle_root=bundle,
                codex_home=home,
                project_root=project,
                version=version,
                changed=False,
                backups=state.get("backups", []),
                ownership=state.get("ownership", "wukong"),
            )

        manifest = _state_manifest(
            bundle_root=bundle,
            codex_home=home,
            project_root=project,
            version=version,
            previous_state=state,
            backup_dir=backup_dir,
            legacy_adopted=bool(preflight.get("legacy_adopted")),
            preexisting_paths={Path(item["path"]).resolve() for item in preflight.get("snapshots", [])},
        )
        try:
            _write_json_atomic(_state_path(home), manifest)
        except (OSError, ValueError, TypeError) as exc:
            if backup_dir is not None and state is not None:
                _restore_backup(backup_dir, manifest, home, project)
            return _public_result(
                status="BLOCKED",
                bundle_root=bundle,
                codex_home=home,
                project_root=project,
                version=version,
                changed=False,
                code="BLOCKED_INSTALL_STATE_WRITE",
                message=str(exc),
            )
        status = "UPGRADED" if state is not None and state.get("identity", {}).get("version") != version else "INSTALLED"
        return _public_result(
            status=status,
            bundle_root=bundle,
            codex_home=home,
            project_root=project,
            version=version,
            changed=True,
            backups=manifest["backups"],
            ownership=manifest["ownership"],
            writes=writes,
        )
    except (OSError, KeyError, TypeError, ValueError, UnicodeError, RuntimeError) as exc:
        return _public_result(
            status="BLOCKED",
            bundle_root=bundle,
            codex_home=home,
            project_root=project,
            version=locals().get("version"),
            changed=False,
            code="BLOCKED_INSTALL_ERROR",
            message=str(exc),
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Install, upgrade, or roll back the public Wukong bundle.")
    parser.add_argument("--bundle-root", default=str(_default_bundle_root()))
    parser.add_argument("--codex-home", default=str(_default_codex_home()))
    parser.add_argument("--project-root")
    parser.add_argument("--bootstrap-doc", action="store_true")
    parser.add_argument("--rollback", action="store_true")
    args = parser.parse_args(argv)
    result = run_install(
        bundle_root=args.bundle_root,
        codex_home=args.codex_home,
        project_root=args.project_root,
        bootstrap_doc=args.bootstrap_doc,
        rollback=args.rollback,
    )
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["status"] in {"INSTALLED", "UPGRADED", "ROLLED_BACK"} else 2


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any


def _load_install():
    path = Path(__file__).resolve().with_name("install_wukong.py")
    spec = importlib.util.spec_from_file_location("wukong_lifecycle_install", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load helper: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _empty_parent_dirs(path: Path, boundary: Path) -> None:
    current = path.parent.resolve()
    boundary = boundary.resolve()
    while current != boundary and _within(current, boundary):
        try:
            current.rmdir()
        except OSError:
            break
        current = current.parent


def _within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _blocked(install: Any, bundle: Path, home: Path, project: Path | None, version: Any, code: str, message: str, **extra: Any) -> dict[str, Any]:
    return install._public_result(
        status="BLOCKED",
        bundle_root=bundle,
        codex_home=home,
        project_root=project,
        version=version,
        changed=False,
        code=code,
        message=message,
        **extra,
    )


def _effective_project(state: dict[str, Any], project_root: Path | None) -> tuple[Path | None, str | None]:
    saved = state.get("project_root")
    if project_root is not None and saved is not None and project_root.resolve() != Path(saved).resolve():
        return None, "BLOCKED_INSTALL_STATE_CONFLICT"
    if project_root is not None:
        return project_root, None
    return (Path(saved).resolve() if isinstance(saved, str) and saved else None), None


def _cleanup_backup(install: Any, backup_dir: Path, backups_root: Path) -> None:
    if not _within(backup_dir, backups_root) or not backup_dir.is_dir():
        raise ValueError("backup directory is outside the owned backup root")
    manifest_path = backup_dir / "backup-manifest.json"
    if not manifest_path.is_file():
        raise ValueError("backup manifest is missing")
    manifest = install._read_json(manifest_path)
    entries = manifest.get("files") if isinstance(manifest, dict) else None
    if not isinstance(entries, list):
        raise ValueError("backup manifest entries are invalid")
    expected = {manifest_path.resolve()}
    for item in entries:
        relative = Path(item["backup"])
        backup_file = (backup_dir / relative).resolve()
        if not _within(backup_file, backup_dir) or not backup_file.is_file():
            raise ValueError("backup entry is outside the backup directory")
        expected.add(backup_file)
    actual = {path.resolve() for path in backup_dir.rglob("*") if path.is_file()}
    if actual != expected:
        raise ValueError("backup directory contains unexpected files")
    for path in sorted(actual, reverse=True):
        path.unlink()
    for directory in sorted((path for path in backup_dir.rglob("*") if path.is_dir()), reverse=True):
        directory.rmdir()
    backup_dir.rmdir()


def run_uninstall(
    *,
    bundle_root: Path | str | None = None,
    codex_home: Path | str | None = None,
    project_root: Path | str | None = None,
    purge_project_control: bool = False,
    confirm_purge: str | None = None,
) -> dict[str, Any]:
    install = _load_install()
    bundle = Path(bundle_root).resolve() if bundle_root is not None else install._default_bundle_root()
    home = Path(codex_home).expanduser().resolve() if codex_home is not None else install._default_codex_home()
    requested_project = Path(project_root).resolve() if project_root is not None else None
    try:
        version = install._bundle_version(bundle)
        state, state_error = install._load_state(home)
        if state_error:
            return _blocked(install, bundle, home, requested_project, version, state_error["code"], state_error["message"])
        if state is None:
            return _blocked(install, bundle, home, requested_project, version, "BLOCKED_INSTALL_STATE_MISSING", "Wukong install-state manifest is missing")
        project, project_error = _effective_project(state, requested_project)
        if project_error:
            return _blocked(install, bundle, home, requested_project, version, project_error, "requested project root does not match the install manifest")
        if purge_project_control and confirm_purge != "PROJECT-CONTROL":
            return _blocked(install, bundle, home, project, version, "BLOCKED_PURGE_CONFIRMATION_REQUIRED", "exact confirmation token PROJECT-CONTROL is required")

        try:
            state_files = install._state_files(state, home, project)
        except ValueError as exc:
            return _blocked(install, bundle, home, project, version, "BLOCKED_INSTALL_STATE_CORRUPT", str(exc))

        removals: list[tuple[Path, str]] = []
        rewrites: list[tuple[Path, str]] = []
        preserved_user_edits: list[str] = []
        managed_agents = state.get("managed_agents", {})
        for path, item in state_files.items():
            if not path.exists():
                continue
            if path.is_symlink():
                return _blocked(install, bundle, home, project, version, "BLOCKED_OWNERSHIP_CONFLICT", f"managed path is a symlink: {path}")
            kind = item.get("kind")
            if kind == "skill":
                if install.sha256(path) != item.get("installed_sha256"):
                    return _blocked(install, bundle, home, project, version, "BLOCKED_OWNERSHIP_CONFLICT", f"edited Wukong file blocks uninstall: {path}")
                removals.append((path, "skill"))
            elif kind == "agents":
                text = path.read_text(encoding="utf-8")
                if install._marker_error(text):
                    return _blocked(install, bundle, home, project, version, "BLOCKED_MANAGED_MARKER_CONFLICT", "managed AGENTS markers are not well formed")
                block = install._block_from_text(text, managed_agents.get("begin", install.LEGACY_BEGIN), managed_agents.get("end", install.LEGACY_END))
                expected_hash = managed_agents.get("block_sha256")
                if block is None or not isinstance(expected_hash, str) or install.hashlib.sha256(block.encode("utf-8")).hexdigest() != expected_hash:
                    return _blocked(install, bundle, home, project, version, "BLOCKED_MANAGED_MARKER_CONFLICT", f"managed AGENTS block was edited: {path}")
                start = text.index(block)
                rewritten = text[:start] + text[start + len(block):]
                if not rewritten.strip() and item.get("created_by_wukong"):
                    removals.append((path, "agents"))
                else:
                    rewrites.append((path, rewritten.rstrip() + "\n"))
            elif kind == "project-agents":
                if install.sha256(path) != item.get("installed_sha256"):
                    preserved_user_edits.append(str(path))
                elif item.get("created_by_wukong"):
                    removals.append((path, "project-agents"))

        control_path = None
        if project is not None:
            control_path = (project / install.PROJECT_CONTROL_RELATIVE).resolve()
            if purge_project_control and control_path.exists():
                recorded = state.get("project_control", {}).get("sha256")
                if not isinstance(recorded, str) or install.sha256(control_path) != recorded:
                    return _blocked(install, bundle, home, project, version, "BLOCKED_PROJECT_CONTROL_CONFLICT", "project control changed; purge refused")
                if not _within(control_path, project):
                    return _blocked(install, bundle, home, project, version, "BLOCKED_PROJECT_CONTROL_CONFLICT", "project control path is not canonical")
            elif purge_project_control and not control_path.exists():
                control_path = None

        backup_root = (home / install.BACKUPS_RELATIVE).resolve()
        backup_dirs = [Path(value).expanduser().resolve() for value in state.get("backups", []) if isinstance(value, str)]
        for backup_dir in backup_dirs:
            if not _within(backup_dir, backup_root):
                return _blocked(install, bundle, home, project, version, "BLOCKED_BACKUP_CONFLICT", "backup path is outside the owned backup root")

        for path, _kind in removals:
            path.unlink()
            if _within(path, home / "skills"):
                _empty_parent_dirs(path, home / "skills")
        for path, rewritten in rewrites:
            path.write_text(rewritten, encoding="utf-8", newline="\n")
        if purge_project_control and control_path is not None:
            control_path.unlink()
        for backup_dir in backup_dirs:
            _cleanup_backup(install, backup_dir, backup_root)
        state_path = install._state_path(home)
        if state_path.exists():
            state_path.unlink()
        if backup_root.exists():
            try:
                backup_root.rmdir()
            except OSError:
                pass
        state_dir = state_path.parent
        if state_dir.exists():
            try:
                state_dir.rmdir()
            except OSError:
                pass

        result = install._public_result(
            status="UNINSTALLED",
            bundle_root=bundle,
            codex_home=home,
            project_root=project,
            version=state.get("identity", {}).get("version", version),
            changed=True,
            preserved_user_edits=preserved_user_edits,
        )
        result["project_control"]["status"] = "PURGED" if purge_project_control else "PRESERVED"
        return result
    except (OSError, KeyError, TypeError, ValueError, UnicodeError, RuntimeError) as exc:
        return _blocked(install, bundle, home, requested_project, locals().get("version"), "BLOCKED_UNINSTALL_ERROR", str(exc))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Safely uninstall the Wukong-managed surface.")
    parser.add_argument("--bundle-root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--codex-home")
    parser.add_argument("--project-root")
    parser.add_argument("--purge-project-control", action="store_true")
    parser.add_argument("--confirm-purge")
    args = parser.parse_args(argv)
    result = run_uninstall(
        bundle_root=args.bundle_root,
        codex_home=args.codex_home,
        project_root=args.project_root,
        purge_project_control=args.purge_project_control,
        confirm_purge=args.confirm_purge,
    )
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["status"] == "UNINSTALLED" else 2


if __name__ == "__main__":
    raise SystemExit(main())

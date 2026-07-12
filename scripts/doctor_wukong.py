from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any


def _load_install():
    path = Path(__file__).resolve().with_name("install_wukong.py")
    spec = importlib.util.spec_from_file_location("wukong_lifecycle_install_doctor", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load helper: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_doctor(
    *,
    bundle_root: Path | str | None = None,
    codex_home: Path | str | None = None,
    project_root: Path | str | None = None,
) -> dict[str, Any]:
    install = _load_install()
    bundle = Path(bundle_root).resolve() if bundle_root is not None else install._default_bundle_root()
    home = Path(codex_home).expanduser().resolve() if codex_home is not None else install._default_codex_home()
    requested_project = Path(project_root).resolve() if project_root is not None else None
    try:
        version = install._bundle_version(bundle)
        state, state_error = install._load_state(home)
        if state_error:
            return {
                "status": "BLOCKED",
                "identity": {"name": install.IDENTITY_NAME, "package": install.PACKAGE_NAME, "version": version},
                "state_path": str(install._state_path(home)),
                "project_control": install._control_status(bundle, requested_project),
                "issues": [{"code": state_error["code"], "message": state_error["message"]}],
                "read_only": True,
            }
        if state is None:
            return {
                "status": "NOT_INSTALLED",
                "identity": {"name": install.IDENTITY_NAME, "package": install.PACKAGE_NAME, "version": version},
                "state_path": str(install._state_path(home)),
                "project_control": install._control_status(bundle, requested_project),
                "issues": [{"code": "BLOCKED_INSTALL_STATE_MISSING", "message": "Wukong install-state manifest is missing"}],
                "read_only": True,
            }
        saved_project = state.get("project_root")
        if requested_project is not None and saved_project and requested_project != Path(saved_project).resolve():
            return {
                "status": "BLOCKED",
                "identity": state.get("identity", {}),
                "state_path": str(install._state_path(home)),
                "project_control": install._control_status(bundle, requested_project),
                "issues": [{"code": "BLOCKED_INSTALL_STATE_CONFLICT", "message": "requested project root differs from install state"}],
                "read_only": True,
            }
        project = requested_project or (Path(saved_project).resolve() if isinstance(saved_project, str) and saved_project else None)
        issues: list[dict[str, str]] = []
        try:
            state_files = install._state_files(state, home, project)
        except ValueError as exc:
            state_files = {}
            issues.append({"code": "BLOCKED_INSTALL_STATE_CORRUPT", "message": str(exc)})
        managed = state.get("managed_agents", {})
        for path, item in state_files.items():
            if not path.exists():
                issues.append({"code": "MISSING_MANAGED_FILE", "message": str(path)})
                continue
            if item.get("kind") == "agents":
                text = path.read_text(encoding="utf-8")
                block = install._block_from_text(text, managed.get("begin", install.LEGACY_BEGIN), managed.get("end", install.LEGACY_END))
                expected = managed.get("block_sha256")
                if block is None or not isinstance(expected, str) or install.hashlib.sha256(block.encode("utf-8")).hexdigest() != expected:
                    issues.append({"code": "BLOCKED_MANAGED_MARKER_CONFLICT", "message": str(path)})
            elif item.get("kind") == "project-agents":
                if install.sha256(path) != item.get("installed_sha256"):
                    issues.append({"code": "PRESERVED_USER_EDIT", "message": str(path)})
            elif install.sha256(path) != item.get("installed_sha256"):
                issues.append({"code": "BLOCKED_OWNERSHIP_CONFLICT", "message": str(path)})

        project_control = install._control_status(bundle, project)
        recorded_control = state.get("project_control", {})
        if project_control.get("status") == "VALID" and recorded_control.get("sha256") != project_control.get("sha256"):
            project_control["status"] = "CONFLICT"
            project_control["code"] = "BLOCKED_PROJECT_CONTROL_CONFLICT"
            issues.append({"code": "BLOCKED_PROJECT_CONTROL_CONFLICT", "message": "project control CAS differs from install state"})
        status = "HEALTHY" if not issues and project_control.get("status") in {"VALID", "NOT_REQUESTED"} else "DEGRADED"
        return {
            "status": status,
            "identity": state.get("identity", {"name": install.IDENTITY_NAME, "package": install.PACKAGE_NAME, "version": version}),
            "state_path": str(install._state_path(home)),
            "project_control": project_control,
            "issues": issues,
            "read_only": True,
        }
    except (OSError, KeyError, TypeError, ValueError, UnicodeError, RuntimeError) as exc:
        return {
            "status": "BLOCKED",
            "identity": {"name": install.IDENTITY_NAME, "package": install.PACKAGE_NAME, "version": locals().get("version")},
            "state_path": str(install._state_path(home)),
            "project_control": install._control_status(bundle, requested_project),
            "issues": [{"code": "BLOCKED_DOCTOR_ERROR", "message": str(exc)}],
            "read_only": True,
        }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inspect the Wukong installation without writing.")
    parser.add_argument("--bundle-root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--codex-home")
    parser.add_argument("--project-root")
    args = parser.parse_args(argv)
    result = run_doctor(bundle_root=args.bundle_root, codex_home=args.codex_home, project_root=args.project_root)
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["status"] == "HEALTHY" else 2


if __name__ == "__main__":
    raise SystemExit(main())

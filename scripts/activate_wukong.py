from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
from pathlib import Path
from typing import Any


SENTINEL_BEGIN = "<!-- WUKONG_PUBLIC_CONTRACT:BEGIN -->"
SENTINEL_END = "<!-- WUKONG_PUBLIC_CONTRACT:END -->"
USER_SKILLS = ("wukong-always", "multi-agent-wukong", "codex-history")
PROJECT_CONTROL_RELATIVE = Path("docs") / "wukong" / "PROJECT-CONTROL.md"
REQUIRED_CONTROL_SECTIONS = (
    "Project Goal",
    "Hard Constraints",
    "Subagent Handoff Contract",
    "Verification Evidence",
    "Change Log",
)


def _load_gate(bundle_root: Path) -> Any:
    gate_path = bundle_root / "skills" / "multi-agent-wukong" / "scripts" / "project_control_gate.py"
    spec = importlib.util.spec_from_file_location("wukong_public_gate", gate_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"missing project-control gate: {gate_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _default_bundle_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _default_codex_home() -> Path:
    configured = os.environ.get("CODEX_HOME")
    if configured:
        return Path(configured).expanduser().resolve()
    return (Path.home() / ".codex").resolve()


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _write_text_if_changed(path: Path, text: str, label: str, writes: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and _read_text(path) == text:
        return
    path.write_text(text, encoding="utf-8", newline="\n")
    writes.append(label)


def _sync_tree(source: Path, target: Path, label: str, writes: list[str]) -> None:
    changed = False
    for src_path in sorted(source.rglob("*")):
        if "__pycache__" in src_path.parts or (src_path.is_file() and src_path.suffix == ".pyc"):
            continue
        relative = src_path.relative_to(source)
        dst_path = target / relative
        if src_path.is_dir():
            dst_path.mkdir(parents=True, exist_ok=True)
            continue
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        src_bytes = src_path.read_bytes()
        if dst_path.exists() and dst_path.read_bytes() == src_bytes:
            continue
        dst_path.write_bytes(src_bytes)
        changed = True
    if changed:
        writes.append(label)


def _managed_block(contract_text: str) -> str:
    return f"{SENTINEL_BEGIN}\n{contract_text.rstrip()}\n{SENTINEL_END}\n"


def _merge_managed_contract(existing: str, contract_text: str) -> str:
    begin_count = existing.count(SENTINEL_BEGIN)
    end_count = existing.count(SENTINEL_END)
    if begin_count != end_count or begin_count > 1:
        raise ValueError("managed AGENTS sentinel is not well formed")
    block = _managed_block(contract_text)
    if begin_count == 1:
        start = existing.index(SENTINEL_BEGIN)
        end = existing.index(SENTINEL_END) + len(SENTINEL_END)
        merged = existing[:start] + block + existing[end:]
    else:
        body = existing.rstrip("\n")
        spacer = "\n\n" if body else ""
        merged = body + spacer + block
    return merged.rstrip() + "\n"


def _render_project_control(template_text: str, project_root: Path) -> str:
    control_doc = (project_root / PROJECT_CONTROL_RELATIVE).resolve()
    text = template_text.replace("<project-root>/docs/wukong/PROJECT-CONTROL.md", str(control_doc))
    return text.replace("<project-root>", str(project_root.resolve()))


def _bundle_contract(bundle_root: Path) -> str:
    return _read_text(bundle_root / "AGENTS.md")


def _ensure_user_surface(bundle_root: Path, codex_home: Path, verify: bool, writes: list[str]) -> dict[str, Any]:
    missing: list[str] = []
    skills_root = codex_home / "skills"
    for skill_name in USER_SKILLS:
        source = bundle_root / "skills" / skill_name
        target = skills_root / skill_name
        marker = f"user_skill:{skill_name}"
        if verify:
            if not (target / "SKILL.md").exists():
                missing.append(marker)
            continue
        _sync_tree(source, target, marker, writes)

    home_agents = codex_home / "AGENTS.md"
    contract = _bundle_contract(bundle_root)
    if verify:
        if not home_agents.exists():
            missing.append("user_agents:managed_block")
        else:
            current = _read_text(home_agents)
            if current.count(SENTINEL_BEGIN) != 1 or current.count(SENTINEL_END) != 1 or _managed_block(contract).strip() not in current:
                missing.append("user_agents:managed_block")
    else:
        current = _read_text(home_agents) if home_agents.exists() else ""
        merged = _merge_managed_contract(current, contract)
        _write_text_if_changed(home_agents, merged, "user_agents:managed_block", writes)
    return {"missing": missing}


def _bootstrap_project(bundle_root: Path, project_root: Path, writes: list[str]) -> dict[str, Any]:
    gate = _load_gate(bundle_root)
    project_agents = project_root / "AGENTS.md"
    control_doc = project_root / PROJECT_CONTROL_RELATIVE
    if not project_agents.exists():
        example = _read_text(bundle_root / "examples" / "project-AGENTS.example.md")
        _write_text_if_changed(project_agents, example, "project_agents:bootstrap", writes)
    if not control_doc.exists():
        template = _read_text(bundle_root / "docs" / "PROJECT-CONTROL.template.md")
        rendered = _render_project_control(template, project_root)
        result = gate.bootstrap_control_doc(
            str(control_doc.resolve()),
            task_id="PUBLIC_ACTIVATION / BOOTSTRAP_DOC",
            content=rendered,
            canonical_root=str(project_root.resolve()),
        )
        if not result.get("valid"):
            return {
                "status": "BLOCKED",
                "code": result.get("code", "BLOCKED_PROJECT_CONTROL_BOOTSTRAP"),
                "message": result.get("message", "project bootstrap failed"),
                "writes": writes,
                "missing": [],
                "checks": [],
            }
        writes.append("project_control:bootstrap")
    return {"status": "OK"}


def _validate_project_surface(bundle_root: Path, project_root: Path) -> dict[str, Any]:
    gate = _load_gate(bundle_root)
    project_agents = project_root / "AGENTS.md"
    control_doc = project_root / PROJECT_CONTROL_RELATIVE
    missing: list[str] = []
    if not project_agents.exists():
        missing.append("project_agents")
    if not control_doc.exists():
        missing.append("project_control")
    if missing:
        return {
            "status": "BLOCKED",
            "code": "BLOCKED_PROJECT_DOCS_MISSING",
            "message": "project activation requires AGENTS.md and a live control document",
            "missing": missing,
            "checks": [],
        }
    agents_text = _read_text(project_agents)
    if "PROJECT-CONTROL.md" not in agents_text or "Wukong" not in agents_text:
        return {
            "status": "BLOCKED",
            "code": "BLOCKED_PROJECT_AGENTS_INVALID",
            "message": "project AGENTS must describe Wukong coordination and the control document",
            "missing": [],
            "checks": [],
        }
    snapshot = gate.read_snapshot(str(control_doc.resolve()))
    if snapshot.get("valid") is False:
        return {
            "status": "BLOCKED",
            "code": snapshot.get("code", "BLOCKED_CONTROL_DOC_MISSING"),
            "message": snapshot.get("message", "control document read failed"),
            "missing": [],
            "checks": [],
        }
    validated = gate.validate_snapshot(
        snapshot,
        canonical_path=str(control_doc.resolve()),
        canonical_root=str(project_root.resolve()),
        expected_schema=gate.SCHEMA,
        required_sections=REQUIRED_CONTROL_SECTIONS,
    )
    if not validated.get("valid"):
        return {
            "status": "BLOCKED",
            "code": validated.get("code", "BLOCKED_CONTROL_DOC_CORRUPT"),
            "message": validated.get("message", "control document validation failed"),
            "missing": [],
            "checks": [],
        }
    return {"status": "OK", "checks": ["project_agents", "project_control"]}  # type: ignore[return-value]


def run_activation(
    *,
    bundle_root: Path | str | None = None,
    codex_home: Path | str | None = None,
    project_root: Path | str | None = None,
    verify: bool = False,
    bootstrap_doc: bool = False,
) -> dict[str, Any]:
    bundle = Path(bundle_root).resolve() if bundle_root is not None else _default_bundle_root()
    home = Path(codex_home).expanduser().resolve() if codex_home is not None else _default_codex_home()
    project = Path(project_root).resolve() if project_root is not None else None
    writes: list[str] = []
    checks: list[str] = []

    if bootstrap_doc and project is None:
        return {
            "status": "BLOCKED",
            "code": "BLOCKED_PROJECT_ROOT_REQUIRED",
            "message": "--bootstrap-doc requires --project-root",
            "writes": writes,
            "missing": [],
            "checks": checks,
        }

    if project is not None and bootstrap_doc and not verify:
        bootstrapped = _bootstrap_project(bundle, project, writes)
        if bootstrapped.get("status") == "BLOCKED":
            return bootstrapped

    if project is not None:
        project_state = _validate_project_surface(bundle, project)
        if project_state["status"] == "BLOCKED":
            return {
                "status": "BLOCKED",
                "code": project_state["code"],
                "message": project_state["message"],
                "writes": writes,
                "missing": project_state.get("missing", []),
                "checks": checks,
            }
        checks.extend(project_state.get("checks", []))

    try:
        user_state = _ensure_user_surface(bundle, home, verify, writes)
    except ValueError as exc:
        return {
            "status": "BLOCKED",
            "code": "BLOCKED_MANAGED_MARKER_CONFLICT",
            "message": str(exc),
            "writes": [] if verify else writes,
            "missing": [],
            "checks": checks,
        }
    except (OSError, UnicodeError) as exc:
        return {
            "status": "BLOCKED",
            "code": "BLOCKED_ACTIVATION_IO",
            "message": str(exc),
            "writes": [] if verify else writes,
            "missing": [],
            "checks": checks,
        }
    missing = list(user_state["missing"])
    checks.extend([*(f"user_skill:{skill_name}" for skill_name in USER_SKILLS), "user_agents:managed_block"])

    if verify and missing:
        return {
            "status": "BLOCKED",
            "code": "BLOCKED_USER_ACTIVATION_INCOMPLETE",
            "message": "verify requires an already activated user surface",
            "writes": [],
            "missing": missing,
            "checks": checks,
        }

    return {
        "status": "VALIDATED" if verify else "ACTIVATED",
        "mode": "user+project" if project is not None else "user",
        "writes": [] if verify else writes,
        "missing": [] if not verify else missing,
        "checks": checks,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Activate or verify the public Wukong staging bundle.")
    parser.add_argument("--bundle-root", default=str(_default_bundle_root()))
    parser.add_argument("--codex-home", default=str(_default_codex_home()))
    parser.add_argument("--project-root")
    parser.add_argument("--bootstrap-doc", action="store_true")
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args(argv)
    result = run_activation(
        bundle_root=args.bundle_root,
        codex_home=args.codex_home,
        project_root=args.project_root,
        verify=args.verify,
        bootstrap_doc=args.bootstrap_doc,
    )
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["status"] in {"ACTIVATED", "VALIDATED"} else 2


if __name__ == "__main__":
    raise SystemExit(main())

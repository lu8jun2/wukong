"""Path-neutral Chang'e Product Design dispatch helpers."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any


ROLE_ALIASES = {"chang'e", "chang’e", "嫦娥"}
SCALES = {"S", "M", "L", "XL"}
DEFAULT_CONTROL_DOC_PATH = "docs/wukong/PROJECT-CONTROL.md"
DEFAULT_CONFIRMATION = "User explicitly authorized a Chang'e design-start task."

_PROJECT_CONTROL_GATE: Any | None = None
_PRODUCT_DESIGN_GATE: Any | None = None


def _valid(**extra: Any) -> dict[str, Any]:
    return {"valid": True, **extra}


def _blocked(code: str, message: str, **extra: Any) -> dict[str, Any]:
    return {"valid": False, "code": code, "message": message, **extra}


def _load_sibling(module_filename: str, cache_name: str) -> Any:
    global _PROJECT_CONTROL_GATE, _PRODUCT_DESIGN_GATE
    cache_value = _PROJECT_CONTROL_GATE if cache_name == "project_control_gate" else _PRODUCT_DESIGN_GATE
    if cache_value is not None:
        return cache_value
    module_path = Path(__file__).with_name(module_filename)
    spec = importlib.util.spec_from_file_location(cache_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load sibling module: {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if cache_name == "project_control_gate":
        _PROJECT_CONTROL_GATE = module
    else:
        _PRODUCT_DESIGN_GATE = module
    return module


def _canonical_role(role: str) -> str:
    return role.strip().casefold()


def _control_snapshot(control_document_path: str) -> dict[str, Any]:
    gate = _load_sibling("project_control_gate.py", "project_control_gate")
    snapshot = gate.read_snapshot(control_document_path)
    if snapshot.get("valid") is False:
        return snapshot
    required_sections = snapshot.get("sections")
    if not isinstance(required_sections, list) or not required_sections:
        return _blocked(
            "TASK_PACKAGE_CONTROL_DOCUMENT_INVALID",
            "Control-document snapshot must include required sections.",
        )
    return _valid(
        control_document={
            "path": snapshot["path"],
            "schema": snapshot["schema"],
            "revision": snapshot["revision"],
            "sha256": snapshot["sha256"],
            "required_sections": list(required_sections),
        }
    )


def build_chang_e_design_start_package(
    *,
    input_brief: str,
    expected_outputs: list[str],
    lifecycle_scale: str = "M",
    role: str = "Chang'e",
    control_document_path: str = DEFAULT_CONTROL_DOC_PATH,
    parent_task_id: str = "PUBLIC-WUKONG",
    confirmation_evidence: str = DEFAULT_CONFIRMATION,
    delegation_permission: str = "FORBIDDEN",
    runtime_tool_exposed: bool = False,
    auth_failed: bool = False,
    call_failed: bool = False,
    actual_plugin_invocation: bool = False,
    tool_call_id: str | None = None,
    invocation_timestamp: str | None = None,
    artifact_paths: list[str] | None = None,
    artifact_hashes: list[str] | None = None,
    output_validation: dict[str, Any] | None = None,
    confirmation_issuer: str | None = None,
    confirmation_timestamp: str | None = None,
    confirmation_evidence_path: str | None = None,
    confirmation_evidence_sha256: str | None = None,
    codex_home: str | None = None,
) -> dict[str, Any]:
    if lifecycle_scale not in SCALES:
        return _blocked("TASK_PACKAGE_REQUIRED_FIELD_MISSING", "Lifecycle scale must be one of S/M/L/XL.")
    if _canonical_role(role) not in ROLE_ALIASES:
        return _blocked("BLOCKED_PRODUCT_DESIGN_PLUGIN_REQUIRED", "Role must be Chang'e.")

    snapshot_result = _control_snapshot(control_document_path)
    if not snapshot_result.get("valid"):
        return snapshot_result

    product_design_gate = _load_sibling("product_design_gate.py", "product_design_gate")
    invocation_result = product_design_gate.build_product_design_invocation(
        input_brief=input_brief,
        expected_outputs=expected_outputs,
        invocation_owner=role,
        runtime_tool_exposed=runtime_tool_exposed,
        auth_failed=auth_failed,
        call_failed=call_failed,
        actual_plugin_invocation=actual_plugin_invocation,
        tool_call_id=tool_call_id,
        invocation_timestamp=invocation_timestamp,
        artifact_paths=artifact_paths,
        artifact_hashes=artifact_hashes,
        output_validation=output_validation,
        confirmation_issuer=confirmation_issuer,
        confirmation_timestamp=confirmation_timestamp,
        confirmation_evidence_path=confirmation_evidence_path,
        confirmation_evidence_sha256=confirmation_evidence_sha256,
        codex_home=codex_home,
    )
    if not invocation_result.get("valid"):
        return invocation_result

    product_design = invocation_result["product_design"]
    package = {
        "task_id": f"{parent_task_id} / PRODUCT_DESIGN_GREEN_IMPLEMENTATION",
        "role": role,
        "task_type": "design_start",
        "design_start": True,
        "lifecycle_scale": lifecycle_scale,
        "authorization": {
            "status": "CONFIRMED_BY_USER",
            "issuer": "USER_FACING_WUKONG",
            "parent_task_id": parent_task_id,
            "confirmation_evidence": confirmation_evidence,
        },
        "control_document": snapshot_result["control_document"],
        "delegation_permission": delegation_permission,
        "scope": {
            "allowed": ["product design governance evidence", "design outputs after Product Design invocation"],
            "forbidden": ["plugin bypass", "fallback without explicit authorization", "recursive delegation"],
        },
        "tdd": {
            "phase": "GREEN",
            "evidence": ["Product Design RED before implementation", "focused Product Design rerun after implementation"],
        },
        "historian": {"handoff_required": True, "cas_merge": True, "dependency_locked": True},
        "independent_verifier": {"role": "Independent Product Design Verifier", "required": True},
        "stop_condition": "Block before downstream design when Product Design runtime or invocation evidence is unavailable.",
        "external_evaluation": {
            "available_capabilities": [product_design_gate.DEFAULT_DISPLAY_NAME],
            "selected_capability": product_design_gate.DEFAULT_DISPLAY_NAME,
            "invocation_required": True,
            "resolution": invocation_result.get("resolution"),
            "actual_product_design_plugin_invocation": bool(product_design.get("actual_plugin_invocation")),
            "runtime_tool_exposed": bool(product_design.get("runtime_tool_exposed")),
            "runtime_status": product_design.get("runtime_status"),
        },
        "product_design_plugin_required": True,
        "product_design": product_design,
        "design_dependency": {
            "status": product_design["dependency_status"],
            "design_output_allowed": product_design["dependency_status"] == "unlocked",
        },
    }
    return _valid(package=package, resolution=invocation_result.get("resolution"), product_design=product_design)


def evaluate_chang_e_design_start(**kwargs: Any) -> dict[str, Any]:
    package_result = build_chang_e_design_start_package(**kwargs)
    if not package_result.get("valid"):
        return package_result
    package = package_result["package"]
    gate = _load_sibling("project_control_gate.py", "project_control_gate")
    decision = gate.validate_task_package(package)
    if decision.get("valid"):
        return _valid(
            package=package,
            resolution=package_result.get("resolution"),
            product_design=package_result.get("product_design"),
            dependency_status=package["design_dependency"]["status"],
        )
    return {
        **decision,
        "package": package,
        "resolution": package_result.get("resolution"),
        "product_design": package_result.get("product_design"),
    }


def build_chang_e_handoff(
    package: dict[str, Any],
    *,
    status: str | None = None,
    issues: list[dict[str, Any]] | None = None,
    logs: list[str] | None = None,
    test_command: str = "python -m unittest discover -s tests -v",
    test_result: dict[str, Any] | None = None,
    conclusion: str | None = None,
    next_step: str = "HISTORIAN_MERGE_PRODUCT_DESIGN_GREEN",
) -> dict[str, Any]:
    if not isinstance(package, dict):
        return _blocked("HANDOFF_REQUIRED_FIELD_MISSING", "Task package must be an object.")
    product_design_gate = _load_sibling("product_design_gate.py", "product_design_gate")
    product_design = package.get("product_design")
    validation = product_design_gate.validate_product_design_invocation(product_design)
    if not validation.get("valid"):
        return validation
    if product_design.get("actual_plugin_invocation") is not True:
        return _blocked(
            product_design.get("blocked_code") or product_design_gate.BLOCKED_PRODUCT_DESIGN_PLUGIN_UNAVAILABLE,
            "Blocked Product Design packages cannot produce an unlocked historian handoff.",
            dependency_status="locked",
            package=package,
        )
    control_document = package.get("control_document", {})
    invocation = {
        "plugin_id": product_design["resolved_plugin_id"],
        "plugin_version": product_design["resolved_plugin_version"],
        "timestamp": product_design.get("invocation_timestamp"),
        "tool_call_id": product_design.get("tool_call_id"),
        "input_digest": product_design["input_digest"],
        "outputs": list(product_design["expected_outputs"]),
        "artifact_paths": list(product_design.get("artifact_paths", [])),
        "artifact_hashes": list(product_design.get("artifact_hashes", [])),
        "output_validation": dict(product_design.get("output_validation", {})),
        "confirmation_issuer": product_design.get("confirmation_issuer"),
        "confirmation_timestamp": product_design.get("confirmation_timestamp"),
        "confirmation_evidence_path": product_design.get("confirmation_evidence_path"),
        "confirmation_evidence_sha256": product_design.get("confirmation_evidence_sha256"),
        "dependency_status": product_design["dependency_status"],
        "issues": list(issues or []),
        "logs": list(logs or []),
    }
    return _valid(
        handoff={
            "status": status or "DONE",
            "task_id": package.get("task_id"),
            "role": package.get("role"),
            "control_document_path": control_document.get("path"),
            "read_revision": control_document.get("revision"),
            "read_sha256": control_document.get("sha256"),
            "related_sections": list(control_document.get("required_sections", [])),
            "modified_files": [],
            "tdd_status": package.get("tdd", {}).get("phase", "GREEN"),
            "tdd_evidence": dict(package.get("tdd", {})),
            "test_command": test_command,
            "test_result": dict(test_result or {}),
            "issues": list(issues or []),
            "bugs_logs": [],
            "hard_constraints_compliance": "PASS",
            "conclusion": conclusion or "Product Design invocation evidence captured.",
            "next_step": next_step,
            "historian_proposal": "Append Product Design gate evidence and preserve explicit dependency status.",
            "external_skill_agent_evaluation": dict(package.get("external_evaluation", {})),
            "product_design_invocation": invocation,
        }
    )


__all__ = [
    "DEFAULT_CONTROL_DOC_PATH",
    "build_chang_e_design_start_package",
    "build_chang_e_handoff",
    "evaluate_chang_e_design_start",
]

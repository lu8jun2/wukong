"""Deterministic Product Design resolution and invocation contract helpers.

This adapter never calls an external Product Design runtime tool. It resolves
local metadata, derives a canonical invocation contract, and fail-closes when
the callable runtime is unavailable or the invocation evidence is incomplete.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_REMOTE_PLUGIN_ID = "Plugin_fa77aec24fc08191bc6e57f377126d76"
DEFAULT_LOGICAL_PLUGIN_ID = "product-design"
DEFAULT_PLUGIN_VERSION = "0.1.50"
DEFAULT_DISPLAY_NAME = "Product Design"
BLOCKED_PRODUCT_DESIGN_PLUGIN_REQUIRED = "BLOCKED_PRODUCT_DESIGN_PLUGIN_REQUIRED"
BLOCKED_PRODUCT_DESIGN_PLUGIN_UNAVAILABLE = "BLOCKED_PRODUCT_DESIGN_PLUGIN_UNAVAILABLE"
BLOCKED_PRODUCT_DESIGN_INVOCATION_REQUIRED = "BLOCKED_PRODUCT_DESIGN_INVOCATION_REQUIRED"
BLOCKED_PRODUCT_DESIGN_FALLBACK_NOT_AUTHORIZED = "BLOCKED_PRODUCT_DESIGN_FALLBACK_NOT_AUTHORIZED"
BLOCKED_PRODUCT_DESIGN_CONFIRMATION_REQUIRED = "BLOCKED_PRODUCT_DESIGN_CONFIRMATION_REQUIRED"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
VERSION_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")

REQUIRED_INVOCATION_FIELDS = (
    "remote_plugin_id",
    "logical_plugin_id",
    "display_name",
    "resolved_plugin_version",
    "metadata_path",
    "local_cache_path",
    "runtime_tool_exposed",
    "runtime_status",
    "availability",
    "capability_name",
    "invocation_owner",
    "input_brief",
    "input_digest",
    "expected_outputs",
    "invocation_evidence_path",
    "invocation_evidence_sha256",
    "dependency_status",
    "actual_plugin_invocation",
    "blocked_code",
)


def _valid(**extra: Any) -> dict[str, Any]:
    return {"valid": True, **extra}


def _blocked(code: str, message: str, **extra: Any) -> dict[str, Any]:
    return {"valid": False, "code": code, "message": message, **extra}


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _stable_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _default_codex_home(codex_home: str | None = None) -> Path:
    if codex_home:
        return Path(codex_home)
    env_home = os.environ.get("CODEX_HOME")
    if env_home:
        return Path(env_home)
    return Path.home() / ".codex"


def _plugin_root(
    *,
    codex_home: str | None,
    logical_plugin_id: str,
    expected_version: str,
) -> Path:
    return (
        _default_codex_home(codex_home)
        / "plugins"
        / "cache"
        / "openai-curated-remote"
        / logical_plugin_id
        / expected_version
    )


def _metadata_path(plugin_root: Path) -> Path:
    return plugin_root / ".codex-plugin" / "plugin.json"


def _read_json(path: Path) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    try:
        raw = path.read_text(encoding="utf-8")
        value = json.loads(raw)
    except FileNotFoundError:
        return None, _blocked(
            BLOCKED_PRODUCT_DESIGN_PLUGIN_UNAVAILABLE,
            f"Product Design metadata is missing: {path}",
            availability="not_installed",
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return None, _blocked(
            BLOCKED_PRODUCT_DESIGN_PLUGIN_UNAVAILABLE,
            f"Product Design metadata is unreadable: {exc}",
            availability="unavailable",
        )
    if not isinstance(value, dict):
        return None, _blocked(
            BLOCKED_PRODUCT_DESIGN_PLUGIN_UNAVAILABLE,
            "Product Design metadata must be an object",
            availability="unavailable",
        )
    return value, None


def _collect_callable_surfaces(plugin_root: Path) -> list[dict[str, str]]:
    surfaces: list[dict[str, str]] = []
    agent_path = plugin_root / "agents" / "openai.yaml"
    if agent_path.is_file():
        surfaces.append(
            {
                "surface_type": "agent",
                "name": DEFAULT_LOGICAL_PLUGIN_ID,
                "path": str(agent_path),
            }
        )
    skills_dir = plugin_root / "skills"
    if skills_dir.is_dir():
        for skill_dir in sorted(path for path in skills_dir.iterdir() if path.is_dir()):
            skill_file = skill_dir / "SKILL.md"
            if skill_file.is_file():
                surfaces.append(
                    {
                        "surface_type": "skill",
                        "name": skill_dir.name,
                        "path": str(skill_file),
                    }
                )
            skill_agent = skill_dir / "agents" / "openai.yaml"
            if skill_agent.is_file():
                surfaces.append(
                    {
                        "surface_type": "agent",
                        "name": f"{skill_dir.name}:agent",
                        "path": str(skill_agent),
                    }
                )
    bootstrap = plugin_root / "scripts" / "bootstrap-prototype.mjs"
    if bootstrap.is_file():
        surfaces.append(
            {
                "surface_type": "script",
                "name": "bootstrap-prototype",
                "path": str(bootstrap),
            }
        )
    return surfaces


def resolve_product_design_capability(
    *,
    remote_plugin_id: str = DEFAULT_REMOTE_PLUGIN_ID,
    logical_plugin_id: str = DEFAULT_LOGICAL_PLUGIN_ID,
    expected_version: str = DEFAULT_PLUGIN_VERSION,
    codex_home: str | None = None,
) -> dict[str, Any]:
    """Resolve Product Design metadata and exposed local capability surfaces."""

    plugin_root = _plugin_root(
        codex_home=codex_home,
        logical_plugin_id=logical_plugin_id,
        expected_version=expected_version,
    )
    metadata_path = _metadata_path(plugin_root)
    metadata, error = _read_json(metadata_path)
    base = {
        "remote_plugin_id": remote_plugin_id,
        "remote_plugin_id_source": "governance_contract",
        "logical_plugin_id": logical_plugin_id,
        "local_cache_path": str(plugin_root),
        "metadata_path": str(metadata_path),
    }
    if error:
        return _blocked(error["code"], error["message"], resolution=base | {"runtime_status": "not_installed"})

    assert metadata is not None
    interface = metadata.get("interface", {})
    if not isinstance(interface, dict):
        return _blocked(
            BLOCKED_PRODUCT_DESIGN_PLUGIN_UNAVAILABLE,
            "Product Design metadata interface must be an object",
            resolution=base | {"runtime_status": "metadata_mismatch"},
        )
    resolved_name = str(metadata.get("name", ""))
    resolved_version = str(metadata.get("version", ""))
    display_name = str(interface.get("displayName", DEFAULT_DISPLAY_NAME))
    if resolved_name != logical_plugin_id or not VERSION_RE.fullmatch(resolved_version):
        return _blocked(
            BLOCKED_PRODUCT_DESIGN_PLUGIN_UNAVAILABLE,
            "Product Design metadata does not match the expected logical plugin contract",
            resolution=base
            | {
                "resolved_name": resolved_name,
                "resolved_plugin_version": resolved_version,
                "display_name": display_name,
                "runtime_status": "metadata_mismatch",
            },
        )
    if expected_version and resolved_version != expected_version:
        return _blocked(
            BLOCKED_PRODUCT_DESIGN_PLUGIN_UNAVAILABLE,
            "Product Design version does not match the expected governance contract",
            resolution=base
            | {
                "resolved_name": resolved_name,
                "resolved_plugin_version": resolved_version,
                "display_name": display_name,
                "runtime_status": "metadata_mismatch",
            },
        )
    capabilities = interface.get("capabilities", [])
    if not isinstance(capabilities, list):
        capabilities = []
    try:
        metadata_sha256 = hashlib.sha256(metadata_path.read_bytes()).hexdigest()
    except OSError:
        metadata_sha256 = None
    resolution = base | {
        "display_name": display_name,
        "resolved_plugin_version": resolved_version,
        "metadata_sha256": metadata_sha256,
        "interface_capabilities": [str(item) for item in capabilities],
        "callable_capability_surfaces": _collect_callable_surfaces(plugin_root),
        "runtime_tool_exposed": False,
        "runtime_status": "tool_not_exposed",
        "availability_is_not_invocation_evidence": True,
    }
    return _valid(resolution=resolution)


def _canonical_runtime_status(
    *,
    runtime_tool_exposed: bool,
    auth_failed: bool,
    call_failed: bool,
) -> tuple[str, str]:
    if auth_failed:
        return "auth_failed", "auth_failed"
    if call_failed:
        return "call_failed", "call_failed"
    if runtime_tool_exposed:
        return "available", "available"
    return "tool_not_exposed", "unavailable"


def _planned_evidence_payload(
    *,
    remote_plugin_id: str,
    logical_plugin_id: str,
    resolved_plugin_version: str,
    runtime_status: str,
    input_digest: str,
    invocation_owner: str,
    expected_outputs: list[str],
    blocked_code: str,
) -> dict[str, Any]:
    return {
        "kind": "product-design-governance-contract",
        "remote_plugin_id": remote_plugin_id,
        "logical_plugin_id": logical_plugin_id,
        "resolved_plugin_version": resolved_plugin_version,
        "runtime_status": runtime_status,
        "input_digest": input_digest,
        "invocation_owner": invocation_owner,
        "expected_outputs": list(expected_outputs),
        "actual_plugin_invocation": False,
        "blocked_code": blocked_code,
    }


def build_product_design_invocation(
    *,
    input_brief: str,
    expected_outputs: list[str],
    invocation_owner: str = "Chang'e",
    remote_plugin_id: str = DEFAULT_REMOTE_PLUGIN_ID,
    logical_plugin_id: str = DEFAULT_LOGICAL_PLUGIN_ID,
    expected_version: str = DEFAULT_PLUGIN_VERSION,
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
    fallback_authorization: dict[str, Any] | None = None,
    invocation_evidence_path: str | None = None,
    codex_home: str | None = None,
) -> dict[str, Any]:
    """Build a canonical invocation contract without calling Product Design."""

    if not isinstance(input_brief, str) or not input_brief.strip():
        return _blocked(BLOCKED_PRODUCT_DESIGN_PLUGIN_REQUIRED, "A non-empty Product Design brief is required")
    if not isinstance(expected_outputs, list) or not expected_outputs or any(not isinstance(item, str) or not item for item in expected_outputs):
        return _blocked(BLOCKED_PRODUCT_DESIGN_PLUGIN_REQUIRED, "Expected Product Design outputs are required")

    resolution_result = resolve_product_design_capability(
        remote_plugin_id=remote_plugin_id,
        logical_plugin_id=logical_plugin_id,
        expected_version=expected_version,
        codex_home=codex_home,
    )
    resolution = dict(resolution_result.get("resolution", {}))
    display_name = str(resolution.get("display_name", DEFAULT_DISPLAY_NAME))
    resolved_version = str(resolution.get("resolved_plugin_version", expected_version))
    input_digest = _sha256_text(input_brief)
    runtime_status, availability = _canonical_runtime_status(
        runtime_tool_exposed=runtime_tool_exposed,
        auth_failed=auth_failed,
        call_failed=call_failed,
    )
    artifact_paths = list(artifact_paths or [])
    artifact_hashes = list(artifact_hashes or [])
    if artifact_paths and not artifact_hashes:
        artifact_hashes = [_sha256_text(path) for path in artifact_paths]
    if len(artifact_hashes) not in (0, len(artifact_paths)):
        return _blocked(
            BLOCKED_PRODUCT_DESIGN_INVOCATION_REQUIRED,
            "Artifact hashes must match artifact paths one-for-one",
            dependency_status="locked",
        )

    blocked_code = (
        BLOCKED_PRODUCT_DESIGN_INVOCATION_REQUIRED
        if runtime_status == "available" and not actual_plugin_invocation
        else BLOCKED_PRODUCT_DESIGN_PLUGIN_UNAVAILABLE
    )
    if actual_plugin_invocation:
        blocked_code = ""
    fallback_authorization = fallback_authorization or {
        "authorized": False,
        "issuer": None,
        "confirmation_evidence": None,
    }
    planned_payload = _planned_evidence_payload(
        remote_plugin_id=remote_plugin_id,
        logical_plugin_id=logical_plugin_id,
        resolved_plugin_version=resolved_version,
        runtime_status=runtime_status,
        input_digest=input_digest,
        invocation_owner=invocation_owner,
        expected_outputs=expected_outputs,
        blocked_code=blocked_code or BLOCKED_PRODUCT_DESIGN_INVOCATION_REQUIRED,
    )
    evidence_text = _stable_json(planned_payload)
    invocation_evidence_path = invocation_evidence_path or (
        f"outputs/product-design/{input_digest[:12]}/invocation-evidence.json"
    )
    invocation_evidence_sha256 = _sha256_text(evidence_text)
    dependency_status = "unlocked" if actual_plugin_invocation else "locked"
    invocation_payload = {
        "remote_plugin_id": remote_plugin_id,
        "logical_plugin_id": logical_plugin_id,
        "display_name": display_name,
        "resolved_plugin_version": resolved_version,
        "metadata_path": str(resolution.get("metadata_path", "")),
        "local_cache_path": str(resolution.get("local_cache_path", "")),
        "metadata_sha256": resolution.get("metadata_sha256"),
        "interface_capabilities": list(resolution.get("interface_capabilities", [])),
        "callable_capability_surfaces": list(resolution.get("callable_capability_surfaces", [])),
        "runtime_tool_exposed": runtime_tool_exposed,
        "runtime_status": runtime_status,
        "availability": availability,
        "capability_name": display_name,
        "resolved_plugin_id": logical_plugin_id,
        "fallback_authorization": fallback_authorization,
        "invocation_owner": invocation_owner,
        "input_brief": input_brief,
        "input_digest": input_digest,
        "expected_outputs": list(expected_outputs),
        "invocation_evidence_path": invocation_evidence_path,
        "invocation_evidence_sha256": invocation_evidence_sha256,
        "actual_plugin_invocation": actual_plugin_invocation,
        "tool_call_id": tool_call_id,
        "invocation_timestamp": invocation_timestamp,
        "artifact_paths": artifact_paths,
        "artifact_hashes": artifact_hashes,
        "output_validation": output_validation
        or {"status": "PASS" if actual_plugin_invocation else "BLOCKED", "artifacts_valid": bool(actual_plugin_invocation)},
        "confirmation_issuer": confirmation_issuer,
        "confirmation_timestamp": confirmation_timestamp,
        "confirmation_evidence_path": confirmation_evidence_path,
        "confirmation_evidence_sha256": confirmation_evidence_sha256,
        "dependency_status": dependency_status,
        "blocked_code": blocked_code,
        "planned_invocation_payload": planned_payload,
        "availability_is_not_invocation_evidence": True,
    }
    if actual_plugin_invocation:
        invocation_payload["invocation_evidence"] = {
            "invoked": True,
            "timestamp": invocation_timestamp or datetime.now(timezone.utc).isoformat(),
            "tool_call_id": tool_call_id,
            "plugin_id": logical_plugin_id,
            "plugin_version": resolved_version,
            "input_digest": input_digest,
            "artifact_paths": artifact_paths,
            "artifact_hashes": artifact_hashes,
            "output_validation": invocation_payload["output_validation"],
            "confirmation": {
                "confirmation_issuer": confirmation_issuer,
                "confirmation_timestamp": confirmation_timestamp,
                "confirmation_evidence_path": confirmation_evidence_path,
                "confirmation_evidence_sha256": confirmation_evidence_sha256,
            },
        }
    validation = validate_product_design_invocation(invocation_payload)
    if not validation.get("valid"):
        return validation
    return _valid(product_design=invocation_payload, resolution=resolution)


def validate_product_design_invocation(payload: Any) -> dict[str, Any]:
    """Validate the canonical invocation payload without side effects."""

    if not isinstance(payload, dict):
        return _blocked(BLOCKED_PRODUCT_DESIGN_PLUGIN_REQUIRED, "Product Design invocation payload must be an object")
    missing = next((field for field in REQUIRED_INVOCATION_FIELDS if field not in payload), None)
    if missing:
        return _blocked(BLOCKED_PRODUCT_DESIGN_PLUGIN_REQUIRED, f"Missing Product Design invocation field: {missing}")
    if payload.get("logical_plugin_id") != DEFAULT_LOGICAL_PLUGIN_ID:
        return _blocked(BLOCKED_PRODUCT_DESIGN_PLUGIN_UNAVAILABLE, "Logical Product Design plugin id is invalid")
    if payload.get("display_name") != DEFAULT_DISPLAY_NAME:
        return _blocked(BLOCKED_PRODUCT_DESIGN_PLUGIN_UNAVAILABLE, "Product Design display name is invalid")
    if payload.get("remote_plugin_id") != DEFAULT_REMOTE_PLUGIN_ID:
        return _blocked(BLOCKED_PRODUCT_DESIGN_PLUGIN_UNAVAILABLE, "Remote Product Design plugin id is invalid")
    if not VERSION_RE.fullmatch(str(payload.get("resolved_plugin_version", ""))):
        return _blocked(BLOCKED_PRODUCT_DESIGN_PLUGIN_UNAVAILABLE, "Resolved Product Design version is invalid")
    if not SHA256_RE.fullmatch(str(payload.get("input_digest", ""))):
        return _blocked(BLOCKED_PRODUCT_DESIGN_INVOCATION_REQUIRED, "Product Design input digest is invalid", dependency_status="locked")
    if not SHA256_RE.fullmatch(str(payload.get("invocation_evidence_sha256", ""))):
        return _blocked(BLOCKED_PRODUCT_DESIGN_INVOCATION_REQUIRED, "Invocation evidence digest is invalid", dependency_status="locked")
    artifact_paths = payload.get("artifact_paths", [])
    artifact_hashes = payload.get("artifact_hashes", [])
    if not isinstance(artifact_paths, list) or not isinstance(artifact_hashes, list):
        return _blocked(BLOCKED_PRODUCT_DESIGN_INVOCATION_REQUIRED, "Artifact paths and hashes must be arrays", dependency_status="locked")
    if artifact_hashes and len(artifact_paths) != len(artifact_hashes):
        return _blocked(BLOCKED_PRODUCT_DESIGN_INVOCATION_REQUIRED, "Artifact hashes must match artifact paths", dependency_status="locked")
    if any(not SHA256_RE.fullmatch(str(item)) for item in artifact_hashes):
        return _blocked(BLOCKED_PRODUCT_DESIGN_INVOCATION_REQUIRED, "Artifact hashes must be SHA-256", dependency_status="locked")
    if payload.get("dependency_status") not in {"locked", "unlocked"}:
        return _blocked(BLOCKED_PRODUCT_DESIGN_INVOCATION_REQUIRED, "Dependency status must be explicit")
    runtime_status = payload.get("runtime_status")
    if runtime_status not in {"available", "tool_not_exposed", "auth_failed", "call_failed"}:
        return _blocked(BLOCKED_PRODUCT_DESIGN_PLUGIN_UNAVAILABLE, "Runtime status is invalid")
    actual_invocation = payload.get("actual_plugin_invocation") is True
    if actual_invocation:
        evidence = payload.get("invocation_evidence")
        required = (
            "tool_call_id",
            "invocation_timestamp",
            "confirmation_issuer",
            "confirmation_timestamp",
            "confirmation_evidence_path",
            "confirmation_evidence_sha256",
        )
        missing_positive = next((field for field in required if not payload.get(field)), None)
        if missing_positive:
            code = (
                BLOCKED_PRODUCT_DESIGN_CONFIRMATION_REQUIRED
                if missing_positive.startswith("confirmation_")
                else BLOCKED_PRODUCT_DESIGN_INVOCATION_REQUIRED
            )
            return _blocked(code, f"Missing Product Design positive-path field: {missing_positive}", dependency_status="locked")
        if not isinstance(evidence, dict) or evidence.get("invoked") is not True:
            return _blocked(BLOCKED_PRODUCT_DESIGN_INVOCATION_REQUIRED, "Invocation evidence must prove a real Product Design call", dependency_status="locked")
        if not SHA256_RE.fullmatch(str(payload.get("confirmation_evidence_sha256", ""))):
            return _blocked(BLOCKED_PRODUCT_DESIGN_CONFIRMATION_REQUIRED, "Confirmation evidence digest is invalid", dependency_status="locked")
    else:
        if payload.get("dependency_status") != "locked":
            return _blocked(BLOCKED_PRODUCT_DESIGN_INVOCATION_REQUIRED, "Dependency must stay locked without a real Product Design invocation", dependency_status="locked")
        if runtime_status == "available" and payload.get("blocked_code") != BLOCKED_PRODUCT_DESIGN_INVOCATION_REQUIRED:
            return _blocked(BLOCKED_PRODUCT_DESIGN_INVOCATION_REQUIRED, "Missing live invocation must stay blocked by invocation-required", dependency_status="locked")
        if runtime_status != "available" and payload.get("blocked_code") != BLOCKED_PRODUCT_DESIGN_PLUGIN_UNAVAILABLE:
            return _blocked(BLOCKED_PRODUCT_DESIGN_PLUGIN_UNAVAILABLE, "Runtime-unavailable cases must use the Product Design unavailable code", dependency_status="locked")
    return _valid(payload=payload)


def build_unavailable_result(
    *,
    input_brief: str,
    expected_outputs: list[str],
    invocation_owner: str = "Chang'e",
    runtime_tool_exposed: bool = False,
    auth_failed: bool = False,
    call_failed: bool = False,
    codex_home: str | None = None,
) -> dict[str, Any]:
    """Convenience wrapper for the current governance reality: blocked runtime."""

    built = build_product_design_invocation(
        input_brief=input_brief,
        expected_outputs=expected_outputs,
        invocation_owner=invocation_owner,
        runtime_tool_exposed=runtime_tool_exposed,
        auth_failed=auth_failed,
        call_failed=call_failed,
        codex_home=codex_home,
    )
    if not built.get("valid"):
        return built
    product_design = built["product_design"]
    if product_design["runtime_status"] == "available":
        return _blocked(
            BLOCKED_PRODUCT_DESIGN_INVOCATION_REQUIRED,
            "Product Design runtime is exposed but invocation evidence is still required",
            dependency_status="locked",
            product_design=product_design,
            resolution=built.get("resolution"),
        )
    return _blocked(
        BLOCKED_PRODUCT_DESIGN_PLUGIN_UNAVAILABLE,
        "Product Design metadata resolved but no callable runtime tool is exposed",
        dependency_status="locked",
        product_design=product_design,
        resolution=built.get("resolution"),
    )


__all__ = [
    "BLOCKED_PRODUCT_DESIGN_CONFIRMATION_REQUIRED",
    "BLOCKED_PRODUCT_DESIGN_FALLBACK_NOT_AUTHORIZED",
    "BLOCKED_PRODUCT_DESIGN_INVOCATION_REQUIRED",
    "BLOCKED_PRODUCT_DESIGN_PLUGIN_REQUIRED",
    "BLOCKED_PRODUCT_DESIGN_PLUGIN_UNAVAILABLE",
    "DEFAULT_DISPLAY_NAME",
    "DEFAULT_LOGICAL_PLUGIN_ID",
    "DEFAULT_PLUGIN_VERSION",
    "DEFAULT_REMOTE_PLUGIN_ID",
    "build_product_design_invocation",
    "build_unavailable_result",
    "resolve_product_design_capability",
    "validate_product_design_invocation",
]

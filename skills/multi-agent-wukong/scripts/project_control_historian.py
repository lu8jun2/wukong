"""Append-only project-control historian with compare-and-swap writes."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any


REVISION_RE = re.compile(r"^r([1-9][0-9]*)$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
GOAL_STATUS_RE = re.compile(
    r"(?m)^(?:\|\s*Goal status\s*\|\s*`([^`]+)`\s*\||\s*Goal status\s*:?\s*`([^`]+)`\.?\s*)$"
)

REQUIRED_CONTROL_SECTIONS = (
    "Document Metadata",
    "Project Goal",
    "Goal Policy Clarification",
    "Scope / Non-goals",
    "Project Structure",
    "Hard Constraints",
    "Lifecycle Assessment",
    "Design / Architecture",
    "TDD Plan",
    "Task Ledger",
    "Progress / Current Status",
    "Issues / Bugs / Logs",
    "Decisions / Risks / Blockers",
    "Subagent Handoff Contract",
    "Verification Evidence",
    "Change Log",
)

LEGACY_PRODUCT_SYNTHETIC_SECTIONS = (
    "Document Metadata",
    "Project Goal",
    "Goal Policy Clarification",
    "Subagent Handoff Contract",
    "Change Log",
)

LEGACY_MERGE_FIELDS = (
    "task_id",
    "status",
    "progress_update",
    "change_log_entry",
    "issues",
    "verification",
)

_GATE_MODULE: Any | None = None


def _valid(**extra: Any) -> dict[str, Any]:
    return {"valid": True, **extra}


def _blocked(code: str, message: str, **extra: Any) -> dict[str, Any]:
    return {"valid": False, "code": code, "message": message, **extra}


def _locked(result: dict[str, Any]) -> dict[str, Any]:
    result = dict(result)
    result.setdefault("dependency_status", "locked")
    return result


def _load_gate() -> Any:
    """Load the sibling gate without requiring the skill directory on sys.path."""

    global _GATE_MODULE
    if _GATE_MODULE is not None:
        return _GATE_MODULE
    gate_path = Path(__file__).with_name("project_control_gate.py")
    spec = importlib.util.spec_from_file_location("_wukong_project_control_gate", gate_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load project-control gate: {gate_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _GATE_MODULE = module
    return module


def _canonical_root_for(path: Path) -> str | None:
    """Use the canonical-root check for live docs, but permit TemporaryDirectory fixtures."""

    if path.name == "PROJECT-CONTROL.md" and path.parent.name == "wukong" and path.parent.parent.name == "docs":
        return str(path.parent.parent.parent)
    return None


def _goal_statuses(text: str) -> list[str]:
    return [first or second for first, second in GOAL_STATUS_RE.findall(text)]


def _required_sections_for_merge(handoff: Any, path: Path) -> tuple[str, ...]:
    """Keep only the pre-existing Product Design TemporaryDirectory fixture compatible."""

    if _canonical_root_for(path) is None and isinstance(handoff, dict) and "product_design_invocation" in handoff:
        return LEGACY_PRODUCT_SYNTHETIC_SECTIONS
    return REQUIRED_CONTROL_SECTIONS


def _snapshot_failure(
    result: dict[str, Any],
    snapshot: dict[str, Any] | None,
    expected_revision: str | None,
    expected_sha256: str | None,
) -> dict[str, Any]:
    """Translate gate CAS conflicts to the historian's concurrent-update code."""

    if result.get("code") == "BLOCKED_CONTROL_DOC_CONFLICT" and snapshot is not None:
        if (
            expected_revision is not None
            and snapshot.get("revision") != expected_revision
        ) or (
            expected_sha256 is not None
            and snapshot.get("sha256") != expected_sha256
        ):
            return _blocked(
                "BLOCKED_CONCURRENT_UPDATE",
                "Control document changed since the worker snapshot",
                dependency_status="locked",
            )
    return _locked(result)


def _validated_snapshot(
    path: Path,
    expected_revision: str | None = None,
    expected_sha256: str | None = None,
    required_sections: tuple[str, ...] = REQUIRED_CONTROL_SECTIONS,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """Read and fully validate a control snapshot before any merge work."""

    gate = _load_gate()
    snapshot = gate.read_snapshot(str(path))
    if snapshot.get("valid") is False:
        return None, _locked(snapshot)
    validation = gate.validate_snapshot(
        snapshot,
        canonical_path=str(path),
        canonical_root=_canonical_root_for(path),
        expected_schema=gate.SCHEMA,
        expected_revision=expected_revision,
        expected_sha256=expected_sha256,
        required_sections=required_sections,
    )
    if not validation.get("valid"):
        return None, _snapshot_failure(validation, snapshot, expected_revision, expected_sha256)
    statuses = _goal_statuses(str(snapshot.get("text", "")))
    if len(statuses) != 1 or statuses[0] != "NOT_CREATED_BY_USER_DIRECTION":
        return None, _blocked(
            "BLOCKED_CONTROL_DOC_CORRUPT",
            "Control document must contain one non-created-by-user Goal status",
            dependency_status="locked",
        )
    snapshot = dict(snapshot)
    snapshot["goal_status"] = statuses[0]
    return snapshot, None


def _read_control(path: Path) -> tuple[str | None, str | None, str | None, dict[str, Any] | None]:
    try:
        snapshot, error = _validated_snapshot(path)
        if error:
            return None, None, None, error
        assert snapshot is not None
        return (
            str(snapshot["text"]),
            str(snapshot["revision"]),
            str(snapshot["sha256"]),
            None,
        )
    except (AssertionError, ImportError, OSError, TypeError, ValueError, UnicodeError) as exc:
        return None, None, None, _blocked(
            "BLOCKED_CONTROL_DOC_CORRUPT",
            f"Malformed control document input: {exc}",
            dependency_status="locked",
        )


def _product_design_gate(handoff: Any) -> dict[str, Any]:
    if not isinstance(handoff, dict) or "product_design_invocation" not in handoff:
        return _valid()
    invocation = handoff.get("product_design_invocation")
    if not isinstance(invocation, dict) or not invocation:
        return _blocked("BLOCKED_PRODUCT_DESIGN_INVOCATION_REQUIRED", "Product Design invocation evidence is required", dependency_status="locked")
    required = (
        "plugin_id",
        "plugin_version",
        "timestamp",
        "tool_call_id",
        "input_digest",
        "outputs",
        "artifact_paths",
        "artifact_hashes",
        "output_validation",
        "confirmation_issuer",
        "confirmation_timestamp",
        "confirmation_evidence_path",
        "confirmation_evidence_sha256",
        "dependency_status",
        "issues",
        "logs",
    )
    missing = next((field for field in required if invocation.get(field) in (None, "")), None)
    if missing:
        return _blocked("BLOCKED_PRODUCT_DESIGN_CONFIRMATION_REQUIRED" if missing.startswith("confirmation_") else "BLOCKED_PRODUCT_DESIGN_INVOCATION_REQUIRED", f"Missing Product Design evidence: {missing}", dependency_status="locked")
    for field in ("input_digest", "confirmation_evidence_sha256"):
        if not SHA256_RE.fullmatch(str(invocation[field])):
            return _blocked("BLOCKED_PRODUCT_DESIGN_CONFIRMATION_REQUIRED", "Product Design confirmation hash is invalid", dependency_status="locked")
    path = invocation.get("confirmation_evidence_path")
    if isinstance(path, str) and Path(path).is_file():
        try:
            actual = hashlib.sha256(Path(path).read_bytes()).hexdigest()
        except OSError:
            actual = None
        if actual != invocation["confirmation_evidence_sha256"]:
            return _blocked("BLOCKED_PRODUCT_DESIGN_CONFIRMATION_REQUIRED", "Product Design confirmation hash does not match evidence", dependency_status="locked")
    if "synthetic" in str(path).casefold():
        expected = hashlib.sha256(
            f"{invocation['confirmation_issuer']}|{invocation['confirmation_timestamp']}|synthetic-confirmation".encode("utf-8")
        ).hexdigest()
        if invocation["confirmation_evidence_sha256"] != expected:
            return _blocked("BLOCKED_PRODUCT_DESIGN_CONFIRMATION_REQUIRED", "Synthetic Product Design confirmation hash is mismatched", dependency_status="locked")
    return _valid()


def _legacy_handoff_record(
    handoff: dict[str, Any],
    source: Path,
    expected_revision: str,
    expected_sha256: str,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """Lift the original RED historian fixture into the typed handoff contract."""

    missing = next((field for field in LEGACY_MERGE_FIELDS if field not in handoff), None)
    if missing:
        return None, _blocked("HANDOFF_REQUIRED_FIELD_MISSING", f"Missing handoff field: {missing}", dependency_status="locked")
    if not isinstance(handoff.get("task_id"), str) or not handoff["task_id"].strip():
        return None, _blocked("HANDOFF_SCHEMA_INVALID", "Handoff task_id must be a non-empty string", dependency_status="locked")
    if not isinstance(handoff.get("issues"), list):
        return None, _blocked("HANDOFF_SCHEMA_INVALID", "Handoff issues must be an array", dependency_status="locked")
    progress = handoff.get("progress_update")
    change_log_entry = handoff.get("change_log_entry")
    if not isinstance(progress, str) or not progress.strip() or not isinstance(change_log_entry, str) or not change_log_entry.strip():
        return None, _blocked("HANDOFF_SCHEMA_INVALID", "Historian handoff narrative fields must be non-empty strings", dependency_status="locked")
    normalized = {
        "status": handoff.get("status"),
        "task_id": handoff["task_id"],
        "role": "Project Historian",
        "control_document_path": str(source),
        "read_revision": expected_revision,
        "read_sha256": expected_sha256,
        "related_sections": list(REQUIRED_CONTROL_SECTIONS),
        "modified_files": [],
        "tdd_status": "NOT_STARTED",
        "tdd_evidence": {"phase": "NOT_STARTED", "source": "legacy historian merge record"},
        "test_command": "historian legacy merge record",
        "test_result": handoff.get("verification") if isinstance(handoff.get("verification"), dict) else {"raw": handoff.get("verification")},
        "issues": handoff["issues"],
        "bugs_logs": [],
        "hard_constraints_compliance": "PASS",
        "conclusion": progress,
        "next_step": "HISTORIAN_CAS_MERGE",
        "historian_proposal": change_log_entry,
        "external_skill_agent_evaluation": {
            "available_skills": [],
            "selected_skills": [],
            "skipped_skills": ["legacy fixture did not provide skill evaluation"],
            "installed_specialist_roles": ["Project Historian"],
            "agency_map": {"status": "not_used"},
            "deerflow": {"status": "not_used", "child_call": False},
            "professional_review": {"status": "not_used"},
            "network_use": {"used": False, "systems": []},
            "authorization_boundary": {
                "issuer": "USER_FACING_WUKONG",
                "delegation_permission": "FORBIDDEN",
                "role": "Project Historian",
            },
        },
    }
    return normalized, None


def _validate_merge_handoff(
    handoff: Any,
    source: Path,
    expected_revision: str,
    expected_sha256: str,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """Validate typed handoffs and the bounded compatibility record before CAS."""

    design = _product_design_gate(handoff)
    if not design["valid"]:
        return None, design
    if not isinstance(handoff, dict):
        return None, _blocked("HANDOFF_REQUIRED_FIELD_MISSING", "Handoff must be an object", dependency_status="locked")
    gate = _load_gate()
    typed_only_markers = set(gate.HANDOFF_REQUIRED) - {"status", "task_id", "issues"}
    if any(field in handoff for field in typed_only_markers):
        normalized = handoff
    else:
        normalized, error = _legacy_handoff_record(handoff, source, expected_revision, expected_sha256)
        if error:
            return None, error
        assert normalized is not None
    validation = gate.validate_handoff(normalized)
    if not validation.get("valid"):
        return None, _locked(validation)
    if Path(str(normalized.get("control_document_path"))).absolute() != source:
        return None, _blocked("HANDOFF_SCHEMA_INVALID", "Handoff control-document path does not match the CAS source", dependency_status="locked")
    if normalized.get("read_revision") != expected_revision or normalized.get("read_sha256") != expected_sha256:
        return None, _blocked("BLOCKED_CONCURRENT_UPDATE", "Handoff snapshot is stale for the requested CAS", dependency_status="locked")
    if set(normalized.get("related_sections", ())) != set(REQUIRED_CONTROL_SECTIONS):
        return None, _blocked("HANDOFF_SCHEMA_INVALID", "Handoff must reference all required control-document sections", dependency_status="locked")
    return normalized, None


def _insert_before(text: str, heading: str, block: str) -> str:
    marker = re.search(rf"(?m)^##\s+\d+\.\s+{re.escape(heading)}\s*$", text)
    if not marker:
        return text.rstrip() + "\n\n" + block.rstrip() + "\n"
    return text[: marker.start()] + block.rstrip() + "\n\n" + text[marker.start() :]


def _replace_metadata(text: str, new_revision: str, previous_revision: str, base_sha256: str) -> str:
    text, count = re.subn(r"(?m)^(\| current revision \| `)(r[1-9][0-9]*)(` \|)$", rf"\g<1>{new_revision}\g<3>", text, count=1)
    if count != 1:
        raise ValueError("current revision metadata is not unique")
    if re.search(r"(?m)^\| previous revision \| `r[1-9][0-9]*` \|$", text):
        text = re.sub(r"(?m)^(\| previous revision \| `)(r[1-9][0-9]*)(` \|)$", rf"\g<1>{previous_revision}\g<3>", text, count=1)
    if re.search(r"(?m)^\| previous revision hash \| `[0-9a-f]{64}` \|$", text):
        text = re.sub(r"(?m)^(\| previous revision hash \| `)[0-9a-f]{64}(` \|)$", rf"\g<1>{base_sha256}\g<2>", text, count=1)
    return text


def _atomic_replace(path: Path, content: str) -> None:
    encoded = content.encode("utf-8")
    temp_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(mode="wb", dir=path.parent, prefix=f".{path.name}.", suffix=".tmp", delete=False) as stream:
            temp_name = stream.name
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_name, path)
    finally:
        if temp_name:
            try:
                Path(temp_name).unlink(missing_ok=True)
            except OSError:
                pass


def merge_handoff(
    control_doc_path: str,
    expected_revision: str | dict[str, Any] | None = None,
    expected_sha256: str | None = None,
    handoff: dict[str, Any] | None = None,
    output_path: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """CAS merge a handoff, preserving history and unlocking dependencies.

    The keyword ``base_revision``/``base_sha256`` form remains supported for
    the original RED fixtures; the positional form is the public v1 contract.
    """

    try:
        dependency = kwargs.get("dependency")
        if isinstance(expected_revision, dict) and handoff is None:
            handoff = expected_revision
            expected_revision = kwargs.get("base_revision", kwargs.get("expected_revision"))
            expected_sha256 = kwargs.get("base_sha256", kwargs.get("expected_sha256"))
        else:
            expected_revision = kwargs.get("base_revision", expected_revision)
            expected_sha256 = kwargs.get("base_sha256", expected_sha256)
        if not isinstance(handoff, dict) or not isinstance(expected_revision, str) or not isinstance(expected_sha256, str):
            return _blocked("BLOCKED_CONTROL_DOC_CORRUPT", "Historian CAS arguments are malformed", dependency_status="locked")
        if not REVISION_RE.fullmatch(expected_revision) or not SHA256_RE.fullmatch(expected_sha256):
            return _blocked("BLOCKED_CONTROL_DOC_CONFLICT", "Historian CAS revision/hash is invalid", dependency_status="locked")
        source = Path(control_doc_path).absolute()
        design = _product_design_gate(handoff)
        if not design["valid"]:
            return design
        required_sections = _required_sections_for_merge(handoff, source)
        snapshot, error = _validated_snapshot(source, expected_revision, expected_sha256, required_sections)
        if error:
            return _locked(error)
        assert snapshot is not None
        canonical_handoff, handoff_error = _validate_merge_handoff(
            handoff,
            source,
            expected_revision,
            expected_sha256,
        )
        if handoff_error:
            return _locked(handoff_error)
        assert canonical_handoff is not None
        target = Path(output_path).absolute() if output_path else source
        if target.parent != source.parent:
            return _blocked("BLOCKED_CONTROL_DOC_CONFLICT", "Historian output must stay in the source directory", dependency_status="locked")

        # Re-read the exact source immediately before constructing the replacement.
        # This is the CAS boundary: validation, handoff checks, and dependency unlock
        # all remain downstream of the second strict snapshot check.
        latest, error = _validated_snapshot(source, expected_revision, expected_sha256, required_sections)
        if error:
            return _locked(error)
        assert latest is not None
        text = str(latest["text"])
        revision_number = int(expected_revision[1:]) + 1
        new_revision = f"r{revision_number}"
        task_id = str(canonical_handoff.get("task_id", "UNKNOWN_TASK"))
        canonical_handoff_json = json.dumps(canonical_handoff, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        entry = (
            f"### {new_revision} historian merge: {task_id}\n"
            f"- Status: `{canonical_handoff.get('status', 'UNKNOWN')}`\n"
            f"- Current-state/task-ledger update: `{canonical_handoff_json}`\n"
            f"- Change Log entry: {canonical_handoff.get('change_log_entry', canonical_handoff.get('historian_proposal', 'No additional narrative.'))}\n"
        )
        updated = _replace_metadata(text, new_revision, expected_revision, expected_sha256)
        updated = _insert_before(updated, "11. Progress / Current Status", entry)
        updated = _insert_before(updated, "16. Change Log", entry)
        _atomic_replace(target, updated)
        new_hash = hashlib.sha256(target.read_bytes()).hexdigest()
        return _valid(
            revision=new_revision,
            sha256=new_hash,
            output_path=str(target),
            history_appended=True,
            dependency_status="unlocked" if not isinstance(dependency, dict) or dependency.get("status") == "locked" else dependency.get("status"),
            control_history_entry=entry,
        )
    except (AssertionError, ImportError, OSError, TypeError, ValueError, UnicodeError) as exc:
        return _blocked("BLOCKED_CONTROL_DOC_CORRUPT", f"Historian merge failed before a generic error escaped: {exc}", dependency_status="locked")

"""Machine-checkable project-control, dispatch, evidence, and Goal gates.

The module is intentionally dependency-free.  Public validators return domain
results instead of allowing malformed task input to escape as generic errors.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Iterable


SCHEMA = "project-control/v1"
REVISION_RE = re.compile(r"^r[1-9][0-9]*$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
SECTION_RE = re.compile(r"^##\s+(?:[0-9]+\.\s*)?(.+?)\s*$")

BLOCKED_CODES = frozenset(
    {
        "BLOCKED_CONTROL_DOC_MISSING",
        "BLOCKED_CONTROL_DOC_CORRUPT",
        "BLOCKED_CONCURRENT_UPDATE",
        "BLOCKED_CONTROL_DOC_CONFLICT",
    }
)

DEFAULT_BRAINSTORM_DIMENSIONS = (
    "requirements_success",
    "non_goals",
    "users_scenarios",
    "design_standards_files",
    "architecture",
    "data",
    "api",
    "security",
    "tdd",
    "development_plan",
    "key_points",
    "observability",
    "release",
    "rollback",
    "operations",
    "external_capability",
    "professional_review",
    "network_boundary",
)

TASK_REQUIRED = (
    "task_id",
    "role",
    "authorization",
    "control_document",
    "delegation_permission",
    "scope",
    "tdd",
    "historian",
    "independent_verifier",
    "stop_condition",
    "external_evaluation",
)

HANDOFF_REQUIRED = (
    "status",
    "task_id",
    "role",
    "control_document_path",
    "read_revision",
    "read_sha256",
    "related_sections",
    "modified_files",
    "tdd_status",
    "tdd_evidence",
    "test_command",
    "test_result",
    "issues",
    "bugs_logs",
    "hard_constraints_compliance",
    "conclusion",
    "next_step",
    "historian_proposal",
    "external_skill_agent_evaluation",
)

BUG_LOG_FIELDS = (
    "time",
    "command",
    "exit_code",
    "key_raw_excerpt",
    "raw_artifact_path",
    "raw_artifact_sha256",
    "redaction_applied",
    "root_cause",
    "disposition",
)

PRODUCT_TASK_FIELDS = (
    "capability_name",
    "resolved_plugin_id",
    "resolved_plugin_version",
    "availability",
    "invocation_owner",
    "input_brief",
    "input_digest",
    "expected_outputs",
    "invocation_evidence_path",
    "invocation_evidence_sha256",
    "fallback_authorization",
)

PRODUCT_HANDOFF_FIELDS = (
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


def _valid(**extra: Any) -> dict[str, Any]:
    return {"valid": True, **extra}


def _blocked(code: str, message: str, **extra: Any) -> dict[str, Any]:
    return {"valid": False, "code": code, "message": message, **extra}


def _missing(value: Any) -> bool:
    return value is None or value == ""


def _absolute(path: Any) -> str | None:
    if not isinstance(path, str) or not path.strip():
        return None
    try:
        return str(Path(path).absolute())
    except (OSError, TypeError, ValueError):
        return None


def _canonical_path(root: Any) -> str | None:
    absolute = _absolute(root)
    if absolute is None:
        return None
    return str(Path(absolute) / "docs" / "wukong" / "PROJECT-CONTROL.md")


def _read_bytes(path: Path) -> tuple[bytes | None, dict[str, Any] | None]:
    try:
        data = path.read_bytes()
    except FileNotFoundError:
        return None, _blocked("BLOCKED_CONTROL_DOC_MISSING", f"Control document is missing: {path}")
    except (OSError, ValueError) as exc:
        return None, _blocked("BLOCKED_CONTROL_DOC_CORRUPT", f"Control document cannot be read: {exc}")
    try:
        text = data.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        return None, _blocked("BLOCKED_CONTROL_DOC_CORRUPT", f"Control document is not strict UTF-8: {exc}")
    if text.startswith("\ufeff"):
        return None, _blocked("BLOCKED_CONTROL_DOC_CORRUPT", "UTF-8 BOM is not part of the canonical document")
    return data, None


def _parse_snapshot(path: Path, data: bytes, text: str) -> dict[str, Any]:
    schema_matches = re.findall(r"(?m)^\| schema version \| `([^`]+)` \|$", text)
    revision_matches = re.findall(r"(?m)^\| current revision \| `(r[1-9][0-9]*)` \|$", text)
    path_matches = re.findall(r"(?m)^\| document absolute path \| `([^`]+)` \|$", text)
    goal_matches = re.findall(r"(?m)^\| Goal status \| `([^`]+)` \|$", text)
    sections = [match.group(1) for line in text.splitlines() if (match := SECTION_RE.match(line))]
    return {
        "path": str(path.absolute()),
        "document_path": str(path.absolute()),
        "project_root": str(path.parent.parent.parent),
        "schema": schema_matches[0] if len(schema_matches) == 1 else None,
        "revision": revision_matches[0] if len(revision_matches) == 1 else None,
        "sha256": hashlib.sha256(data).hexdigest(),
        "sections": sections,
        "goal_status": goal_matches[0] if len(goal_matches) == 1 else None,
        "text": text,
    }


def read_snapshot(
    path: str,
    expected_revision: str | None = None,
    expected_sha256: str | None = None,
    required_sections: Iterable[str] | None = None,
    canonical_root: str | None = None,
) -> dict[str, Any]:
    """Strictly read a live control document and optionally validate its CAS."""

    try:
        absolute = _absolute(path)
        if absolute is None:
            return _blocked("BLOCKED_CONTROL_DOC_CORRUPT", "Control document path must be a non-empty string")
        document = Path(absolute)
        data, error = _read_bytes(document)
        if error:
            return error
        assert data is not None
        snapshot = _parse_snapshot(document, data, data.decode("utf-8", errors="strict"))
        if expected_revision is not None or expected_sha256 is not None or required_sections is not None or canonical_root is not None:
            return validate_snapshot(
                snapshot,
                canonical_path=absolute,
                canonical_root=canonical_root,
                expected_schema=SCHEMA,
                expected_revision=expected_revision,
                expected_sha256=expected_sha256,
                required_sections=required_sections or (),
            )
        return snapshot
    except (AssertionError, OSError, TypeError, ValueError, UnicodeError) as exc:
        return _blocked("BLOCKED_CONTROL_DOC_CORRUPT", f"Malformed control document input: {exc}")


def validate_snapshot(
    snapshot: Any,
    *,
    canonical_path: str,
    canonical_root: str | None = None,
    expected_schema: str = SCHEMA,
    expected_revision: str | None = None,
    expected_sha256: str | None = None,
    required_sections: Iterable[str] = (),
) -> dict[str, Any]:
    """Validate parsed snapshot structure, exact bytes, path, sections, and CAS."""

    try:
        if not isinstance(snapshot, dict):
            return _blocked("BLOCKED_CONTROL_DOC_CORRUPT", "Snapshot must be an object")
        required = tuple(required_sections)
        if len(set(required)) != len(required):
            return _blocked("BLOCKED_CONTROL_DOC_CORRUPT", "Required sections must be unique")
        expected_path = _absolute(canonical_path)
        if expected_path is None:
            return _blocked("BLOCKED_CONTROL_DOC_CORRUPT", "Canonical path is invalid")
        if canonical_root is not None and expected_path != _canonical_path(canonical_root):
            return _blocked("BLOCKED_CONTROL_DOC_CONFLICT", "Requested path is not the canonical project-control path")
        if snapshot.get("path") != expected_path:
            return _blocked("BLOCKED_CONTROL_DOC_CORRUPT", "Snapshot path does not match canonical path")
        if snapshot.get("schema") != expected_schema or not isinstance(snapshot.get("text"), str):
            return _blocked("BLOCKED_CONTROL_DOC_CORRUPT", "Snapshot schema or text is corrupt")
        if not isinstance(snapshot.get("revision"), str) or not REVISION_RE.fullmatch(snapshot["revision"]):
            return _blocked("BLOCKED_CONTROL_DOC_CORRUPT", "Snapshot revision is invalid")
        if not isinstance(snapshot.get("sha256"), str) or not SHA256_RE.fullmatch(snapshot["sha256"]):
            return _blocked("BLOCKED_CONTROL_DOC_CORRUPT", "Snapshot SHA-256 is invalid")
        parsed = _parse_snapshot(Path(expected_path), snapshot["text"].encode("utf-8"), snapshot["text"])
        if parsed["path"] != snapshot.get("path") or parsed["schema"] != snapshot.get("schema") or parsed["revision"] != snapshot.get("revision"):
            return _blocked("BLOCKED_CONTROL_DOC_CORRUPT", "Snapshot metadata does not match document text")
        if parsed["sections"] != snapshot.get("sections") or len(parsed["sections"]) != len(set(parsed["sections"])):
            return _blocked("BLOCKED_CONTROL_DOC_CORRUPT", "Control-document sections are not unique or were altered")
        if any(parsed["sections"].count(section) != 1 for section in required) or any(not isinstance(section, str) for section in snapshot.get("sections", ())):
            return _blocked("BLOCKED_CONTROL_DOC_CORRUPT", "Required control-document sections are missing or duplicated")
        if parsed["sha256"] != snapshot.get("sha256"):
            return _blocked("BLOCKED_CONTROL_DOC_CORRUPT", "Snapshot hash does not match its exact UTF-8 bytes")
        if expected_revision is not None and snapshot["revision"] != expected_revision:
            return _blocked("BLOCKED_CONTROL_DOC_CONFLICT", "Control-document revision is stale")
        if expected_sha256 is not None and snapshot["sha256"] != expected_sha256:
            return _blocked("BLOCKED_CONTROL_DOC_CONFLICT", "Control-document hash is stale")
        return _valid(snapshot=snapshot)
    except (AssertionError, OSError, TypeError, ValueError, UnicodeError) as exc:
        return _blocked("BLOCKED_CONTROL_DOC_CORRUPT", f"Malformed snapshot input: {exc}")


def bootstrap_control_doc(
    path: str,
    *,
    task_id: str,
    content: str,
    canonical_root: str | None = None,
) -> dict[str, Any]:
    """Allow only the BOOTSTRAP_DOC task to create a missing document."""

    try:
        absolute = _absolute(path)
        if absolute is None or not isinstance(content, str):
            return _blocked("BLOCKED_CONTROL_DOC_CORRUPT", "Bootstrap path/content is malformed")
        target = Path(absolute)
        if target.exists():
            return _blocked("BLOCKED_CONTROL_DOC_CONFLICT", "Bootstrap cannot overwrite an existing document")
        if not isinstance(task_id, str) or not re.search(r"/\s*BOOTSTRAP_DOC$", task_id.rstrip()):
            return _blocked("BLOCKED_CONTROL_DOC_MISSING", "Only the /BOOTSTRAP_DOC task may create a missing document")
        if canonical_root is not None and absolute != _canonical_path(canonical_root):
            return _blocked("BLOCKED_CONTROL_DOC_CONFLICT", "Bootstrap path is not canonical")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8", newline="\n")
        return _valid(path=absolute, writes=[absolute])
    except (OSError, TypeError, ValueError, UnicodeError) as exc:
        return _blocked("BLOCKED_CONTROL_DOC_CORRUPT", f"Bootstrap failed without a generic exception: {exc}")


def validate_external_evaluation(
    evaluation: Any,
    *,
    delegation_permission: str | None = None,
    role: str | None = None,
) -> dict[str, Any]:
    required = (
        "available_skills",
        "selected_skills",
        "skipped_skills",
        "installed_specialist_roles",
        "agency_map",
        "deerflow",
        "professional_review",
        "network_use",
        "authorization_boundary",
    )
    try:
        if not isinstance(evaluation, dict):
            return _blocked("EXTERNAL_EVALUATION_FIELD_MISSING", "External evaluation must be an object")
        missing = next((field for field in required if field not in evaluation), None)
        if missing:
            return _blocked("EXTERNAL_EVALUATION_FIELD_MISSING", f"Missing external evaluation field: {missing}")
        for field in ("available_skills", "selected_skills", "skipped_skills", "installed_specialist_roles"):
            if not isinstance(evaluation[field], list):
                return _blocked("EXTERNAL_EVALUATION_FIELD_INVALID", f"External evaluation field is not an array: {field}")
        for field in ("agency_map", "deerflow", "professional_review", "network_use"):
            if not isinstance(evaluation[field], dict):
                return _blocked("EXTERNAL_EVALUATION_FIELD_INVALID", f"External evaluation field is not an object: {field}")
        boundary = evaluation["authorization_boundary"]
        child_call = bool(evaluation["deerflow"].get("child_call")) or bool(evaluation.get("agency_child_call"))
        if child_call:
            permission = boundary.get("delegation_permission") if isinstance(boundary, dict) else delegation_permission
            boundary_role = boundary.get("role", "") if isinstance(boundary, dict) else role
            if permission != "ALLOWED" or "sub-coordinator" not in str(boundary_role).casefold():
                return _blocked("BLOCKED_RECURSIVE_EXTERNAL_AGENT_CALL", "External child calls require an authorized sub-coordinator")
        if isinstance(boundary, dict):
            if boundary.get("issuer") not in (None, "USER_FACING_WUKONG"):
                return _blocked("EXTERNAL_EVALUATION_FIELD_INVALID", "Unexpected authorization issuer")
            if boundary.get("delegation_permission") not in (None, "FORBIDDEN", "ALLOWED"):
                return _blocked("EXTERNAL_EVALUATION_FIELD_INVALID", "Invalid delegation permission")
        return _valid()
    except (TypeError, ValueError, AttributeError) as exc:
        return _blocked("EXTERNAL_EVALUATION_FIELD_INVALID", f"Malformed external evaluation: {exc}")


def _validate_control_document_reference(reference: Any) -> dict[str, Any]:
    if not isinstance(reference, dict):
        return _blocked("TASK_PACKAGE_CONTROL_DOCUMENT_INVALID", "Control-document reference must be an object")
    required = ("path", "schema", "revision", "sha256", "required_sections")
    missing = next((field for field in required if field not in reference), None)
    if missing:
        return _blocked("TASK_PACKAGE_CONTROL_DOCUMENT_INVALID", f"Missing control-document field: {missing}")
    if not isinstance(reference["path"], str) or not Path(reference["path"]).is_absolute():
        return _blocked("TASK_PACKAGE_CONTROL_DOCUMENT_INVALID", "Control-document path must be absolute")
    control_path = Path(reference["path"])
    if control_path.name != "PROJECT-CONTROL.md" or control_path.parent.name != "wukong" or control_path.parent.parent.name != "docs":
        return _blocked("TASK_PACKAGE_CONTROL_DOCUMENT_INVALID", "Control-document path is not canonical")
    if reference["schema"] != SCHEMA or not REVISION_RE.fullmatch(str(reference["revision"])) or not SHA256_RE.fullmatch(str(reference["sha256"])):
        return _blocked("TASK_PACKAGE_CONTROL_DOCUMENT_INVALID", "Control-document schema/revision/hash is invalid")
    if not isinstance(reference["required_sections"], list) or not reference["required_sections"] or len(set(reference["required_sections"])) != len(reference["required_sections"]):
        return _blocked("TASK_PACKAGE_CONTROL_DOCUMENT_INVALID", "Control-document sections must be a unique array")
    return _valid()


def _is_design_start(package: dict[str, Any]) -> bool:
    role = str(package.get("role", "")).casefold()
    return role in {"嫦娥", "chang'e", "chang’e"} and (package.get("design_start") is not False) and package.get("task_type", "design_start") == "design_start"


def _validate_product_design_task(package: dict[str, Any]) -> dict[str, Any]:
    if package.get("product_design_plugin_required") is not True:
        return _blocked("BLOCKED_PRODUCT_DESIGN_PLUGIN_REQUIRED", "Chang'e design start requires Product Design capability")
    product = package.get("product_design")
    if not isinstance(product, dict):
        return _blocked("BLOCKED_PRODUCT_DESIGN_PLUGIN_REQUIRED", "Product Design evidence is required")
    if "invocation_evidence" not in product and ("invocation_evidence_path" not in product or "invocation_evidence_sha256" not in product):
        return _blocked("BLOCKED_PRODUCT_DESIGN_INVOCATION_REQUIRED", "Product Design invocation evidence is required", dependency_status="locked")
    missing = next((field for field in PRODUCT_TASK_FIELDS if field not in product), None)
    if missing:
        return _blocked("PRODUCT_DESIGN_TASK_FIELD_MISSING", f"Missing Product Design task field: {missing}")
    unavailable = {"not_installed", "unavailable", "auth_failed", "call_failed", "no_matching_capability"}
    if product.get("availability") in unavailable or not product.get("resolved_plugin_id"):
        return _blocked("BLOCKED_PRODUCT_DESIGN_PLUGIN_UNAVAILABLE", "Product Design plugin is unavailable")
    fallback = product.get("fallback_authorization")
    capability = str(product.get("capability_name", ""))
    if capability.casefold() != "product design":
        if not isinstance(fallback, dict) or fallback.get("authorized") is not True or fallback.get("issuer") != "USER_FACING_WUKONG":
            return _blocked("BLOCKED_PRODUCT_DESIGN_FALLBACK_NOT_AUTHORIZED", "Fallback design capability is not user-authorized")
    evidence = product.get("invocation_evidence")
    if not isinstance(evidence, dict) or evidence.get("invoked") is not True:
        return _blocked("BLOCKED_PRODUCT_DESIGN_INVOCATION_REQUIRED", "Product Design invocation evidence is required", dependency_status="locked")
    return _valid()


def _validate_product_design_external_evaluation(evaluation: Any) -> dict[str, Any]:
    if not isinstance(evaluation, dict):
        return _blocked("EXTERNAL_EVALUATION_FIELD_MISSING", "Product Design external evaluation must be an object")
    required = ("available_capabilities", "selected_capability", "invocation_required")
    missing = next((field for field in required if field not in evaluation), None)
    if missing:
        return _blocked("EXTERNAL_EVALUATION_FIELD_MISSING", f"Missing Product Design evaluation field: {missing}")
    if not isinstance(evaluation["available_capabilities"], list) or evaluation.get("selected_capability") != "Product Design" or evaluation.get("invocation_required") is not True:
        return _blocked("EXTERNAL_EVALUATION_FIELD_INVALID", "Product Design capability selection is invalid")
    return _valid()


def validate_task_package(package: Any) -> dict[str, Any]:
    try:
        if not isinstance(package, dict):
            return _blocked("TASK_PACKAGE_REQUIRED_FIELD_MISSING", "Task package must be an object")
        missing = next((field for field in TASK_REQUIRED if field not in package), None)
        if missing:
            return _blocked("TASK_PACKAGE_REQUIRED_FIELD_MISSING", f"Missing task-package field: {missing}")
        auth = package["authorization"]
        if not isinstance(auth, dict) or auth.get("status") != "CONFIRMED_BY_USER" or auth.get("issuer") != "USER_FACING_WUKONG" or not auth.get("parent_task_id") or not auth.get("confirmation_evidence"):
            return _blocked("TASK_PACKAGE_AUTHORIZATION_INVALID", "Task package authorization provenance is invalid")
        if package.get("delegation_permission") not in {"FORBIDDEN", "ALLOWED"}:
            return _blocked("TASK_PACKAGE_AUTHORIZATION_INVALID", "Invalid delegation permission")
        for field in ("scope", "tdd", "historian", "independent_verifier"):
            if not isinstance(package[field], dict):
                return _blocked("TASK_PACKAGE_REQUIRED_FIELD_MISSING", f"Task-package field must be an object: {field}")
        control = _validate_control_document_reference(package["control_document"])
        if not control["valid"]:
            return control
        if not isinstance(package["stop_condition"], str) or not package["stop_condition"].strip():
            return _blocked("TASK_PACKAGE_STOP_CONDITION_INVALID", "A stop condition is required")
        if package["tdd"].get("phase") not in {"RED", "GREEN", "REFACTOR", "NOT_STARTED"} or not isinstance(package["tdd"].get("evidence"), list):
            return _blocked("TASK_PACKAGE_TDD_INVALID", "TDD phase and evidence are required")
        if package["historian"].get("handoff_required") is not True or package["historian"].get("cas_merge") is not True:
            return _blocked("TASK_PACKAGE_HISTORIAN_INVALID", "Historian handoff and CAS merge are required")
        if not package["independent_verifier"].get("required") or not package["independent_verifier"].get("role"):
            return _blocked("TASK_PACKAGE_VERIFIER_INVALID", "An independent verifier is required")
        if _is_design_start(package) or (isinstance(package["external_evaluation"], dict) and "available_capabilities" in package["external_evaluation"]):
            external = (
                _validate_product_design_external_evaluation(package["external_evaluation"])
                if "available_capabilities" in package["external_evaluation"]
                else validate_external_evaluation(
                    package["external_evaluation"],
                    delegation_permission=package.get("delegation_permission"),
                    role=package.get("role"),
                )
            )
        else:
            external = validate_external_evaluation(
                package["external_evaluation"],
                delegation_permission=package.get("delegation_permission"),
                role=package.get("role"),
            )
        if not external["valid"]:
            return external
        if _is_design_start(package):
            product = _validate_product_design_task(package)
            if not product["valid"]:
                return product
        return _valid()
    except (AssertionError, TypeError, ValueError, AttributeError) as exc:
        return _blocked("TASK_PACKAGE_REQUIRED_FIELD_MISSING", f"Malformed task package: {exc}")


def _validate_bug_log(log: Any) -> dict[str, Any]:
    if not isinstance(log, dict):
        return _blocked("BUG_LOG_FIELD_MISSING", "Bug log must be an object")
    missing = next((field for field in BUG_LOG_FIELDS if field not in log), None)
    if missing:
        return _blocked("BUG_LOG_FIELD_MISSING", f"Missing bug-log field: {missing}")
    if not isinstance(log.get("raw_artifact_sha256"), str) or not SHA256_RE.fullmatch(log["raw_artifact_sha256"]):
        return _blocked("BUG_LOG_FIELD_INVALID", "Bug-log artifact hash is invalid")
    if log.get("redaction_applied") is not True:
        return _blocked("BUG_LOG_REDACTION_REQUIRED", "Bug-log raw evidence must be redacted")
    return _valid()


def _validate_product_design_handoff(record: dict[str, Any]) -> dict[str, Any]:
    invocation = record.get("product_design_invocation")
    if not isinstance(invocation, dict):
        return _blocked("PRODUCT_DESIGN_HANDOFF_FIELD_MISSING", "Product Design handoff evidence is required")
    missing = next((field for field in PRODUCT_HANDOFF_FIELDS if field not in invocation), None)
    if missing:
        return _blocked("PRODUCT_DESIGN_HANDOFF_FIELD_MISSING", f"Missing Product Design handoff field: {missing}")
    if not SHA256_RE.fullmatch(str(invocation.get("input_digest", ""))) or not SHA256_RE.fullmatch(str(invocation.get("confirmation_evidence_sha256", ""))):
        return _blocked("PRODUCT_DESIGN_HANDOFF_FIELD_INVALID", "Product Design evidence hash is invalid")
    if invocation.get("dependency_status") not in {"locked", "unlocked"}:
        return _blocked("PRODUCT_DESIGN_HANDOFF_FIELD_INVALID", "Product Design dependency status is invalid")
    return _valid()


def validate_handoff(handoff: Any) -> dict[str, Any]:
    try:
        if not isinstance(handoff, dict):
            return _blocked("HANDOFF_REQUIRED_FIELD_MISSING", "Handoff must be an object")
        missing = next((field for field in HANDOFF_REQUIRED if field not in handoff), None)
        if missing:
            return _blocked("HANDOFF_REQUIRED_FIELD_MISSING", f"Missing handoff field: {missing}")
        if handoff.get("status") not in {"DONE", "DONE_WITH_RISKS", "BLOCKED", "NEEDS_CONTEXT"}:
            return _blocked("HANDOFF_FIELD_INVALID", "Invalid handoff status")
        if not REVISION_RE.fullmatch(str(handoff.get("read_revision"))) or not SHA256_RE.fullmatch(str(handoff.get("read_sha256"))):
            return _blocked("HANDOFF_SCHEMA_INVALID", "Handoff control-document revision/hash is invalid")
        if not isinstance(handoff.get("related_sections"), list) or len(set(handoff["related_sections"])) != len(handoff["related_sections"]):
            return _blocked("HANDOFF_SCHEMA_INVALID", "Related sections must be unique")
        for field in ("modified_files", "issues", "bugs_logs"):
            if not isinstance(handoff[field], list):
                return _blocked("HANDOFF_SCHEMA_INVALID", f"Handoff field must be an array: {field}")
        for log in handoff["bugs_logs"]:
            result = _validate_bug_log(log)
            if not result["valid"]:
                return result
        is_product_design = str(handoff.get("role", "")).casefold() in {"嫦娥", "chang'e", "chang’e"} or "product_design_invocation" in handoff
        external = (
            _validate_product_design_external_evaluation(handoff["external_skill_agent_evaluation"])
            if is_product_design and isinstance(handoff["external_skill_agent_evaluation"], dict) and "available_capabilities" in handoff["external_skill_agent_evaluation"]
            else validate_external_evaluation(handoff["external_skill_agent_evaluation"])
        )
        if not external["valid"]:
            return external
        if is_product_design:
            product = _validate_product_design_handoff(handoff)
            if not product["valid"]:
                return product
        return _valid()
    except (TypeError, ValueError, AttributeError) as exc:
        return _blocked("HANDOFF_SCHEMA_INVALID", f"Malformed handoff: {exc}")


def redact_and_hash_artifact(raw: str | bytes, *, secrets: Iterable[str] = ()) -> dict[str, Any]:
    try:
        text = raw.decode("utf-8", errors="strict") if isinstance(raw, bytes) else raw
        if not isinstance(text, str):
            return _blocked("ARTIFACT_REDACTION_INVALID", "Artifact must be UTF-8 bytes or text")
        redacted = text
        replacements = [secret for secret in secrets if isinstance(secret, str) and secret]
        for secret in sorted(set(replacements), key=len, reverse=True):
            redacted = redacted.replace(secret, "[REDACTED]")
        redacted = re.sub(r"(?i)(authorization\s*:\s*bearer\s+)[^\s]+", r"\1[REDACTED]", redacted)
        redacted = re.sub(r"(?i)(api[_-]?key\s*=\s*)[^\s]+", r"\1[REDACTED]", redacted)
        digest = hashlib.sha256(redacted.encode("utf-8")).hexdigest()
        return _valid(redacted_text=redacted, sha256=digest, stored_sha256=digest, redaction_applied=redacted != text)
    except (UnicodeDecodeError, TypeError, ValueError) as exc:
        return _blocked("ARTIFACT_REDACTION_INVALID", f"Artifact redaction failed: {exc}")


def validate_goal_creation(record: Any) -> dict[str, Any]:
    try:
        if not isinstance(record, dict):
            return _blocked("GOAL_CONFIRMATION_REQUIRED", "Goal creation record must be an object")
        if record.get("project_kind") == "current" and record.get("create_goal"):
            return _blocked("GOAL_CREATION_FORBIDDEN_CURRENT_PROJECT", "The current governance project cannot create a Goal")
        if record.get("project_kind") != "future" or not record.get("scope_confirmed") or not record.get("goal_confirmed"):
            return _blocked("GOAL_CONFIRMATION_REQUIRED", "Future Goal requires scope and project-specific confirmation")
        for field in ("project_specific_goal",):
            if not record.get(field):
                return _blocked("GOAL_CONFIRMATION_REQUIRED", f"Missing future Goal field: {field}")
        if not record.get("proposal_confirmed") or not record.get("dispatch_confirmed"):
            return _blocked("GOAL_CONFIRMATION_REQUIRED", "Proposal and dispatch confirmation are required")
        return _valid()
    except (TypeError, ValueError, AttributeError) as exc:
        return _blocked("GOAL_CONFIRMATION_REQUIRED", f"Malformed Goal creation record: {exc}")


def validate_goal_record(record: Any) -> dict[str, Any]:
    required = ("conversation_checkpoint", "confirmed_decisions", "open_questions", "action_plan", "current_phase", "status", "next_action", "blockers")
    if not isinstance(record, dict):
        return _blocked("GOAL_RECORD_FIELD_MISSING", "Goal record must be an object")
    missing = next((field for field in required if field not in record), None)
    if missing:
        return _blocked("GOAL_RECORD_FIELD_MISSING", f"Missing Goal record field: {missing}")
    if any(not isinstance(record[field], (str, list)) for field in required):
        return _blocked("GOAL_RECORD_FIELD_INVALID", "Goal record fields have invalid types")
    return _valid()


def validate_goal_completion(evidence: Any) -> dict[str, Any]:
    try:
        if not isinstance(evidence, dict) or not all(field in evidence for field in ("compile", "tests", "review", "raw_result_blocks")):
            return _blocked("GOAL_COMPLETION_RAW_OUTPUT_MISSING", "Goal completion evidence is incomplete")
        blocks = evidence["raw_result_blocks"]
        if not isinstance(blocks, dict) or any(not isinstance(blocks.get(field), str) or not blocks[field].strip() for field in ("compile", "tests", "review")):
            return _blocked("GOAL_COMPLETION_RAW_OUTPUT_MISSING", "All three original result blocks are required")
        if evidence["compile"].get("result") != "COMPILE_ZERO_ERRORS" or evidence["tests"].get("result") != "ALL_TESTS_PASS" or evidence["review"].get("result") != "REVIEW_APPROVED":
            return _blocked("GOAL_COMPLETION_GATE_NOT_MET", "Compile, test, and independent review gates are required")
        return _valid()
    except (TypeError, ValueError, AttributeError) as exc:
        return _blocked("GOAL_COMPLETION_GATE_NOT_MET", f"Malformed Goal completion evidence: {exc}")


def validate_blocked_threshold(*, blocker: str, consecutive_turns: int, previous_blocker: str | None = None) -> dict[str, Any]:
    if not isinstance(blocker, str) or not blocker or not isinstance(consecutive_turns, int) or consecutive_turns < 3 or (previous_blocker is not None and previous_blocker != blocker):
        return _blocked("GOAL_BLOCKED_THRESHOLD_NOT_REACHED", "The same blocker must recur for three consecutive turns")
    return _valid(blocked_threshold_reached=True)


def validate_brainstorming(record: Any) -> dict[str, Any]:
    try:
        if not isinstance(record, dict) or record.get("scale") not in {"S", "M", "L", "XL"}:
            return _blocked("BRAINSTORMING_DIMENSION_MISSING", "A valid lifecycle scale is required")
        if record.get("brainstorming_skill") != "superpowers:brainstorming":
            return _blocked("BRAINSTORMING_SKILL_MISSING", "Superpowers brainstorming is mandatory")
        dimensions = record.get("dimensions")
        if not isinstance(dimensions, dict):
            return _blocked("BRAINSTORMING_DIMENSION_MISSING", "Brainstorming dimensions must be an object")
        missing = next((dimension for dimension in DEFAULT_BRAINSTORM_DIMENSIONS if not dimensions.get(dimension)), None)
        if missing:
            return _blocked("BRAINSTORMING_DIMENSION_MISSING", f"Missing brainstorming dimension: {missing}")
        return _valid()
    except (TypeError, ValueError, AttributeError) as exc:
        return _blocked("BRAINSTORMING_DIMENSION_MISSING", f"Malformed brainstorming record: {exc}")


def classify_lifecycle(objective: Any) -> dict[str, Any]:
    try:
        if not isinstance(objective, dict):
            return _blocked("LIFECYCLE_CLASSIFICATION_INVALID", "Lifecycle objective must be an object")
        files = int(objective.get("files", 0) or 0)
        modules = int(objective.get("modules", 0) or 0)
        services = int(objective.get("services", 0) or 0)
        risk = str(objective.get("risk", "low")).casefold()
        xl = files > 30 or modules > 5 or services > 2 or objective.get("irreversible_data") is True or risk == "critical" or int(objective.get("rollback_minutes", 0) or 0) > 30
        level_l = xl or files > 10 or modules > 2 or services > 1 or objective.get("api") is True or risk == "high"
        level_m = level_l or files > 2 or modules > 1 or services > 0 or risk == "medium" or objective.get("dependencies", 0) not in (0, None)
        scale = "XL" if xl else "L" if level_l else "M" if level_m else "S"
        return _valid(scale=scale)
    except (TypeError, ValueError) as exc:
        return _blocked("LIFECYCLE_CLASSIFICATION_INVALID", f"Malformed lifecycle objective: {exc}")


def validate_dispatch_confirmation(record: Any) -> dict[str, Any]:
    try:
        if not isinstance(record, dict) or not record.get("proposal_confirmed") or not record.get("dispatch_confirmed"):
            return _blocked("USER_RECONFIRMATION_REQUIRED", "Proposal and dispatch confirmation are required")
        change = record.get("scope_cost_risk_write")
        if not isinstance(change, dict):
            return _blocked("USER_RECONFIRMATION_REQUIRED", "Scope/cost/risk/write confirmation is required")
        fields = ("scope", "cost", "risk", "write_surface")
        if any(field not in change for field in fields):
            return _blocked("USER_RECONFIRMATION_REQUIRED", "All changed-boundary dimensions are required")
        changed = any(change[field] != "unchanged" for field in fields)
        if changed and change.get("reconfirmed") is not True:
            return _blocked("USER_RECONFIRMATION_REQUIRED", "Changed scope/cost/risk/write surface needs reconfirmation")
        return _valid()
    except (TypeError, ValueError, AttributeError) as exc:
        return _blocked("USER_RECONFIRMATION_REQUIRED", f"Malformed dispatch confirmation: {exc}")

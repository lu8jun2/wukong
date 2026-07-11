from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "skills" / "multi-agent-wukong"
GATE_MODULE = SKILL_ROOT / "scripts" / "project_control_gate.py"
HISTORIAN_MODULE = SKILL_ROOT / "scripts" / "project_control_historian.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"missing import spec for {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def synthetic_control_doc(path: Path, revision: str = "r3") -> str:
    sections = (
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
    lines = ["# Synthetic Project Control", ""]
    for index, section in enumerate(sections, start=1):
        lines.append(f"## {index}. {section}")
        if section == "Document Metadata":
            lines.extend(
                (
                    "| Field | Value |",
                    "|---|---|",
                    "| schema version | `project-control/v1` |",
                    f"| document absolute path | `{path}` |",
                    f"| current revision | `{revision}` |",
                    "| Goal status | `NOT_CREATED_BY_USER_DIRECTION` |",
                )
            )
        else:
            lines.append(f"Synthetic {section}.")
        lines.append("")
    text = "\n".join(lines)
    path.write_text(text, encoding="utf-8", newline="\n")
    return text


class ProjectControlContractTests(unittest.TestCase):
    def test_gate_validates_synthetic_control_doc_and_contracts(self) -> None:
        gate = load_module(GATE_MODULE, "public_gate")
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            control_doc = project_root / "docs" / "wukong" / "PROJECT-CONTROL.md"
            control_doc.parent.mkdir(parents=True, exist_ok=True)
            synthetic_control_doc(control_doc)
            snapshot = gate.read_snapshot(str(control_doc))
            self.assertTrue(snapshot.get("path", "").endswith("PROJECT-CONTROL.md"))
            validated = gate.validate_snapshot(
                snapshot,
                canonical_path=str(control_doc),
                canonical_root=str(project_root),
                expected_revision="r3",
                expected_sha256=hashlib.sha256(control_doc.read_bytes()).hexdigest(),
                required_sections=(
                    "Project Goal",
                    "Hard Constraints",
                    "Subagent Handoff Contract",
                ),
            )
            self.assertTrue(validated["valid"], validated)

            package = {
                "task_id": "PUBLIC-WUKONG / CHILD",
                "role": "Implementation Worker",
                "authorization": {
                    "status": "CONFIRMED_BY_USER",
                    "issuer": "USER_FACING_WUKONG",
                    "parent_task_id": "PUBLIC-WUKONG",
                    "confirmation_evidence": "User approved the public staging build.",
                },
                "control_document": {
                    "path": str(control_doc),
                    "schema": "project-control/v1",
                    "revision": "r3",
                    "sha256": hashlib.sha256(control_doc.read_bytes()).hexdigest(),
                    "required_sections": ["Project Goal", "Hard Constraints", "Subagent Handoff Contract"],
                },
                "delegation_permission": "FORBIDDEN",
                "scope": {"allowed": ["staging only"], "forbidden": ["recursive dispatch"]},
                "tdd": {"phase": "RED", "evidence": ["initial red run"]},
                "historian": {"handoff_required": True, "cas_merge": True},
                "independent_verifier": {"role": "Verifier", "required": True},
                "stop_condition": "Block on contract mismatch.",
                "external_evaluation": {
                    "available_skills": ["plugin-creator", "verification-before-completion"],
                    "selected_skills": ["plugin-creator"],
                    "skipped_skills": [{"name": "product-design", "reason": "No design artifact"}],
                    "installed_specialist_roles": ["Implementation Worker"],
                    "agency_map": {"status": "not_used"},
                    "deerflow": {"status": "not_used", "child_call": False},
                    "professional_review": {"needed": True, "reason": "Independent security review later"},
                    "network_use": {"used": False, "systems": []},
                    "authorization_boundary": {
                        "issuer": "USER_FACING_WUKONG",
                        "delegation_permission": "FORBIDDEN",
                        "role": "Implementation Worker",
                    },
                },
            }
            self.assertTrue(gate.validate_task_package(package)["valid"])
            self.assertTrue(
                gate.validate_brainstorming(
                    {
                        "scale": "L",
                        "brainstorming_skill": "superpowers:brainstorming",
                        "dimensions": {key: "confirmed" for key in gate.DEFAULT_BRAINSTORM_DIMENSIONS},
                    }
                )["valid"]
            )
            self.assertTrue(
                gate.validate_goal_completion(
                    {
                        "compile": {"result": "COMPILE_ZERO_ERRORS"},
                        "tests": {"result": "ALL_TESTS_PASS"},
                        "review": {"result": "REVIEW_APPROVED"},
                        "raw_result_blocks": {
                            "compile": "compile ok",
                            "tests": "tests ok",
                            "review": "review ok",
                        },
                    }
                )["valid"]
            )

    def test_historian_merges_append_only_on_synthetic_doc(self) -> None:
        historian = load_module(HISTORIAN_MODULE, "public_historian")
        with tempfile.TemporaryDirectory() as temp_dir:
            control_doc = Path(temp_dir) / "docs" / "wukong" / "PROJECT-CONTROL.md"
            control_doc.parent.mkdir(parents=True, exist_ok=True)
            synthetic_control_doc(control_doc)
            base_hash = hashlib.sha256(control_doc.read_bytes()).hexdigest()
            handoff = {
                "status": "DONE",
                "task_id": "PUBLIC-WUKONG / PACKAGE",
                "role": "Implementation Worker",
                "control_document_path": str(control_doc),
                "read_revision": "r3",
                "read_sha256": base_hash,
                "related_sections": [
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
                ],
                "modified_files": ["README.md"],
                "tdd_status": "GREEN",
                "tdd_evidence": {"phase": "GREEN"},
                "test_command": "python -m unittest discover -s tests",
                "test_result": {"exit_code": 0},
                "issues": [],
                "bugs_logs": [],
                "hard_constraints_compliance": "PASS",
                "conclusion": "Staging package created.",
                "next_step": "SECURITY_REVIEW",
                "historian_proposal": "Append public release staging result.",
                "external_skill_agent_evaluation": {
                    "available_skills": ["plugin-creator"],
                    "selected_skills": ["plugin-creator"],
                    "skipped_skills": [],
                    "installed_specialist_roles": ["Implementation Worker"],
                    "agency_map": {"status": "not_used"},
                    "deerflow": {"status": "not_used", "child_call": False},
                    "professional_review": {"needed": True, "reason": "security review next"},
                    "network_use": {"used": False, "systems": []},
                    "authorization_boundary": {
                        "issuer": "USER_FACING_WUKONG",
                        "delegation_permission": "FORBIDDEN",
                        "role": "Implementation Worker",
                    },
                },
            }
            merged = historian.merge_handoff(
                str(control_doc),
                handoff,
                base_revision="r3",
                base_sha256=base_hash,
                dependency={"task_id": "FOLLOWUP", "status": "locked"},
            )
            self.assertTrue(merged["valid"], merged)
            self.assertEqual("r4", merged["revision"])

    def test_schemas_are_json_objects(self) -> None:
        schema_names = (
            "project-control.schema.json",
            "task-package.schema.json",
            "handoff.schema.json",
            "product-design-invocation.schema.json",
            "product-design-evidence.schema.json",
        )
        for name in schema_names:
            with self.subTest(name=name):
                path = SKILL_ROOT / "schemas" / name
                data = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual("object", data["type"])
                self.assertIs(data["additionalProperties"], False)


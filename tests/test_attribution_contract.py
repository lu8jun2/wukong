from __future__ import annotations

import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, ValidationError


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_ROOT = ROOT / "skills" / "multi-agent-wukong" / "schemas"
DISPATCH_USAGE = ROOT / "skills" / "multi-agent-wukong" / "references" / "wukong-dispatch-usage.md"
DELEGATION_TEMPLATES = ROOT / "skills" / "multi-agent-wukong" / "references" / "delegation-templates.md"


CONTROL_SHA256 = "a" * 64


def load_schema(name: str) -> dict:
    return json.loads((SCHEMA_ROOT / name).read_text(encoding="utf-8"))


def control_context() -> dict:
    return {
        "path": "docs/wukong/PROJECT-CONTROL.md",
        "schema": "project-control/v1",
        "revision": "r1",
        "sha256": CONTROL_SHA256,
        "status": "VALID",
    }


def protocol_context() -> dict:
    return {
        "actor": "Wukong",
        "role_display": "Role=Wukong/悟空",
        "project_control": control_context(),
    }


def external_evaluation() -> dict:
    return {
        "available_skills": ["superpowers:test-driven-development"],
        "selected_skills": ["superpowers:test-driven-development"],
        "skipped_skills": [],
        "installed_specialist_roles": [],
        "agency_map": {"status": "not_used"},
        "deerflow": {"status": "not_used", "child_call": False},
        "professional_review": {"needed": False},
        "network_use": {"used": False},
        "authorization_boundary": {
            "issuer": "USER_FACING_WUKONG",
            "delegation_permission": "FORBIDDEN",
        },
    }


def secondary_historian_identity() -> dict:
    return {
        "role": "public-historian",
        "role_class": "secondary-only",
        "primary_role": "guanyin",
        "secondary_roles": ["public-historian"],
        "role_display": "Role=Public Historian/公共史官",
    }


def task_package() -> dict:
    return {
        "task_id": "PUBLIC-WUKONG / HISTORIAN",
        **secondary_historian_identity(),
        "authorization": {
            "status": "CONFIRMED_BY_USER",
            "issuer": "USER_FACING_WUKONG",
            "parent_task_id": "PUBLIC-WUKONG",
            "confirmation_evidence": "User confirmed public historian dispatch.",
        },
        "control_document": {
            "path": "docs/wukong/PROJECT-CONTROL.md",
            "schema": "project-control/v1",
            "revision": "r1",
            "sha256": CONTROL_SHA256,
            "required_sections": ["Project Structure", "Subagent Handoff Contract"],
        },
        "protocol_context": protocol_context(),
        "delegation_permission": "FORBIDDEN",
        "scope": {"allowed": ["public history"], "forbidden": ["recursive dispatch"]},
        "tdd": {"phase": "RED", "evidence": ["focused red test"]},
        "historian": {"handoff_required": True, "cas_merge": True},
        "independent_verifier": {"role": "Independent Verifier", "required": True},
        "stop_condition": "Block on missing or mismatched paragraph attribution.",
        "external_evaluation": external_evaluation(),
    }


def attribution_record() -> dict:
    return {
        "paragraph_id": "p-001",
        "role_id": "public-historian",
        "role_display": "Role=Public Historian/公共史官",
        "primary_role": "guanyin",
        "secondary_roles": ["public-historian"],
        "contribution": "Recorded the sanitized release-history paragraph.",
        "evidence_refs": ["test:evidence:001"],
        "text_sha256": "b" * 64,
    }


def handoff() -> dict:
    return {
        "status": "DONE",
        "task_id": "PUBLIC-WUKONG / HISTORIAN",
        **secondary_historian_identity(),
        "protocol_context": protocol_context(),
        "control_document_path": "docs/wukong/PROJECT-CONTROL.md",
        "read_revision": "r1",
        "read_sha256": CONTROL_SHA256,
        "related_sections": ["Subagent Handoff Contract", "Verification Evidence"],
        "modified_files": ["skills/multi-agent-wukong/schemas/handoff.schema.json"],
        "tdd_status": "GREEN",
        "tdd_evidence": {"phase": "GREEN"},
        "test_command": "python -m unittest tests/test_attribution_contract.py",
        "test_result": {"exit_code": 0},
        "visible_paragraph_count": 1,
        "visible_paragraph_ids": ["p-001"],
        "attribution": [attribution_record()],
        "issues": [],
        "bugs_logs": [],
        "hard_constraints_compliance": "PASS; no recursion; control document was read-only.",
        "conclusion": "Attribution contract implemented.",
        "next_step": "Independent verification.",
        "historian_proposal": "Append the sanitized handoff with paragraph attribution.",
        "external_skill_agent_evaluation": external_evaluation(),
    }


class AttributionContractTests(unittest.TestCase):
    def assert_valid(self, schema_name: str, instance: dict) -> None:
        schema = load_schema(schema_name)
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(instance)

    def assert_invalid(self, schema_name: str, instance: dict) -> None:
        schema = load_schema(schema_name)
        Draft202012Validator.check_schema(schema)
        with self.assertRaises(ValidationError):
            Draft202012Validator(schema).validate(instance)

    def test_secondary_only_public_historian_task_package_is_valid(self) -> None:
        self.assert_valid("task-package.schema.json", task_package())

    def test_public_historian_role_display_cannot_be_fabricated(self) -> None:
        package = task_package()
        package["role_display"] = "Role=Historian/Not the public historian"
        self.assert_invalid("task-package.schema.json", package)

    def test_handoff_requires_wukong_protocol_context_and_per_paragraph_attribution(self) -> None:
        self.assert_valid("handoff.schema.json", handoff())

        missing_attribution = handoff()
        del missing_attribution["attribution"]
        self.assert_invalid("handoff.schema.json", missing_attribution)

    def test_handoff_attribution_record_requires_binding_fields(self) -> None:
        record = attribution_record()
        del record["text_sha256"]
        broken = handoff()
        broken["attribution"] = [record]
        self.assert_invalid("handoff.schema.json", broken)

    def test_protocol_documents_fail_closed_contract_is_published(self) -> None:
        dispatch = DISPATCH_USAGE.read_text(encoding="utf-8")
        templates = DELEGATION_TEMPLATES.read_text(encoding="utf-8")
        required_tokens = (
            "Role=Wukong/悟空",
            "PROJECT-CONTROL.md",
            "project-control/v1",
            "sha256",
            "BLOCKED_CONTROL_DOC_MISSING",
            "secondary-only",
            "public-historian",
            "paragraph_id",
            "text_sha256",
            "count mismatch",
            "paragraph mismatch",
            "fabricated role display",
            "zero writes",
        )
        for token in required_tokens:
            with self.subTest(token=token):
                self.assertIn(token, dispatch)
                self.assertIn(token, templates)


if __name__ == "__main__":
    unittest.main()

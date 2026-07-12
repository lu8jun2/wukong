from __future__ import annotations

import importlib.util
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "skills" / "codex-history" / "scripts" / "collect_project_history.py"


def load_module(path: Path = MODULE_PATH, name: str = "public_history_collector"):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"missing import spec for {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def public_handoff() -> dict:
    return {
        "status": "DONE_WITH_RISKS",
        "task_id": "public-history-task-001",
        "role": "public-historian",
        "role_class": "secondary-only",
        "primary_role": "guanyin",
        "secondary_roles": ["public-historian"],
        "role_display": "Role=Public Historian/公共史官",
        "protocol_context": {
            "actor": "Wukong",
            "role_display": "Role=Wukong/悟空",
            "project_control": {
                "path": "docs/wukong/PROJECT-CONTROL.md",
                "schema": "project-control/v1",
                "revision": "r1",
                "sha256": "a" * 64,
                "status": "VALID",
            },
        },
        "control_document_path": "docs/wukong/PROJECT-CONTROL.md",
        "read_revision": "r1",
        "read_sha256": "a" * 64,
        "related_sections": ["Subagent Handoff Contract", "Verification Evidence"],
        "modified_files": ["skills/codex-history/SKILL.md"],
        "tdd_status": "GREEN",
        "tdd_evidence": {"phase": "GREEN", "note": "focused test"},
        "test_command": "python -m unittest tests/test_public_historian.py",
        "test_result": {"exit_code": 0},
        "visible_paragraph_count": 1,
        "visible_paragraph_ids": ["p-001"],
        "attribution": [
            {
                "paragraph_id": "p-001",
                "role_id": "public-historian",
                "role_display": "Role=Public Historian/公共史官",
                "primary_role": "guanyin",
                "secondary_roles": ["public-historian"],
                "contribution": "Recorded a public-safe handoff.",
                "evidence_refs": ["test:evidence:001", "C:\\Users\\private\\secret.log"],
                "text_sha256": "b" * 64,
            }
        ],
        "issues": [{"message": "hostname=DESKTOP-PRIVATE"}],
        "bugs_logs": [],
        "hard_constraints_compliance": "No recursion; record-only historian.",
        "conclusion": "History was recorded for independent review.",
        "next_step": "Independent verification remains required.",
        "historian_proposal": "Append the sanitized handoff.",
        "external_skill_agent_evaluation": {
            "available_skills": ["superpowers:test-driven-development"],
            "selected_skills": ["superpowers:test-driven-development"],
            "skipped_skills": [],
            "installed_specialist_roles": [],
            "agency_map": {"status": "not_used"},
            "deerflow": {"status": "not_used", "child_call": False},
            "professional_review": {"needed": False},
            "network_use": {"used": False},
            "authorization_boundary": {"delegation_permission": "FORBIDDEN"},
        },
    }


class PublicHistorianTests(unittest.TestCase):
    def test_public_serializer_keeps_protocol_attribution_and_secondary_boundary(self) -> None:
        module = load_module()

        record = module.serialize_public_handoff(public_handoff())

        self.assertEqual("public-historian", record["role"])
        self.assertEqual("secondary-only", record["role_class"])
        self.assertEqual("Role=Public Historian/公共史官", record["role_display"])
        self.assertEqual("public-historian", record["secondary_roles"][0])
        self.assertEqual("Wukong", record["protocol_context"]["actor"])
        self.assertEqual(
            "docs/wukong/PROJECT-CONTROL.md",
            record["protocol_context"]["project_control"]["path"],
        )
        self.assertEqual(["test:evidence:001"], record["attribution"][0]["evidence_refs"][:1])
        self.assertIn("secondary-only", record["hard_constraints_compliance"])
        self.assertIn("does not coordinate", record["hard_constraints_compliance"])
        self.assertIn("does not approve", record["hard_constraints_compliance"])

    def test_public_history_redacts_paths_secrets_machine_names_timestamps_and_private_logs(self) -> None:
        module = load_module()
        secret_label = "-".join(("api", "key"))
        secret_value = "not-public-" + "secret"
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "README.md").write_text(
                "Public note.\n"
                "path=C:\\Users\\win11\\private\\artifact.txt\n"
                "hostname=DESKTOP-PRIVATE\n"
                f"{secret_label}={secret_value}\n"
                "recorded=2026-07-12T10:20:30Z\n",
                encoding="utf-8",
            )
            (root / "docs").mkdir()
            (root / "docs" / "public-summary.md").write_text(
                "A public summary with evidence.\n",
                encoding="utf-8",
            )
            (root / "private").mkdir()
            (root / "private" / "session.log").write_text(
                "PRIVATE LOG MUST NOT APPEAR\n",
                encoding="utf-8",
            )
            output = module.render_public_history(root, handoff=public_handoff())

        self.assertIn("Role=Public Historian/公共史官", output)
        self.assertIn("test:evidence:001", output)
        self.assertNotIn("C:\\Users\\win11", output)
        self.assertNotIn("DESKTOP-PRIVATE", output)
        self.assertNotIn(secret_value, output)
        self.assertNotIn("2026-07-12T10:20:30Z", output)
        self.assertNotIn("PRIVATE LOG MUST NOT APPEAR", output)
        self.assertNotRegex(output, re.compile(r"(?i)project:\s*[`']?[A-Za-z]:[\\/]"))

    def test_public_historian_fixture_source_has_no_secret_pattern_findings(self) -> None:
        scanner = load_module(ROOT / "scripts" / "redaction_scan.py")
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_root = Path(temp_dir)
            fixture = fixture_root / "test_public_historian.py"
            fixture.write_text(
                (ROOT / "tests" / "test_public_historian.py").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            result = scanner.scan(fixture_root)

        self.assertEqual([], result["findings"])

    def test_public_cli_mode_does_not_change_private_default_collection(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "README.md").write_text("Public note.\n", encoding="utf-8")
            public_out = root / "public-history.md"
            private_out = root / "private-history.md"

            self.assertEqual(
                0,
                module.main([str(root), "--public", "--out", str(public_out)]),
            )
            self.assertEqual(
                0,
                module.main([str(root), "--out", str(private_out)]),
            )

            public_text = public_out.read_text(encoding="utf-8")
            private_text = private_out.read_text(encoding="utf-8")

        self.assertIn("secondary-only", public_text)
        self.assertIn(f"Project: `{root}`", private_text)
        self.assertIn("Generated:", private_text)
        self.assertNotIn(f"Project: `{root}`", public_text)

    def test_public_skill_declares_dispatch_and_lifecycle_boundaries(self) -> None:
        text = (ROOT / "skills" / "codex-history" / "SKILL.md").read_text(encoding="utf-8")

        for token in (
            "Role=Public Historian/公共史官",
            "secondary-only",
            "Delegation permission: FORBIDDEN",
            "no recursion",
            "does not coordinate",
            "does not approve",
            "evidence_refs",
            "--public",
            "installer",
        ):
            with self.subTest(token=token):
                self.assertIn(token, text)


if __name__ == "__main__":
    unittest.main()

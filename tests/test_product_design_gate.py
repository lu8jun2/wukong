from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "skills" / "multi-agent-wukong"
PRODUCT_GATE = SKILL_ROOT / "scripts" / "product_design_gate.py"
DISPATCH_GATE = SKILL_ROOT / "scripts" / "chang_e_dispatch_gate.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"missing import spec for {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def make_fake_plugin(codex_home: Path) -> None:
    plugin_root = codex_home / "plugins" / "cache" / "openai-curated-remote" / "product-design" / "0.1.50"
    manifest_path = plugin_root / ".codex-plugin" / "plugin.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest = {
        "name": "product-design",
        "version": "0.1.50",
        "interface": {
            "displayName": "Product Design",
            "capabilities": ["Interactive", "Write"],
        },
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def synthetic_control_doc(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "# Synthetic Project Control",
                "",
                "## 1. Document Metadata",
                "| Field | Value |",
                "|---|---|",
                "| schema version | `project-control/v1` |",
                f"| document absolute path | `{path}` |",
                "| current revision | `r2` |",
                "| Goal status | `NOT_CREATED_BY_USER_DIRECTION` |",
                "",
                "## 2. Project Goal",
                "Goal.",
                "",
                "## 3. Goal Policy Clarification",
                "Policy.",
                "",
                "## 4. Scope / Non-goals",
                "Scope.",
                "",
                "## 5. Project Structure",
                "Structure.",
                "",
                "## 6. Hard Constraints",
                "Constraints.",
                "",
                "## 7. Lifecycle Assessment",
                "Lifecycle.",
                "",
                "## 8. Design / Architecture",
                "Architecture.",
                "",
                "## 9. TDD Plan",
                "TDD.",
                "",
                "## 10. Task Ledger",
                "Ledger.",
                "",
                "## 11. Progress / Current Status",
                "Status.",
                "",
                "## 12. Issues / Bugs / Logs",
                "Issues.",
                "",
                "## 13. Decisions / Risks / Blockers",
                "Decisions.",
                "",
                "## 14. Subagent Handoff Contract",
                "Handoff.",
                "",
                "## 15. Verification Evidence",
                "Verification.",
                "",
                "## 16. Change Log",
                "History.",
                "",
            ]
        ),
        encoding="utf-8",
        newline="\n",
    )


class ProductDesignGateTests(unittest.TestCase):
    def test_unavailable_runtime_fail_closes(self) -> None:
        gate = load_module(PRODUCT_GATE, "public_product_design_gate")
        result = gate.build_unavailable_result(
            input_brief="Create a design proposal.",
            expected_outputs=["design_proposal"],
            runtime_tool_exposed=False,
            codex_home=str(Path(tempfile.gettempdir()) / "missing-codex-home"),
        )
        self.assertFalse(result["valid"])
        self.assertEqual("BLOCKED_PRODUCT_DESIGN_PLUGIN_UNAVAILABLE", result["code"])

    def test_positive_invocation_path_requires_confirmation_and_builds_dispatch_package(self) -> None:
        gate = load_module(PRODUCT_GATE, "public_product_design_gate_positive")
        dispatch = load_module(DISPATCH_GATE, "public_dispatch_gate")
        with tempfile.TemporaryDirectory() as temp_dir:
            codex_home = Path(temp_dir) / ".codex"
            make_fake_plugin(codex_home)
            control_doc = Path(temp_dir) / "project" / "docs" / "wukong" / "PROJECT-CONTROL.md"
            synthetic_control_doc(control_doc)
            test_timestamp = datetime.now(timezone.utc).isoformat()
            confirmation_payload = "USER_FACING_WUKONG|" + test_timestamp + "|synthetic-confirmation"
            confirmation_hash = hashlib.sha256(confirmation_payload.encode("utf-8")).hexdigest()
            built = gate.build_product_design_invocation(
                input_brief="Create the design proposal.",
                expected_outputs=["design_proposal", "artifact_manifest"],
                runtime_tool_exposed=True,
                actual_plugin_invocation=True,
                tool_call_id="pd-tool-001",
                invocation_timestamp=test_timestamp,
                artifact_paths=["outputs/product-design/design-proposal.json"],
                confirmation_issuer="USER_FACING_WUKONG",
                confirmation_timestamp=test_timestamp,
                confirmation_evidence_path="outputs/product-design/synthetic-confirmation.json",
                confirmation_evidence_sha256=confirmation_hash,
                codex_home=str(codex_home),
            )
            self.assertTrue(built["valid"], built)
            package = dispatch.evaluate_chang_e_design_start(
                input_brief="Create the design proposal.",
                expected_outputs=["design_proposal", "artifact_manifest"],
                control_document_path=str(control_doc),
                runtime_tool_exposed=True,
                actual_plugin_invocation=True,
                tool_call_id="pd-tool-001",
                invocation_timestamp=test_timestamp,
                artifact_paths=["outputs/product-design/design-proposal.json"],
                confirmation_issuer="USER_FACING_WUKONG",
                confirmation_timestamp=test_timestamp,
                confirmation_evidence_path="outputs/product-design/synthetic-confirmation.json",
                confirmation_evidence_sha256=confirmation_hash,
                codex_home=str(codex_home),
            )
            self.assertTrue(package["valid"], package)
            self.assertEqual("unlocked", package["dependency_status"])

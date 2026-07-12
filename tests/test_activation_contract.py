from __future__ import annotations

import importlib.util
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ACTIVATION_MODULE = ROOT / "scripts" / "activate_wukong.py"
PUBLIC_AGENTS = ROOT / "AGENTS.md"
README = ROOT / "README.md"
DOCS = (
    ROOT / "docs" / "macOS-install.md",
    ROOT / "docs" / "plugin-install.md",
    ROOT / "docs" / "cross-platform.md",
)
WUKONG_ALWAYS = ROOT / "skills" / "wukong-always" / "SKILL.md"
MULTI_AGENT = ROOT / "skills" / "multi-agent-wukong" / "SKILL.md"
ROLE_MAP = ROOT / "skills" / "multi-agent-wukong" / "references" / "agency-agent-role-map.json"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"missing import spec for {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def make_live_project(project_root: Path) -> Path:
    control_doc = project_root / "docs" / "wukong" / "PROJECT-CONTROL.md"
    control_doc.parent.mkdir(parents=True, exist_ok=True)
    control_doc.write_text(
        "\n".join(
            (
                "# Synthetic Project Control",
                "",
                "## 1. Document Metadata",
                "| Field | Value |",
                "|---|---|",
                "| schema version | `project-control/v1` |",
                f"| project root | `{project_root}` |",
                f"| document absolute path | `{control_doc}` |",
                "| current revision | `r1` |",
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
            )
        ),
        encoding="utf-8",
        newline="\n",
    )
    (project_root / "AGENTS.md").write_text(
        "\n".join(
            (
                "# Project AGENTS",
                "",
                "- Wukong is the visible coordinator.",
                "- Project work starts only after `<project-root>/docs/wukong/PROJECT-CONTROL.md` exists.",
            )
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return control_doc


class ActivationContractTests(unittest.TestCase):
    def test_wukong_always_skill_exists_and_sets_entry_contract(self) -> None:
        self.assertTrue(WUKONG_ALWAYS.exists(), "skills/wukong-always/SKILL.md must exist")
        text = WUKONG_ALWAYS.read_text(encoding="utf-8")
        for token in (
            "Every task starts with Wukong dialogue",
            "Wukong never performs substantive work",
            "Subagents",
            "user confirmation before dispatch",
            "superpowers:brainstorming",
            "external capability evaluation",
            "historian",
            "independent verification",
            "fail closed",
            "CHANG_E_PRODUCT_DESIGN_PLUGIN_GATE",
        ):
            with self.subTest(token=token):
                self.assertIn(token, text)

    def test_activation_module_bootstrap_and_verify_contract(self) -> None:
        self.assertTrue(ACTIVATION_MODULE.exists(), "scripts/activate_wukong.py must exist")
        module = load_module(ACTIVATION_MODULE, "public_activate_wukong")
        with tempfile.TemporaryDirectory() as temp_dir:
            sandbox = Path(temp_dir)
            codex_home = sandbox / ".codex"
            project_root = sandbox / "project"
            blocked = module.run_activation(
                bundle_root=ROOT,
                codex_home=codex_home,
                project_root=project_root,
            )
            self.assertEqual("BLOCKED", blocked["status"])
            self.assertIn("project_agents", blocked["missing"])
            self.assertIn("project_control", blocked["missing"])
            self.assertFalse((project_root / "AGENTS.md").exists())
            self.assertFalse((project_root / "docs" / "wukong" / "PROJECT-CONTROL.md").exists())

            activated = module.run_activation(
                bundle_root=ROOT,
                codex_home=codex_home,
                project_root=project_root,
                bootstrap_doc=True,
            )
            self.assertEqual("ACTIVATED", activated["status"])
            self.assertTrue((project_root / "AGENTS.md").exists())
            self.assertTrue((project_root / "docs" / "wukong" / "PROJECT-CONTROL.md").exists())

            validated = module.run_activation(
                bundle_root=ROOT,
                codex_home=codex_home,
                project_root=project_root,
                verify=True,
            )
            self.assertEqual("VALIDATED", validated["status"])
            self.assertEqual([], validated["writes"])

    def test_user_activation_is_idempotent_and_preserves_unmanaged_agents_bytes(self) -> None:
        module = load_module(ACTIVATION_MODULE, "public_activate_wukong_idempotence")
        with tempfile.TemporaryDirectory() as temp_dir:
            sandbox = Path(temp_dir)
            codex_home = sandbox / ".codex"
            codex_home.mkdir(parents=True, exist_ok=True)
            home_agents = codex_home / "AGENTS.md"
            prefix = "# Local Header\n\nKeep this unmanaged preface.\n"
            suffix = "\nKeep this unmanaged suffix.\n"
            home_agents.write_text(prefix + suffix, encoding="utf-8", newline="\n")

            first = module.run_activation(bundle_root=ROOT, codex_home=codex_home)
            second = module.run_activation(bundle_root=ROOT, codex_home=codex_home)
            verify = module.run_activation(bundle_root=ROOT, codex_home=codex_home, verify=True)

            self.assertEqual("ACTIVATED", first["status"])
            self.assertEqual("ACTIVATED", second["status"])
            self.assertEqual("VALIDATED", verify["status"])
            self.assertEqual([], verify["writes"])

            merged = home_agents.read_text(encoding="utf-8")
            self.assertIn(prefix.strip(), merged)
            self.assertIn(suffix.strip(), merged)
            self.assertEqual(1, merged.count(module.SENTINEL_BEGIN))
            self.assertEqual(1, merged.count(module.SENTINEL_END))
            self.assertIn("Wukong is the user-facing coordinator.", merged)
            self.assertTrue((codex_home / "skills" / "wukong-always" / "SKILL.md").exists())
            self.assertTrue((codex_home / "skills" / "multi-agent-wukong" / "SKILL.md").exists())

    def test_cli_verify_emits_validated_and_no_writes(self) -> None:
        module = load_module(ACTIVATION_MODULE, "public_activate_wukong_cli")
        with tempfile.TemporaryDirectory() as temp_dir:
            sandbox = Path(temp_dir)
            codex_home = sandbox / ".codex"
            project_root = sandbox / "project"
            make_live_project(project_root)
            module.run_activation(bundle_root=ROOT, codex_home=codex_home, project_root=project_root)
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = module.main(
                    [
                        "--bundle-root",
                        str(ROOT),
                        "--codex-home",
                        str(codex_home),
                        "--project-root",
                        str(project_root),
                        "--verify",
                    ]
                )
            payload = json.loads(buffer.getvalue())
            self.assertEqual(0, exit_code)
            self.assertEqual("VALIDATED", payload["status"])
            self.assertEqual([], payload["writes"])

    def test_docs_describe_passive_bundle_vs_activated_install_and_document_loop(self) -> None:
        readme_text = README.read_text(encoding="utf-8")
        self.assertIn("Passive bundle vs activated install", readme_text)
        self.assertIn("PROJECT-CONTROL -> task package -> Subagent -> historian -> verifier -> update", readme_text)
        self.assertIn("python -X utf8 scripts/activate_wukong.py", readme_text)
        for path in DOCS:
            text = path.read_text(encoding="utf-8")
            with self.subTest(path=path.name):
                self.assertIn("ACTIVATED", text)
                self.assertIn("VALIDATED", text)
                self.assertIn("--project-root", text)
                self.assertIn("--bootstrap-doc", text)

    def test_public_contract_requires_cas_fields_and_historian_before_summary(self) -> None:
        agents_text = PUBLIC_AGENTS.read_text(encoding="utf-8")
        skill_text = MULTI_AGENT.read_text(encoding="utf-8")
        for text in (agents_text, skill_text):
            for token in (
                "control_document.path",
                "control_document.schema",
                "control_document.revision",
                "control_document.sha256",
                "control_document.required_sections",
                "authorization",
                "external capability evaluation",
                "historian target",
                "historian merge",
                "independent verifier",
                "no-recursion",
                "historian merge before final user summary",
            ):
                with self.subTest(token=token):
                    self.assertIn(token, text)

    def test_plugin_version_and_role_map_counts_are_stable(self) -> None:
        manifest = json.loads((ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
        role_map = json.loads(ROLE_MAP.read_text(encoding="utf-8"))
        self.assertEqual("0.2.0", manifest["version"])
        self.assertEqual(243, role_map["agent_count"])
        self.assertEqual(10, len(role_map["roles"]))
        self.assertEqual(476, sum(len(agent["secondary_roles"]) for agent in role_map["agents"].values()))

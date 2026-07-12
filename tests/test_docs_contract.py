from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class DocumentationContractTests(unittest.TestCase):
    def read(self, relative: str) -> str:
        return (ROOT / relative).read_text(encoding="utf-8")

    def test_plugin_manifest_is_v020(self) -> None:
        manifest = json.loads(self.read(".codex-plugin/plugin.json"))
        self.assertEqual("0.2.0", manifest["version"])

    def test_readme_presents_five_minute_cross_platform_install_and_identity(self) -> None:
        text = self.read("README.md")
        required = (
            "five-minute",
            "clone alone is passive",
            "activation is required",
            "Windows",
            "macOS",
            "Linux",
            "scripts/install_wukong.py",
            "scripts/doctor_wukong.py",
            "scripts/activate_wukong.py",
            "scripts/uninstall_wukong.py",
            "--bootstrap-doc",
            "Role=Wukong/悟空",
            "PROJECT-CONTROL.md",
            "project-control/v1",
            "revision",
            "sha256",
            "status",
            "INSTALLED",
            "HEALTHY",
            "VALIDATED",
            "UPGRADED",
            "ROLLED_BACK",
            "UNINSTALLED",
        )
        for token in required:
            with self.subTest(token=token):
                self.assertIn(token, text)

    def test_lifecycle_doc_covers_each_workflow_and_attribution(self) -> None:
        text = self.read("docs/install-lifecycle.md")
        required_headings = (
            "Five-minute quickstart",
            "First safe dialogue test",
            "Upgrade",
            "Rollback",
            "Uninstall",
            "Residual-file policy",
            "Compatibility matrix",
            "Privacy and redaction",
            "Troubleshooting",
        )
        for heading in required_headings:
            with self.subTest(heading=heading):
                self.assertRegex(text, rf"(?m)^## .*{re.escape(heading)}.*$")

        for section in re.split(r"(?=^## )", text, flags=re.MULTILINE):
            if not section.startswith("## "):
                continue
            heading = section.splitlines()[0]
            if any(name in heading for name in required_headings):
                for token in (
                    "Role=Wukong/悟空",
                    "Role=Public Historian/公共史官",
                    "PROJECT-CONTROL.md",
                    "project-control/v1",
                    "revision",
                    "sha256",
                    "status",
                ):
                    with self.subTest(section=heading, token=token):
                        self.assertIn(token, section)

    def test_root_agents_retains_coordinator_no_recursion_and_verifier_contracts(self) -> None:
        text = self.read("AGENTS.md")
        for token in (
            "coordinator-only",
            "never performs substantive work",
            "Delegation permission: FORBIDDEN",
            "Recursive dispatch",
            "independent verification",
            "Every substantive task needs user confirmation",
        ):
            with self.subTest(token=token):
                self.assertIn(token, text)

    def test_examples_cover_development_research_and_project_initialization(self) -> None:
        for relative in (
            "examples/software-development.md",
            "examples/research.md",
            "examples/project-initialization.md",
        ):
            text = self.read(relative)
            for token in (
                "Role=Wukong/悟空",
                "Role=Public Historian/公共史官",
                "PROJECT-CONTROL.md",
                "project-control/v1",
                "sha256",
                "status",
            ):
                with self.subTest(file=relative, token=token):
                    self.assertIn(token, text)

    def test_public_payload_policy_excludes_private_evidence_and_control_snapshots(self) -> None:
        text = self.read("README.md") + self.read("docs/install-lifecycle.md")
        for token in (
            "release-evidence/",
            "not part of the public payload",
            ".wukong/",
            "private control snapshots",
        ):
            with self.subTest(token=token):
                self.assertIn(token, text)


if __name__ == "__main__":
    unittest.main()

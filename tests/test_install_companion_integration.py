from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
EXPECTED_SKILLS = ("wukong-always", "multi-agent-wukong", "codex-history")


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"missing lifecycle helper: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def public_skill_files(skill_name: str) -> set[Path]:
    source_root = ROOT / "skills" / skill_name
    return {
        Path("skills") / skill_name / source.relative_to(source_root)
        for source in source_root.rglob("*")
        if source.is_file() and "__pycache__" not in source.parts and source.suffix != ".pyc"
    }


class InstallCompanionIntegrationTests(unittest.TestCase):
    def test_install_registers_and_owns_all_public_skills_and_uninstall_preserves_user_edits_and_control(self) -> None:
        activate = load_module(SCRIPTS / "activate_wukong.py", "integration_activate_companion")
        install = load_module(SCRIPTS / "install_wukong.py", "integration_install_companion")
        uninstall = load_module(SCRIPTS / "uninstall_wukong.py", "integration_uninstall_companion")
        with tempfile.TemporaryDirectory() as temp_dir:
            sandbox = Path(temp_dir)
            codex_home = sandbox / ".codex"
            project = sandbox / "project"

            installed = install.run_install(
                bundle_root=ROOT,
                codex_home=codex_home,
                project_root=project,
                bootstrap_doc=True,
            )

            self.assertEqual("INSTALLED", installed["status"])
            self.assertTrue((codex_home / "skills" / "codex-history" / "SKILL.md").exists())
            activated = activate.run_activation(bundle_root=ROOT, codex_home=codex_home, verify=True)
            self.assertIn("user_skill:codex-history", activated["checks"])

            state = json.loads(Path(installed["state_path"]).read_text(encoding="utf-8"))
            owned_skill_paths = {
                Path(item["path"]).relative_to(codex_home)
                for item in state["files"]
                if item["kind"] == "skill"
            }
            expected_skill_paths = set().union(*(public_skill_files(name) for name in EXPECTED_SKILLS))
            self.assertEqual(expected_skill_paths, owned_skill_paths)
            self.assertTrue(all(item["ownership"] == "wukong" for item in state["files"] if item["kind"] == "skill"))

            home_agents = codex_home / "AGENTS.md"
            project_agents = project / "AGENTS.md"
            home_agents.write_text(home_agents.read_text(encoding="utf-8") + "\nUser-owned footer.\n", encoding="utf-8")
            project_agents.write_text(project_agents.read_text(encoding="utf-8") + "\nProject user edit.\n", encoding="utf-8")

            result = uninstall.run_uninstall(
                bundle_root=ROOT,
                codex_home=codex_home,
                project_root=project,
            )

            self.assertEqual("UNINSTALLED", result["status"])
            self.assertTrue((project / "docs" / "wukong" / "PROJECT-CONTROL.md").exists())
            self.assertIn("User-owned footer.", home_agents.read_text(encoding="utf-8"))
            self.assertIn("Project user edit.", project_agents.read_text(encoding="utf-8"))
            for skill_name in EXPECTED_SKILLS:
                self.assertFalse((codex_home / "skills" / skill_name).exists())

    def test_edited_historian_companion_blocks_uninstall_without_losing_bytes(self) -> None:
        install = load_module(SCRIPTS / "install_wukong.py", "integration_install_companion_conflict")
        uninstall = load_module(SCRIPTS / "uninstall_wukong.py", "integration_uninstall_companion_conflict")
        with tempfile.TemporaryDirectory() as temp_dir:
            sandbox = Path(temp_dir)
            codex_home = sandbox / ".codex"
            installed = install.run_install(bundle_root=ROOT, codex_home=codex_home)
            self.assertEqual("INSTALLED", installed["status"])

            target = codex_home / "skills" / "codex-history" / "SKILL.md"
            self.assertTrue(target.exists(), "the Public Historian companion must be installed before ownership can be checked")
            target.write_text(target.read_text(encoding="utf-8") + "\nUser historian edit.\n", encoding="utf-8")
            edited = target.read_bytes()

            result = uninstall.run_uninstall(bundle_root=ROOT, codex_home=codex_home)

            self.assertEqual("BLOCKED", result["status"])
            self.assertEqual("BLOCKED_OWNERSHIP_CONFLICT", result["code"])
            self.assertEqual(edited, target.read_bytes())


if __name__ == "__main__":
    unittest.main()

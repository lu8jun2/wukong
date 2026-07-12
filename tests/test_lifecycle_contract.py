from __future__ import annotations

import importlib.util
import io
import json
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
INSTALL_SCRIPT = SCRIPTS / "install_wukong.py"
UNINSTALL_SCRIPT = SCRIPTS / "uninstall_wukong.py"
DOCTOR_SCRIPT = SCRIPTS / "doctor_wukong.py"
ACTIVATE_SCRIPT = SCRIPTS / "activate_wukong.py"


def load_module(path: Path, name: str):
    if not path.exists():
        raise AssertionError(f"missing lifecycle helper: {path}")
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
        "# Project AGENTS\n\n"
        "- Wukong is the visible coordinator.\n"
        "- Project work starts only after `<project-root>/docs/wukong/PROJECT-CONTROL.md` exists.\n",
        encoding="utf-8",
        newline="\n",
    )
    return control_doc


def copy_bundle_with_version(source: Path, destination: Path, version: str, marker: str = "") -> Path:
    shutil.copytree(
        source,
        destination,
        ignore=shutil.ignore_patterns(".git", "__pycache__", "release-evidence"),
    )
    manifest_path = destination / ".codex-plugin" / "plugin.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["version"] = version
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if marker:
        skill = destination / "skills" / "wukong-always" / "SKILL.md"
        skill.write_text(skill.read_text(encoding="utf-8") + f"\n{marker}\n", encoding="utf-8")
    return destination


class LifecycleContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.assertTrue(INSTALL_SCRIPT.exists(), "scripts/install_wukong.py must exist")
        self.assertTrue(UNINSTALL_SCRIPT.exists(), "scripts/uninstall_wukong.py must exist")
        self.assertTrue(DOCTOR_SCRIPT.exists(), "scripts/doctor_wukong.py must exist")

    def test_install_is_idempotent_and_records_identity_and_control_cas(self) -> None:
        install = load_module(INSTALL_SCRIPT, "lifecycle_install_idempotence")
        with tempfile.TemporaryDirectory() as temp_dir:
            sandbox = Path(temp_dir)
            project = sandbox / "project"
            control = make_live_project(project)
            codex_home = sandbox / ".codex"

            first = install.run_install(bundle_root=ROOT, codex_home=codex_home, project_root=project)
            second = install.run_install(bundle_root=ROOT, codex_home=codex_home, project_root=project)

            self.assertEqual("INSTALLED", first["status"])
            self.assertEqual("INSTALLED", second["status"])
            self.assertFalse(second["changed"])
            self.assertEqual("Wukong", second["identity"]["name"])
            self.assertEqual("wukong-public-staging", second["identity"]["package"])
            self.assertEqual(str(control), second["project_control"]["path"])
            self.assertEqual("project-control/v1", second["project_control"]["schema"])
            self.assertEqual("r1", second["project_control"]["revision"])
            self.assertEqual("VALID", second["project_control"]["status"])
            state_path = Path(second["state_path"])
            state = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual("wukong-install-state/v1", state["format"])
            self.assertEqual("Wukong", state["identity"]["name"])
            self.assertTrue(state["files"])
            for item in state["files"]:
                self.assertEqual(item["installed_sha256"], install.sha256(Path(item["path"])))

    def test_project_mode_requires_control_unless_explicit_bootstrap(self) -> None:
        install = load_module(INSTALL_SCRIPT, "lifecycle_install_bootstrap")
        with tempfile.TemporaryDirectory() as temp_dir:
            sandbox = Path(temp_dir)
            project = sandbox / "project"
            codex_home = sandbox / ".codex"

            blocked = install.run_install(bundle_root=ROOT, codex_home=codex_home, project_root=project)
            self.assertEqual("BLOCKED", blocked["status"])
            self.assertEqual("BLOCKED_PROJECT_DOCS_MISSING", blocked["code"])
            self.assertFalse((project / "docs" / "wukong" / "PROJECT-CONTROL.md").exists())

            bootstrapped = install.run_install(
                bundle_root=ROOT,
                codex_home=codex_home,
                project_root=project,
                bootstrap_doc=True,
            )
            self.assertEqual("INSTALLED", bootstrapped["status"])
            self.assertEqual("VALID", bootstrapped["project_control"]["status"])

    def test_v01_managed_marker_surface_is_adopted_without_reinstalling_as_conflict(self) -> None:
        install = load_module(INSTALL_SCRIPT, "lifecycle_install_legacy")
        activate = load_module(ACTIVATE_SCRIPT, "lifecycle_activate_legacy")
        with tempfile.TemporaryDirectory() as temp_dir:
            codex_home = Path(temp_dir) / ".codex"
            activated = activate.run_activation(bundle_root=ROOT, codex_home=codex_home)
            self.assertEqual("ACTIVATED", activated["status"])
            self.assertFalse((codex_home / ".wukong" / "install-state.json").exists())

            adopted = install.run_install(bundle_root=ROOT, codex_home=codex_home)

            self.assertEqual("INSTALLED", adopted["status"])
            self.assertEqual("legacy-marker-adopted", adopted["ownership"])
            self.assertTrue((codex_home / ".wukong" / "install-state.json").exists())

    def test_edited_owned_file_fails_closed_before_upgrade_and_preserves_bytes(self) -> None:
        install = load_module(INSTALL_SCRIPT, "lifecycle_install_conflict")
        with tempfile.TemporaryDirectory() as temp_dir:
            sandbox = Path(temp_dir)
            codex_home = sandbox / ".codex"
            first = install.run_install(bundle_root=ROOT, codex_home=codex_home)
            self.assertEqual("INSTALLED", first["status"])
            target = codex_home / "skills" / "wukong-always" / "SKILL.md"
            target.write_text(target.read_text(encoding="utf-8") + "\nUSER EDIT\n", encoding="utf-8")
            edited = target.read_bytes()
            bundle = copy_bundle_with_version(ROOT, sandbox / "bundle-014", "0.1.4", "UPGRADE")

            result = install.run_install(bundle_root=bundle, codex_home=codex_home)

            self.assertEqual("BLOCKED", result["status"])
            self.assertEqual("BLOCKED_OWNERSHIP_CONFLICT", result["code"])
            self.assertEqual(edited, target.read_bytes())
            state = json.loads((codex_home / ".wukong" / "install-state.json").read_text(encoding="utf-8"))
            self.assertEqual("0.2.0", state["identity"]["version"])

    def test_upgrade_creates_hash_backups_and_rollback_restores_previous_release(self) -> None:
        install = load_module(INSTALL_SCRIPT, "lifecycle_install_rollback")
        with tempfile.TemporaryDirectory() as temp_dir:
            sandbox = Path(temp_dir)
            codex_home = sandbox / ".codex"
            first = install.run_install(bundle_root=ROOT, codex_home=codex_home)
            target = codex_home / "skills" / "wukong-always" / "SKILL.md"
            previous = target.read_bytes()
            bundle = copy_bundle_with_version(ROOT, sandbox / "bundle-014", "0.1.4", "UPGRADE")

            upgraded = install.run_install(bundle_root=bundle, codex_home=codex_home)
            self.assertEqual("UPGRADED", upgraded["status"])
            self.assertTrue(upgraded["backups"])
            self.assertNotEqual(previous, target.read_bytes())
            backup_manifest = Path(upgraded["backups"][0]) / "backup-manifest.json"
            self.assertTrue(backup_manifest.exists())
            self.assertTrue(json.loads(backup_manifest.read_text(encoding="utf-8"))["files"])

            rolled_back = install.run_install(bundle_root=ROOT, codex_home=codex_home, rollback=True)

            self.assertEqual("ROLLED_BACK", rolled_back["status"])
            self.assertEqual(previous, target.read_bytes())
            state = json.loads((codex_home / ".wukong" / "install-state.json").read_text(encoding="utf-8"))
            self.assertEqual("0.2.0", state["identity"]["version"])

    def test_doctor_is_read_only_and_reports_identity_and_control_status_cas(self) -> None:
        install = load_module(INSTALL_SCRIPT, "lifecycle_install_doctor")
        doctor = load_module(DOCTOR_SCRIPT, "lifecycle_doctor")
        with tempfile.TemporaryDirectory() as temp_dir:
            sandbox = Path(temp_dir)
            project = sandbox / "project"
            control = make_live_project(project)
            codex_home = sandbox / ".codex"
            installed = install.run_install(bundle_root=ROOT, codex_home=codex_home, project_root=project)
            state_before = (codex_home / ".wukong" / "install-state.json").read_bytes()

            healthy = doctor.run_doctor(bundle_root=ROOT, codex_home=codex_home, project_root=project)

            self.assertEqual("HEALTHY", healthy["status"])
            self.assertEqual("Wukong", healthy["identity"]["name"])
            self.assertEqual(str(control), healthy["project_control"]["path"])
            self.assertEqual(installed["project_control"]["sha256"], healthy["project_control"]["sha256"])
            self.assertEqual(state_before, (codex_home / ".wukong" / "install-state.json").read_bytes())

            control.write_text(control.read_text(encoding="utf-8") + "\nUser revision.\n", encoding="utf-8")
            degraded = doctor.run_doctor(bundle_root=ROOT, codex_home=codex_home, project_root=project)
            self.assertEqual("DEGRADED", degraded["status"])
            self.assertEqual("CONFLICT", degraded["project_control"]["status"])

    def test_default_uninstall_removes_only_owned_unchanged_content_and_preserves_user_edits_and_control(self) -> None:
        install = load_module(INSTALL_SCRIPT, "lifecycle_install_uninstall")
        uninstall = load_module(UNINSTALL_SCRIPT, "lifecycle_uninstall")
        with tempfile.TemporaryDirectory() as temp_dir:
            sandbox = Path(temp_dir)
            project = sandbox / "project"
            control = make_live_project(project)
            codex_home = sandbox / ".codex"
            installed = install.run_install(bundle_root=ROOT, codex_home=codex_home, project_root=project)
            home_agents = codex_home / "AGENTS.md"
            home_agents.write_text(home_agents.read_text(encoding="utf-8") + "\nUser-owned footer.\n", encoding="utf-8")
            project_agents = project / "AGENTS.md"
            project_agents.write_text(project_agents.read_text(encoding="utf-8") + "\nProject user edit.\n", encoding="utf-8")
            unrelated = project / "docs" / "wukong" / "keep.txt"
            unrelated.write_text("keep", encoding="utf-8")

            result = uninstall.run_uninstall(
                bundle_root=ROOT,
                codex_home=codex_home,
                project_root=project,
            )

            self.assertEqual("UNINSTALLED", result["status"])
            self.assertTrue(control.exists())
            self.assertTrue(unrelated.exists())
            self.assertIn("User-owned footer.", home_agents.read_text(encoding="utf-8"))
            self.assertNotIn(install.SENTINEL_BEGIN, home_agents.read_text(encoding="utf-8"))
            self.assertIn("Project user edit.", project_agents.read_text(encoding="utf-8"))
            self.assertFalse((codex_home / "skills" / "wukong-always").exists())
            self.assertFalse((codex_home / ".wukong" / "install-state.json").exists())
            self.assertEqual("PRESERVED", result["project_control"]["status"])

    def test_existing_project_agents_is_never_misclassified_as_bootstrap_owned(self) -> None:
        install = load_module(INSTALL_SCRIPT, "lifecycle_install_existing_project_agents")
        uninstall = load_module(UNINSTALL_SCRIPT, "lifecycle_uninstall_existing_project_agents")
        with tempfile.TemporaryDirectory() as temp_dir:
            sandbox = Path(temp_dir)
            project = sandbox / "project"
            control = make_live_project(project)
            project_agents = project / "AGENTS.md"
            original = project_agents.read_bytes()
            codex_home = sandbox / ".codex"

            installed = install.run_install(bundle_root=ROOT, codex_home=codex_home, project_root=project)
            state = json.loads(Path(installed["state_path"]).read_text(encoding="utf-8"))
            project_entry = next(item for item in state["files"] if item["kind"] == "project-agents")
            self.assertFalse(project_entry["created_by_wukong"])

            result = uninstall.run_uninstall(bundle_root=ROOT, codex_home=codex_home, project_root=project)

            self.assertEqual("UNINSTALLED", result["status"])
            self.assertEqual(original, project_agents.read_bytes())
            self.assertTrue(control.exists())

    def test_uninstall_conflict_is_fail_closed_and_exact_purge_confirmation_is_required(self) -> None:
        install = load_module(INSTALL_SCRIPT, "lifecycle_install_purge")
        uninstall = load_module(UNINSTALL_SCRIPT, "lifecycle_uninstall_purge")
        with tempfile.TemporaryDirectory() as temp_dir:
            sandbox = Path(temp_dir)
            project = sandbox / "project"
            control = make_live_project(project)
            codex_home = sandbox / ".codex"
            install.run_install(bundle_root=ROOT, codex_home=codex_home, project_root=project)

            missing_confirmation = uninstall.run_uninstall(
                bundle_root=ROOT,
                codex_home=codex_home,
                project_root=project,
                purge_project_control=True,
                confirm_purge="PROJECT-CONTROL now",
            )
            self.assertEqual("BLOCKED", missing_confirmation["status"])
            self.assertEqual("BLOCKED_PURGE_CONFIRMATION_REQUIRED", missing_confirmation["code"])
            self.assertTrue(control.exists())
            self.assertTrue((codex_home / "skills" / "wukong-always" / "SKILL.md").exists())

            exact = uninstall.run_uninstall(
                bundle_root=ROOT,
                codex_home=codex_home,
                project_root=project,
                purge_project_control=True,
                confirm_purge="PROJECT-CONTROL",
            )
            self.assertEqual("UNINSTALLED", exact["status"])
            self.assertFalse(control.exists())

    def test_cli_status_output_contains_wukong_identity_and_project_control_cas(self) -> None:
        install = load_module(INSTALL_SCRIPT, "lifecycle_install_cli")
        doctor = load_module(DOCTOR_SCRIPT, "lifecycle_doctor_cli")
        with tempfile.TemporaryDirectory() as temp_dir:
            sandbox = Path(temp_dir)
            project = sandbox / "project"
            control = make_live_project(project)
            codex_home = sandbox / ".codex"
            install.run_install(bundle_root=ROOT, codex_home=codex_home, project_root=project)
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = doctor.main(
                    [
                        "--bundle-root",
                        str(ROOT),
                        "--codex-home",
                        str(codex_home),
                        "--project-root",
                        str(project),
                    ]
                )
            payload = json.loads(buffer.getvalue())
            self.assertEqual(0, exit_code)
            self.assertEqual("Wukong", payload["identity"]["name"])
            self.assertEqual("wukong-public-staging", payload["identity"]["package"])
            self.assertEqual(str(control), payload["project_control"]["path"])
            self.assertEqual("project-control/v1", payload["project_control"]["schema"])
            self.assertRegex(payload["project_control"]["sha256"], r"^[0-9a-f]{64}$")
            self.assertIn(payload["project_control"]["status"], {"VALID", "PRESERVED", "CONFLICT"})


if __name__ == "__main__":
    unittest.main()

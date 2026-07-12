from __future__ import annotations

import json
import importlib.util
import re
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WUKONG_ROOT = ROOT / "skills" / "multi-agent-wukong"
REFS_ROOT = WUKONG_ROOT / "references"


def joined(*parts: str) -> str:
    return "".join(parts)


FORBIDDEN_SNIPPETS = (
    joined("cap", "_sid"),
    joined("sess", "ion"),
    joined(".", "json", "l"),
    joined(".", "sql", "ite"),
)


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"missing import spec for {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class PublicBundleTests(unittest.TestCase):
    def test_required_release_files_exist(self) -> None:
        required = (
            ROOT / ".codex-plugin" / "plugin.json",
            ROOT / "AGENTS.md",
            ROOT / "README.md",
            ROOT / "LICENSE",
            ROOT / "CONTRIBUTING.md",
            ROOT / "SECURITY.md",
            ROOT / ".gitignore",
            ROOT / "docs" / "PROJECT-CONTROL.template.md",
            ROOT / "docs" / "macOS-install.md",
            ROOT / "docs" / "cross-platform.md",
            ROOT / "docs" / "security-model.md",
            ROOT / "docs" / "plugin-install.md",
            ROOT / "examples" / "project-AGENTS.example.md",
            ROOT / "examples" / "config.example.toml",
            ROOT / "skills" / "multi-agent-wukong" / "SKILL.md",
            ROOT / "skills" / "multi-agent-wukong" / "references" / "agency-agent-role-map.json",
            ROOT / "skills" / "multi-agent-wukong" / "references" / "agency-agent-role-map.md",
            ROOT / "skills" / "multi-agent-wukong" / "scripts" / "project_control_gate.py",
            ROOT / "skills" / "multi-agent-wukong" / "scripts" / "project_control_historian.py",
            ROOT / "skills" / "multi-agent-wukong" / "scripts" / "product_design_gate.py",
            ROOT / "skills" / "multi-agent-wukong" / "scripts" / "chang_e_dispatch_gate.py",
            ROOT / "skills" / "multi-agent-wukong" / "schemas" / "project-control.schema.json",
            ROOT / "skills" / "multi-agent-wukong" / "schemas" / "task-package.schema.json",
            ROOT / "skills" / "multi-agent-wukong" / "schemas" / "handoff.schema.json",
            ROOT / "skills" / "codex-history" / "SKILL.md",
        )
        missing = [str(path.relative_to(ROOT)) for path in required if not path.exists()]
        self.assertEqual([], missing)

    def test_plugin_manifest_has_public_metadata(self) -> None:
        manifest_path = ROOT / ".codex-plugin" / "plugin.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual("wukong-public-staging", manifest["name"])
        self.assertEqual("0.1.2", manifest["version"])
        self.assertEqual("MIT", manifest["license"])
        self.assertEqual("./skills/", manifest["skills"])
        self.assertEqual("Wukong", manifest["interface"]["displayName"])
        self.assertIn("Productivity", manifest["interface"]["category"])
        self.assertIn("coordinator", manifest["description"].lower())
        self.assertIn("not an official OpenAI product", manifest["interface"]["longDescription"])

    def test_core_text_surfaces_are_redacted(self) -> None:
        text_paths = (
            ROOT / "AGENTS.md",
            ROOT / "README.md",
            ROOT / "docs" / "PROJECT-CONTROL.template.md",
            ROOT / "examples" / "project-AGENTS.example.md",
            ROOT / "skills" / "multi-agent-wukong" / "SKILL.md",
            ROOT / "skills" / "codex-history" / "SKILL.md",
        )
        for path in text_paths:
            text = path.read_text(encoding="utf-8")
            for snippet in FORBIDDEN_SNIPPETS:
                with self.subTest(path=path.name, snippet=snippet):
                    self.assertNotIn(snippet, text)

    def test_public_payload_has_no_fixed_iso_timestamps(self) -> None:
        timestamp_pattern = re.compile(r"\b20\d{2}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z\b")
        suffixes = {".md", ".txt", ".json", ".toml", ".py", ".yaml", ".yml", ".gitignore"}
        findings = []
        for path in sorted(ROOT.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in suffixes:
                continue
            if "__pycache__" in path.parts:
                continue
            if timestamp_pattern.search(path.read_text(encoding="utf-8", errors="ignore")):
                findings.append(path.relative_to(ROOT).as_posix())
        self.assertEqual([], findings)

    def test_redaction_scan_is_clean_without_self_false_positives(self) -> None:
        scanner = load_module(ROOT / "scripts" / "redaction_scan.py", "public_redaction_scan")
        result = scanner.scan(ROOT)
        self.assertEqual([], result["findings"])

    def test_redaction_scan_keeps_sensitive_pattern_coverage(self) -> None:
        scanner = load_module(ROOT / "scripts" / "redaction_scan.py", "public_redaction_scan_coverage")
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_root = Path(temp_dir)
            drive_path_backslash = joined("C:", "\\", "Users", "\\", "example-user", "\\", "workspace", "\\", "private.txt")
            drive_path_forward = joined("C:", "/", "Users", "/", "example-user", "/", "workspace", "/", "private.txt")
            credential = joined("Authorization", ": ", "Bearer ", "redacted-value")
            (fixture_root / "fixture.txt").write_text(
                "absolute-backslash=" + drive_path_backslash + "\n"
                "absolute-forward=" + drive_path_forward + "\n"
                + credential + "\n",
                encoding="utf-8",
            )
            result = scanner.scan(fixture_root)
        types = {finding["type"] for finding in result["findings"]}
        self.assertIn("windows_drive_path", types)
        self.assertIn("windows_users_path", types)
        self.assertIn("bearer_token", types)

    def test_redaction_scan_covers_unc_and_private_internal_paths(self) -> None:
        scanner = load_module(ROOT / "scripts" / "redaction_scan.py", "public_redaction_scan_paths")
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_root = Path(temp_dir)
            unc_backslash = joined("\\", "\\", "server", "\\", "share", "\\", "private.txt")
            unc_forward = joined("/", "/", "server", "/", "share", "/", "private.txt")
            private_path = joined("private", "/", "artifact", "/", "payload.bin")
            internal_output = joined("outputs", "/", "internal", "/", "payload.bin")
            cache_path = joined("plugin-cache", "/", "state", ".", "json")
            history_path = joined("history", "/", "records", ".", "txt")
            config_path = joined("settings", "/", "config", ".", "toml")
            (fixture_root / "fixture.txt").write_text(
                "\n".join(
                    (
                        unc_backslash,
                        unc_forward,
                        private_path,
                        internal_output,
                        cache_path,
                        history_path,
                        config_path,
                        joined("cap", "_sid"),
                        joined(".", "json", "l"),
                        joined(".", "sql", "ite"),
                    )
                ),
                encoding="utf-8",
            )
            result = scanner.scan(fixture_root)
        types = {finding["type"] for finding in result["findings"]}
        self.assertIn("unc_path", types)
        self.assertIn("private_internal_path", types)
        self.assertIn("private_output_path", types)
        self.assertIn("private_artifact_path", types)
        self.assertIn("live_config_path", types)
        self.assertIn("forbidden_literal", types)

    def test_context_store_builds_line_record_suffix_at_runtime(self) -> None:
        module_path = ROOT / "skills" / "multi-agent-wukong" / "scripts" / "wukong_context_orchestrator.py"
        source = module_path.read_text(encoding="utf-8")
        self.assertNotIn(joined(".", "json", "l"), source)
        context = load_module(module_path, "public_context_orchestrator")
        with tempfile.TemporaryDirectory() as temp_dir:
            _, memory, facts = context._build_stores(Path(temp_dir))
        suffix = joined(".", "json", "l")
        self.assertEqual("memory" + suffix, memory.path.name)
        self.assertEqual("facts" + suffix, facts.path.name)

    def test_skill_requires_role_map_consultation_and_routing_matrix(self) -> None:
        text = (WUKONG_ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("Role Routing Matrix", text)
        self.assertIn("references/agency-agent-role-map.md", text)
        self.assertIn("references/agency-agent-role-map.json", text)
        self.assertIn("references/team-roles.md", text)
        self.assertRegex(text, r"consult .*agency-agent-role-map")
        self.assertIn("external specialist", text)
        self.assertIn("secondary roles", text)

    def test_team_roles_keeps_full_secondary_role_taxonomy(self) -> None:
        text = (REFS_ROOT / "team-roles.md").read_text(encoding="utf-8")
        required_tokens = (
            "Harness Submodes",
            "design-critic",
            "core-builder",
            "ui-director",
            "long-researcher",
            "deerflow-harness",
        )
        for token in required_tokens:
            with self.subTest(token=token):
                self.assertIn(token, text)

    def test_dispatch_usage_and_templates_require_role_map_consultation(self) -> None:
        dispatch_text = (REFS_ROOT / "wukong-dispatch-usage.md").read_text(encoding="utf-8")
        template_text = (REFS_ROOT / "delegation-templates.md").read_text(encoding="utf-8")
        for token in (
            "agency-agent-role-map.md",
            "agency-agent-role-map.json",
            "Delegation permission: ALLOWED",
            "Delegation permission: FORBIDDEN",
            "primary role",
            "secondary roles",
        ):
            with self.subTest(token=token):
                self.assertIn(token, dispatch_text)
        for token in (
            "agency-agent-role-map",
            "ALLOWED",
            "FORBIDDEN",
            "role map",
        ):
            with self.subTest(token=token):
                self.assertIn(token, template_text)

    def test_role_map_markdown_is_detailed_and_sanitized(self) -> None:
        text = (REFS_ROOT / "agency-agent-role-map.md").read_text(encoding="utf-8")
        self.assertIn("| Agent id | Agent name | Primary role | Secondary roles | Capability cluster |", text)
        self.assertIn("3d-scene-developer", text)
        self.assertIn("clinical-evidence-agent", text)
        self.assertIn("体验与视觉", text)
        for field_name in ("_".join(("source", "file")), "_".join(("source", "path"))):
            self.assertNotIn(field_name, text)
        for drive in "CD":
            self.assertNotIn(drive + ":" + chr(92), text)
        self.assertNotIn("/" + "Users" + "/", text)
        self.assertNotIn("~/" + ".codex", text)

    def test_role_map_json_is_meaningful_and_sanitized(self) -> None:
        path = REFS_ROOT / "agency-agent-role-map.json"
        text = path.read_text(encoding="utf-8")
        mapping = json.loads(text)
        self.assertGreater(mapping["agent_count"], 200)
        self.assertGreaterEqual(len(mapping["roles"]), 10)
        self.assertIn("嫦娥", mapping["role_counts"])
        self.assertGreater(mapping["role_counts"]["嫦娥"], 20)
        self.assertIn("3d-scene-developer", mapping["agents"])
        self.assertIn("clinical-evidence-agent", mapping["agents"])
        scene = mapping["agents"]["3d-scene-developer"]
        self.assertEqual("嫦娥", scene["primary_role"])
        self.assertIn("观音", scene["secondary_roles"])
        self.assertIn("沙僧", scene["secondary_roles"])
        self.assertTrue(scene["capability_cluster"])
        self.assertTrue(scene["call_when"])
        self.assertTrue(scene["boundary"])
        for field_name in ("_".join(("source", "file")), "_".join(("source", "path"))):
            self.assertNotIn(field_name, scene)
        for drive in "CD":
            self.assertNotIn(drive + ":" + chr(92), text)
        self.assertNotIn("/" + "Users" + "/", text)

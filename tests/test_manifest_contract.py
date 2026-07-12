from __future__ import annotations

import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILD_MANIFEST = ROOT / "scripts" / "build_manifest.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"missing import spec for {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class ManifestContractTests(unittest.TestCase):
    def test_public_manifest_excludes_private_release_evidence_and_control_doc(self) -> None:
        module = load_module(BUILD_MANIFEST, "manifest_contract_builder")
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            output = root / "MANIFEST.json"
            (root / "public.txt").write_text("public", encoding="utf-8")
            (root / "commands.json").write_text("{}", encoding="utf-8")
            (root / "redaction.json").write_text("{}", encoding="utf-8")

            private_files = (
                "docs/wukong/PROJECT-CONTROL.md",
                "release-evidence/validation-summary.json",
                "release-evidence/MANIFEST.json",
                ".pytest_cache/v/cache/nodeids",
                ".mypy_cache/3.14/cache.json",
                "__pycache__/fixture.pyc",
                "nested/MANIFEST.json",
                "credentials-and-secrets/token.txt",
                "private-absolute-paths/paths.txt",
                "session-history-cache-backup-artifacts/history.json",
                "live-machine-config/config.json",
                "private-project-outputs/output.txt",
                "manifest-self-reference/reference.txt",
            )

            for relative_path in private_files:
                path = root / relative_path
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("private", encoding="utf-8")

            output.write_text("{}", encoding="utf-8")
            with patch.object(
                sys,
                "argv",
                [
                    str(BUILD_MANIFEST),
                    "--root",
                    str(root),
                    "--out",
                    str(output),
                    "--commands-json",
                    "commands.json",
                    "--redaction-json",
                    "redaction.json",
                ],
            ):
                exit_code = module.main()

            self.assertEqual(0, exit_code)
            manifest = json.loads(output.read_text(encoding="utf-8"))
            paths = {item["path"] for item in manifest["file_allowlist"]}
            self.assertEqual({"commands.json", "public.txt", "redaction.json"}, paths)
            self.assertTrue(
                all(
                    not (
                        path == "docs/wukong/PROJECT-CONTROL.md"
                        or path.startswith("release-evidence/")
                        or Path(path).name.casefold().startswith("manifest")
                        or any(
                            part.casefold()
                            in {
                                ".pytest_cache",
                                "credentials-and-secrets",
                                "private-absolute-paths",
                                "session-history-cache-backup-artifacts",
                                "live-machine-config",
                                "private-project-outputs",
                                "manifest-self-reference",
                            }
                            for part in Path(path).parts
                        )
                        or any(part.casefold() == "__pycache__" for part in Path(path).parts)
                    )
                    for path in paths
                )
            )

    def test_manifest_metadata_uses_current_role_registry_and_scans_final_payload(self) -> None:
        module = load_module(BUILD_MANIFEST, "manifest_contract_metadata_builder")
        role_map = ROOT / "skills" / "multi-agent-wukong" / "references" / "agency-agent-role-map.json"
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            output = root / "release-evidence" / "MANIFEST.json"
            target_role_map = root / "skills" / "multi-agent-wukong" / "references" / role_map.name
            target_role_map.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(role_map, target_role_map)
            stale_commands = {
                "role_map": {
                    "agent_count": 243,
                    "role_count": 10,
                    "secondary_edge_count": 475,
                },
                "validation_failures": ["stale release evidence"],
            }
            (root / "commands.json").write_text(json.dumps(stale_commands), encoding="utf-8")
            (root / "redaction.json").write_text(
                json.dumps({"clean": True, "findings": []}), encoding="utf-8"
            )
            secret_label = "-".join(("api", "key"))
            (root / "payload.txt").write_text(
                f"{secret_label}=runtime-secret-value\n", encoding="utf-8"
            )

            with patch.object(
                sys,
                "argv",
                [
                    str(BUILD_MANIFEST),
                    "--root",
                    str(root),
                    "--out",
                    str(output),
                    "--commands-json",
                    "commands.json",
                    "--redaction-json",
                    "redaction.json",
                ],
            ):
                exit_code = module.main()

            self.assertEqual(0, exit_code)
            manifest = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(
            {
                "role_count": 11,
                "primary_role_count": 10,
                "secondary_role_count": 1,
                "secondary_edge_count": 476,
            },
            manifest["role_registry"],
        )
        self.assertNotIn("commands", manifest)
        self.assertFalse(manifest["redaction_results"]["clean"])
        self.assertEqual("payload.txt", manifest["redaction_results"]["findings"][0]["file"])


if __name__ == "__main__":
    unittest.main()

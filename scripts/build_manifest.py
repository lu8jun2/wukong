from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import shutil
import tempfile
from pathlib import Path


EXCLUDED_DIRECTORY_NAMES = frozenset(
    {
        ".git",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        ".tox",
        ".nox",
        ".cache",
        "release-evidence",
        "credentials-and-secrets",
        "private-absolute-paths",
        "session-history-cache-backup-artifacts",
        "live-machine-config",
        "private-project-outputs",
        "manifest-self-reference",
    }
)

EXCLUDED_RELATIVE_PATHS = frozenset({"docs/wukong/PROJECT-CONTROL.md"})

EXCLUSIONS = [
    ".git/",
    "__pycache__/",
    ".pytest_cache/",
    ".mypy_cache/",
    ".ruff_cache/",
    ".tox/",
    ".nox/",
    ".cache/",
    "credentials-and-secrets",
    "private-absolute-paths",
    "session-history-cache-backup-artifacts",
    "live-machine-config",
    "private-project-outputs",
    "manifest-self-reference",
    "release-evidence/",
    "docs/wukong/PROJECT-CONTROL.md",
    "MANIFEST*",
]

ROLE_MAP_RELATIVE_PATH = Path(
    "skills/multi-agent-wukong/references/agency-agent-role-map.json"
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def is_excluded(path: Path, root: Path, out: Path) -> bool:
    relative = path.relative_to(root)
    relative_path = relative.as_posix()
    if path == out or relative_path in EXCLUDED_RELATIVE_PATHS:
        return True
    if any(part.casefold() in EXCLUDED_DIRECTORY_NAMES for part in relative.parts):
        return True
    filename = path.name.casefold()
    if filename == "manifest" or filename.startswith("manifest."):
        return True
    return path.suffix.casefold() in {".pyc", ".pyo"}


def current_role_registry(root: Path) -> dict[str, int] | None:
    role_map_path = root / ROLE_MAP_RELATIVE_PATH
    if not role_map_path.is_file():
        return None
    role_map = json.loads(role_map_path.read_text(encoding="utf-8"))
    primary_roles = role_map.get("roles")
    public_registry = role_map.get("public_role_registry")
    secondary_roles = public_registry.get("roles") if isinstance(public_registry, dict) else None
    agents = role_map.get("agents")
    if not isinstance(primary_roles, dict) or not isinstance(secondary_roles, dict) or not isinstance(agents, dict):
        return None
    secondary_edge_count = sum(
        len(agent.get("secondary_roles", []))
        for agent in agents.values()
        if isinstance(agent, dict) and isinstance(agent.get("secondary_roles", []), list)
    )
    return {
        "role_count": len(primary_roles) + len(secondary_roles),
        "primary_role_count": len(primary_roles),
        "secondary_role_count": len(secondary_roles),
        "secondary_edge_count": secondary_edge_count,
    }


def scan_final_payload(root: Path, files: list[dict[str, object]]) -> dict:
    scanner_path = Path(__file__).with_name("redaction_scan.py")
    spec = importlib.util.spec_from_file_location("manifest_redaction_scan", scanner_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"missing redaction scanner: {scanner_path}")
    scanner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(scanner)
    with tempfile.TemporaryDirectory() as temp_dir:
        payload_root = Path(temp_dir)
        for item in files:
            relative = Path(str(item["path"]))
            source = root / relative
            target = payload_root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        return scanner.scan(payload_root)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--commands-json", default="release-evidence/validation-summary.json")
    parser.add_argument("--redaction-json", default="release-evidence/redaction-scan.json")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    out = Path(args.out).resolve()
    files = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if is_excluded(path, root, out):
            continue
        files.append(
            {
                "path": path.relative_to(root).as_posix(),
                "sha256": sha256(path),
                "bytes": path.stat().st_size,
            }
        )
    manifest = {
        "root": "<staging-root>",
        "file_allowlist": files,
        "exclusions": EXCLUSIONS,
        "redaction_results": scan_final_payload(root, files),
    }
    role_registry = current_role_registry(root)
    if role_registry is not None:
        manifest["role_registry"] = role_registry
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"files": len(files), "out": Path(args.out).as_posix()}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

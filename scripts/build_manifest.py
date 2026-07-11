from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


EXCLUSIONS = [
    ".git/",
    "__pycache__/",
    "credentials-and-secrets",
    "private-absolute-paths",
    "session-history-cache-backup-artifacts",
    "live-machine-config",
    "private-project-outputs",
    "manifest-self-reference",
    "release-evidence/",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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
        if any(part in {".git", "__pycache__", "release-evidence"} for part in path.parts):
            continue
        if path == out:
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
        "commands": json.loads((root / args.commands_json).read_text(encoding="utf-8")),
        "redaction_results": json.loads((root / args.redaction_json).read_text(encoding="utf-8")),
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"files": len(files), "out": Path(args.out).as_posix()}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

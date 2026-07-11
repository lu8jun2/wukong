from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def join_parts(*parts: str) -> str:
    """Build a matcher without placing the complete sensitive value in source."""
    return "".join(parts)


FORBIDDEN_LITERALS = (
    join_parts("cap", "_sid"),
    join_parts(".", "json", "l"),
    join_parts(".", "sql", "ite"),
)

SECRET_PATTERNS = {
    "bearer_token": re.compile(r"(?i)authorization\s*:\s*bearer\s+\S+"),
    "api_key": re.compile(r"(?i)\bapi[_-]?key\b\s*[:=]\s*\S+"),
    "cookie": re.compile(r"(?i)\bcookie\b\s*[:=]\s*\S+"),
    "windows_drive_path": re.compile(
        r"(?i)(?<![A-Za-z0-9_])[A-Za-z]:[\\/]"
        r"(?:[^\\/\r\n:*?\"'<>|]+[\\/])+[^\\/\r\n:*?\"'<>|]+"
    ),
    "windows_users_path": re.compile(
        r"(?i)(?<![A-Za-z0-9_])[A-Za-z]:[\\/]+Users[\\/]+"
        r"(?:[^\\/\r\n:*?\"'<>|]+[\\/])+[^\\/\r\n:*?\"'<>|]+"
    ),
    "unc_path": re.compile(
        r"(?i)(?<![:A-Za-z0-9_])[\\/]{2}"
        r"[A-Za-z0-9][^\\/\s\"'<>|]*[\\/]"
        r"[A-Za-z0-9][^\\/\s\"'<>|]*(?:[\\/][^\\/\s\"'<>|]+)+"
    ),
    "private_internal_path": re.compile(
        r"(?i)(?<![A-Za-z0-9_-])"
        r"(?:private|internal|backups?|machine[ _-]*state|plugin[ _-]*cache)"
        r"[\\/][^\\/\s\"'<>|]+(?:[\\/][^\\/\s\"'<>|]+)*"
    ),
    "private_output_path": re.compile(
        r"(?i)(?<![A-Za-z0-9_-])outputs?[\\/](?:private|internal|evidence)"
        r"[\\/][^\\/\s\"'<>|]+(?:[\\/][^\\/\s\"'<>|]+)*"
    ),
    "private_artifact_path": re.compile(
        r"(?i)(?<![A-Za-z0-9_-])(?:history|session)"
        r"[\\/][^\\/\s\"'<>|]+(?:[\\/][^\\/\s\"'<>|]+)*"
    ),
    "live_config_path": re.compile(
        r"(?i)(?<![A-Za-z0-9_.-])[A-Za-z0-9_-]+[\\/]"
        r"(?:[A-Za-z0-9_.-]+[\\/])*config[.]toml\b"
    ),
    "credential_assignment": re.compile(
        r"(?i)\b(?:auth(?:entication|orization)?|token|cookie|session)\s*[:=]\s*"
        r"(?!<[^>]+>|\[[A-Z_]+\]|\{|\[|(?:package|args|config|os|env|self)\b)"
        r"(?:[\"'][^\"']+[\"']|[A-Za-z0-9_-]{8,})"
    ),
}

TEXT_SUFFIXES = {".md", ".txt", ".json", ".toml", ".py", ".yaml", ".yml", ".gitignore"}


def scan(root: Path) -> dict:
    findings = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES and path.name != "LICENSE":
            continue
        if any(part == "__pycache__" for part in path.parts):
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        rel = path.relative_to(root).as_posix()
        for literal in FORBIDDEN_LITERALS:
            if literal in text:
                findings.append({"file": rel, "type": "forbidden_literal", "match": literal})
        for name, pattern in SECRET_PATTERNS.items():
            if pattern.search(text):
                findings.append({"file": rel, "type": name, "match": pattern.pattern})
    return {
        "root": ".",
        "rule_count": len(FORBIDDEN_LITERALS) + len(SECRET_PATTERNS),
        "findings": findings,
        "clean": not findings,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    root = Path(args.root).resolve()
    out = Path(args.out).resolve()
    result = scan(root)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"clean": result["clean"], "findings": len(result["findings"])}, ensure_ascii=False))
    return 0 if result["clean"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

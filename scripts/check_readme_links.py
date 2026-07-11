from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--readme", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    root = Path(args.root).resolve()
    readme = (root / args.readme).resolve()
    text = readme.read_text(encoding="utf-8")
    findings = []
    for target in LINK_RE.findall(text):
        if target.startswith("http://") or target.startswith("https://") or target.startswith("mailto:"):
            continue
        candidate = (readme.parent / target).resolve()
        if not candidate.exists():
            findings.append({"target": target, "status": "missing"})
    result = {"root": ".", "readme": Path(args.readme).as_posix(), "findings": findings, "clean": not findings}
    out = Path(args.out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"clean": result["clean"], "findings": len(findings)}, ensure_ascii=False))
    return 0 if result["clean"] else 1


if __name__ == "__main__":
    raise SystemExit(main())


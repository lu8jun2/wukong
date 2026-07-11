#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path

PATTERNS = [
    'docs/VERSION_*',
    'docs/*history*',
    'docs/*record*',
    'docs/*summary*',
    'docs/*??*',
    'docs/*??*',
    'releases/MANIFEST_*',
    'README.md',
]

MAX_CHARS_PER_FILE = 6000


def read_text(path: Path) -> str:
    return path.read_text(encoding='utf-8', errors='replace')[:MAX_CHARS_PER_FILE]


def main() -> int:
    parser = argparse.ArgumentParser(description='Collect a starter Codex project history markdown file.')
    parser.add_argument('project_root', nargs='?', default='.')
    parser.add_argument('--out', default='docs/CODEX_HISTORY.md')
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    out = (root / args.out).resolve() if not Path(args.out).is_absolute() else Path(args.out)

    files: list[Path] = []
    for pattern in PATTERNS:
        files.extend(sorted(root.glob(pattern)))
    seen = []
    for path in files:
        if path.is_file() and path not in seen:
            seen.append(path)

    lines = [
        '# Codex Project History',
        '',
        f'Generated: {dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
        f'Project: `{root}`',
        '',
        '## Source Artifacts',
        '',
    ]
    if not seen:
        lines.append('- No high-signal history artifacts found.')
    for path in seen:
        rel = path.relative_to(root)
        lines.append(f'- `{rel}`')

    lines.extend(['', '## Extracted Notes', ''])
    for path in seen:
        rel = path.relative_to(root)
        lines.extend([f'### `{rel}`', '', '```text'])
        lines.append(read_text(path).strip())
        lines.extend(['```', ''])

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text('\n'.join(lines), encoding='utf-8')
    print(out)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

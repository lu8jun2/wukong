#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping

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

PUBLIC_ROLE_ID = 'public-historian'
PUBLIC_ROLE_DISPLAY = 'Role=Public Historian/公共史官'
PUBLIC_ROLE_CLASS = 'secondary-only'
PUBLIC_PRIMARY_ROLE = 'guanyin'
PUBLIC_CONTROL_PATH = 'docs/wukong/PROJECT-CONTROL.md'

PUBLIC_PATTERNS = [
    'docs/VERSION_*',
    'docs/*history*',
    'docs/*record*',
    'docs/*summary*',
    PUBLIC_CONTROL_PATH,
    'releases/MANIFEST_*',
    'README.md',
]

_DRIVE_PATH_RE = re.compile(
    r'(?i)(?<![A-Za-z0-9_])[A-Za-z]:[\\/][^\\/\r\n:*?"\'<>|]+'
    r'(?:[\\/][^\\/\r\n:*?"\'<>|]+)*'
)
_UNC_PATH_RE = re.compile(
    r'(?i)(?<![A-Za-z0-9_])[\\/]{2}[^\\/\s"\'<>|]+'
    r'(?:[\\/][^\\/\s"\'<>|]+)+'
)
_POSIX_PRIVATE_PATH_RE = re.compile(
    r'(?i)(?<![A-Za-z0-9_])/(?:Users|home|mnt|private|internal)'
    r'(?:/[^\s"\'<>|]+)+'
)
_ENV_PATH_RE = re.compile(r'(?i)(?:%[A-Z_]+%|~[\\/])[^\s"\'<>|]+')
_SECRET_RE = re.compile(
    r'(?i)\b(?:api[_-]?key|access[_-]?token|refresh[_-]?token|password|passwd|secret|cookie|authorization)'
    r'\s*[:=]\s*(?:bearer\s+)?[^\s,;]+'
)
_MACHINE_RE = re.compile(
    r'(?i)\b(?:hostname|computername|machine(?:[_ -]?name)?|node(?:[_ -]?name)?)'
    r'\s*[:=]\s*[^\s,;]+'
)
_TIMESTAMP_RE = re.compile(
    r'\b(?:19|20)\d{2}-\d{2}-\d{2}(?:[T ][0-9]{2}:[0-9]{2}'
    r'(?::[0-9]{2}(?:\.[0-9]+)?)?(?:Z|[+-][0-9]{2}:?[0-9]{2})?)?\b'
)
_PRIVATE_LOG_LINE_RE = re.compile(r'(?im)^\s*(?:private|internal|debug|trace)\s+log\b.*$')
_HASH_RE = re.compile(r'^[0-9a-f]{64}$')
_REVISION_RE = re.compile(r'\bcurrent revision\s*\|\s*`(r[1-9][0-9]*)`', re.IGNORECASE)
_PRIVATE_SEGMENTS = frozenset(
    {
        'private',
        'internal',
        'logs',
        'log',
        'session',
        'cache',
        'evidence',
        'backups',
        'backup',
    }
)
_PRIVATE_SUFFIXES = frozenset({'.log', '.' + 'jsonl', '.' + 'sqlite', '.db'})
_PRIVATE_NAME_MARKERS = ('private', 'internal', 'session', 'log', 'evidence', 'cache')


def read_text(path: Path) -> str:
    return path.read_text(encoding='utf-8', errors='replace')[:MAX_CHARS_PER_FILE]


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def _public_evidence_ref(value: str) -> str:
    return f'evidence://sha256/{_sha256_text(value)}'


def sanitize_public_text(value: Any) -> str:
    """Return text safe for public history without inventing provenance."""
    text = str(value).replace('\r\n', '\n').replace('\r', '\n')
    text = _PRIVATE_LOG_LINE_RE.sub('[REDACTED_PRIVATE_LOG]', text)
    text = _SECRET_RE.sub('[REDACTED_SECRET]', text)
    text = _MACHINE_RE.sub('[REDACTED_MACHINE]', text)
    text = _DRIVE_PATH_RE.sub('[REDACTED_PATH]', text)
    text = _UNC_PATH_RE.sub('[REDACTED_PATH]', text)
    text = _POSIX_PRIVATE_PATH_RE.sub('[REDACTED_PATH]', text)
    text = _ENV_PATH_RE.sub('[REDACTED_PATH]', text)
    text = _TIMESTAMP_RE.sub('[REDACTED_TIMESTAMP]', text)
    return text


def _looks_like_absolute_path(value: str) -> bool:
    return bool(
        _DRIVE_PATH_RE.search(value)
        or _UNC_PATH_RE.search(value)
        or _POSIX_PRIVATE_PATH_RE.search(value)
        or _ENV_PATH_RE.search(value)
    )


def sanitize_public_path(value: Any) -> str:
    """Keep public relative paths; hash anything that could identify local state."""
    text = str(value).strip()
    if not text:
        return 'artifact://unnamed'
    normalized = text.replace('\\', '/')
    parts = [part for part in normalized.split('/') if part not in ('', '.')]
    lowered = {part.lower() for part in parts}
    suffix = Path(normalized).suffix.lower()
    if (
        _looks_like_absolute_path(text)
        or normalized.startswith('/')
        or '..' in parts
        or lowered & _PRIVATE_SEGMENTS
        or suffix in _PRIVATE_SUFFIXES
    ):
        return _public_evidence_ref(text)
    return '/'.join(parts) or 'artifact://unnamed'


def _sanitize_evidence_ref(value: Any) -> str:
    text = str(value).strip()
    if not text:
        return _public_evidence_ref('empty-evidence-ref')
    if _looks_like_absolute_path(text) or _SECRET_RE.search(text) or _TIMESTAMP_RE.search(text):
        return _public_evidence_ref(text)
    return sanitize_public_text(text)


def _sanitize_value(value: Any, depth: int = 0) -> Any:
    if depth > 8:
        return '[REDACTED_NESTED_DATA]'
    if isinstance(value, Mapping):
        return {str(key): _sanitize_value(item, depth + 1) for key, item in value.items()}
    if isinstance(value, list):
        return [_sanitize_value(item, depth + 1) for item in value]
    if isinstance(value, tuple):
        return [_sanitize_value(item, depth + 1) for item in value]
    if isinstance(value, str):
        return sanitize_public_text(value)
    return value


def _required_hash(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not _HASH_RE.fullmatch(value.lower()):
        raise ValueError(f'{field_name} must be a lowercase SHA-256 value')
    return value.lower()


def _public_control_context(handoff: Mapping[str, Any]) -> dict[str, Any]:
    protocol = handoff.get('protocol_context')
    if not isinstance(protocol, Mapping):
        raise ValueError('protocol_context is required for public handoff serialization')
    control = protocol.get('project_control')
    if not isinstance(control, Mapping):
        raise ValueError('protocol_context.project_control is required')
    revision = control.get('revision', handoff.get('read_revision'))
    if not isinstance(revision, str) or not re.fullmatch(r'r[1-9][0-9]*|unknown', revision):
        raise ValueError('project control revision is invalid')
    digest = control.get('sha256', handoff.get('read_sha256'))
    if digest != 'unknown':
        digest = _required_hash(digest, 'project control sha256')
    status = control.get('status', 'BLOCKED')
    if status not in {
        'VALID',
        'BLOCKED_CONTROL_DOC_MISSING',
        'BLOCKED_CONTROL_DOC_CORRUPT',
        'BLOCKED_CONTROL_DOC_CONFLICT',
        'BLOCKED',
    }:
        status = 'BLOCKED'
    return {
        'actor': 'Wukong',
        'role_display': 'Role=Wukong/悟空',
        'project_control': {
            'path': PUBLIC_CONTROL_PATH,
            'schema': 'project-control/v1',
            'revision': revision,
            'sha256': digest,
            'status': status,
        },
    }


def _public_attribution(handoff: Mapping[str, Any]) -> list[dict[str, Any]]:
    attribution = handoff.get('attribution')
    paragraph_ids = handoff.get('visible_paragraph_ids')
    count = handoff.get('visible_paragraph_count')
    if not isinstance(attribution, list) or not isinstance(paragraph_ids, list) or not isinstance(count, int):
        raise ValueError('visible paragraph attribution fields are required')
    if count != len(paragraph_ids) or count != len(attribution):
        raise ValueError('visible paragraph attribution count mismatch')
    result: list[dict[str, Any]] = []
    for index, item in enumerate(attribution):
        if not isinstance(item, Mapping):
            raise ValueError('attribution entries must be objects')
        paragraph_id = sanitize_public_text(item.get('paragraph_id', paragraph_ids[index]))
        if paragraph_id != sanitize_public_text(paragraph_ids[index]):
            raise ValueError('visible paragraph attribution id mismatch')
        refs = item.get('evidence_refs')
        if not isinstance(refs, list) or not refs:
            raise ValueError('attribution evidence_refs are required')
        contribution = sanitize_public_text(item.get('contribution', ''))
        text_hash = item.get('text_sha256')
        if not isinstance(text_hash, str) or not _HASH_RE.fullmatch(text_hash.lower()):
            text_hash = _sha256_text(contribution)
        result.append(
            {
                'paragraph_id': paragraph_id,
                'role_id': PUBLIC_ROLE_ID,
                'role_display': PUBLIC_ROLE_DISPLAY,
                'primary_role': sanitize_public_text(item.get('primary_role', PUBLIC_PRIMARY_ROLE)),
                'secondary_roles': [PUBLIC_ROLE_ID],
                'contribution': contribution,
                'evidence_refs': [_sanitize_evidence_ref(ref) for ref in refs],
                'text_sha256': text_hash.lower(),
            }
        )
    return result


def _public_bug_logs(handoff: Mapping[str, Any]) -> list[dict[str, Any]]:
    raw_logs = handoff.get('bugs_logs', [])
    if not isinstance(raw_logs, list):
        raise ValueError('bugs_logs must be a list')
    result: list[dict[str, Any]] = []
    for item in raw_logs:
        if not isinstance(item, Mapping):
            raise ValueError('bug log entries must be objects')
        artifact = item.get('raw_artifact_path', 'unidentified-artifact')
        artifact_hash = item.get('raw_artifact_sha256')
        if not isinstance(artifact_hash, str) or not _HASH_RE.fullmatch(artifact_hash.lower()):
            artifact_hash = _sha256_text(str(artifact))
        result.append(
            {
                'time': '[REDACTED_TIMESTAMP]',
                'command': sanitize_public_text(item.get('command', 'redacted command')),
                'exit_code': int(item.get('exit_code', 1)),
                'key_raw_excerpt': sanitize_public_text(item.get('key_raw_excerpt', '')),
                'raw_artifact_path': _sanitize_evidence_ref(artifact),
                'raw_artifact_sha256': artifact_hash.lower(),
                'redaction_applied': True,
                'root_cause': sanitize_public_text(item.get('root_cause', '')),
                'disposition': sanitize_public_text(item.get('disposition', '')),
            }
        )
    return result


def serialize_public_handoff(handoff: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize a worker handoff to a schema-shaped, public-safe historian record."""
    if not isinstance(handoff, Mapping):
        raise TypeError('handoff must be a mapping')
    status = handoff.get('status', 'DONE_WITH_RISKS')
    if status not in {'DONE', 'DONE_WITH_RISKS', 'BLOCKED', 'NEEDS_CONTEXT'}:
        raise ValueError('handoff status is invalid')
    attribution = _public_attribution(handoff)
    primary_role = sanitize_public_text(handoff.get('primary_role', PUBLIC_PRIMARY_ROLE))
    if not primary_role or primary_role == PUBLIC_ROLE_ID:
        raise ValueError('public historian cannot be a primary role')
    control_context = _public_control_context(handoff)
    read_revision = handoff.get('read_revision', control_context['project_control']['revision'])
    if not isinstance(read_revision, str) or not re.fullmatch(r'r[1-9][0-9]*', read_revision):
        raise ValueError('read_revision must be an explicit revision')
    read_sha256 = _required_hash(handoff.get('read_sha256'), 'read_sha256')
    compliance = sanitize_public_text(handoff.get('hard_constraints_compliance', ''))
    compliance = (
        f'{compliance} Public Historian is secondary-only; Delegation permission: FORBIDDEN; '
        'does not coordinate, does not recurse, does not verify, and does not approve.'
    ).strip()
    paragraph_ids = [item['paragraph_id'] for item in attribution]
    return {
        'status': status,
        'task_id': sanitize_public_text(handoff.get('task_id', 'public-history-record')),
        'role': PUBLIC_ROLE_ID,
        'role_class': PUBLIC_ROLE_CLASS,
        'primary_role': primary_role,
        'secondary_roles': [PUBLIC_ROLE_ID],
        'role_display': PUBLIC_ROLE_DISPLAY,
        'protocol_context': control_context,
        'control_document_path': PUBLIC_CONTROL_PATH,
        'read_revision': read_revision,
        'read_sha256': read_sha256,
        'related_sections': [sanitize_public_text(item) for item in handoff.get('related_sections', [])],
        'modified_files': [sanitize_public_path(item) for item in handoff.get('modified_files', [])],
        'tdd_status': handoff.get('tdd_status', 'NOT_STARTED'),
        'tdd_evidence': _sanitize_value(handoff.get('tdd_evidence', {})),
        'test_command': sanitize_public_text(handoff.get('test_command', 'not run')),
        'test_result': _sanitize_value(handoff.get('test_result', {})),
        'visible_paragraph_count': len(attribution),
        'visible_paragraph_ids': paragraph_ids,
        'attribution': attribution,
        'issues': _sanitize_value(handoff.get('issues', [])),
        'bugs_logs': _public_bug_logs(handoff),
        'hard_constraints_compliance': compliance,
        'conclusion': sanitize_public_text(handoff.get('conclusion', 'Recorded for independent review.')),
        'next_step': sanitize_public_text(handoff.get('next_step', 'Independent verification remains required.')),
        'historian_proposal': sanitize_public_text(handoff.get('historian_proposal', 'Retain the sanitized record.')),
        'external_skill_agent_evaluation': _sanitize_value(handoff.get('external_skill_agent_evaluation', {})),
    }


def _public_source_files(root: Path, output_path: Path | None = None) -> list[Path]:
    files: list[Path] = []
    for pattern in PUBLIC_PATTERNS:
        files.extend(sorted(root.glob(pattern)))
    seen: list[Path] = []
    output = output_path.resolve() if output_path else None
    for path in files:
        resolved = path.resolve()
        if not path.is_file() or resolved in seen or (output and resolved == output):
            continue
        relative = path.relative_to(root)
        parts = {part.lower() for part in relative.parts}
        name = path.name.lower()
        if (
            parts & _PRIVATE_SEGMENTS
            or path.suffix.lower() in _PRIVATE_SUFFIXES
            or any(marker in name for marker in _PRIVATE_NAME_MARKERS)
        ):
            continue
        seen.append(resolved)
    return [Path(path) for path in seen]


def _control_snapshot(root: Path) -> tuple[str, str, str]:
    control = root / PUBLIC_CONTROL_PATH
    if not control.is_file():
        return 'r1', '0' * 64, 'BLOCKED_CONTROL_DOC_MISSING'
    content = read_text(control)
    match = _REVISION_RE.search(content)
    revision = match.group(1) if match else 'r1'
    return revision, hashlib.sha256(control.read_bytes()).hexdigest(), 'BLOCKED'


def _default_public_handoff(root: Path, source_files: list[Path]) -> dict[str, Any]:
    revision, digest, control_status = _control_snapshot(root)
    refs = [sanitize_public_path(path.relative_to(root).as_posix()) for path in source_files]
    if not refs:
        refs = [_public_evidence_ref('no-public-artifacts')]
    contribution = 'Collected public-safe project history artifacts for independent review.'
    return {
        'status': 'DONE_WITH_RISKS',
        'task_id': 'public-history-collection',
        'primary_role': PUBLIC_PRIMARY_ROLE,
        'protocol_context': {
            'project_control': {
                'revision': revision,
                'sha256': digest,
                'status': control_status,
            }
        },
        'read_revision': revision,
        'read_sha256': digest,
        'related_sections': ['Project Structure', 'Verification Evidence'],
        'modified_files': [],
        'tdd_status': 'NOT_STARTED',
        'tdd_evidence': {'status': 'not applicable to collection'},
        'test_command': 'not run',
        'test_result': {'status': 'not run'},
        'visible_paragraph_count': 1,
        'visible_paragraph_ids': ['history-summary'],
        'attribution': [
            {
                'paragraph_id': 'history-summary',
                'primary_role': PUBLIC_PRIMARY_ROLE,
                'contribution': contribution,
                'evidence_refs': refs,
                'text_sha256': _sha256_text(contribution),
            }
        ],
        'issues': [],
        'bugs_logs': [],
        'hard_constraints_compliance': 'Collection is record-only.',
        'conclusion': 'Public-safe history was collected without release approval.',
        'next_step': 'Independent verification remains required.',
        'historian_proposal': 'Retain the sanitized record and evidence references.',
        'external_skill_agent_evaluation': {'network_use': {'used': False}},
    }


def render_public_history(
    project_root: Path | str,
    *,
    handoff: Mapping[str, Any] | None = None,
    output_path: Path | str | None = None,
) -> str:
    """Render a public-safe Markdown history without exposing local project identity."""
    root = Path(project_root).resolve()
    output = Path(output_path).resolve() if output_path else None
    source_files = _public_source_files(root, output)
    record = serialize_public_handoff(handoff or _default_public_handoff(root, source_files))
    lines = [
        '# Codex Project History',
        '',
        f'**{PUBLIC_ROLE_DISPLAY}** This is a public-safe, record-only history artifact.',
        '',
        '## Public Role Boundary',
        '',
        f'**{PUBLIC_ROLE_DISPLAY}** The role is `secondary-only`; Delegation permission: `FORBIDDEN`.',
        f'**{PUBLIC_ROLE_DISPLAY}** It does not coordinate users, recurse into other agents, verify releases, or approve final authority.',
        '',
        '## Protocol Attribution',
        '',
        f'**{PUBLIC_ROLE_DISPLAY}** The machine-readable record preserves protocol attribution and evidence references.',
        '',
        '```json',
        json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True),
        '```',
        '',
        '## Source Artifacts',
        '',
    ]
    if not source_files:
        lines.append(f'**{PUBLIC_ROLE_DISPLAY}** No public source artifacts were selected.')
    for path in source_files:
        relative = sanitize_public_path(path.relative_to(root).as_posix())
        lines.append(f'**{PUBLIC_ROLE_DISPLAY}** - `{relative}`')
    lines.extend(['', '## Extracted Notes', ''])
    if not source_files:
        lines.append(f'**{PUBLIC_ROLE_DISPLAY}** No notes were extracted.')
    for path in source_files:
        relative = sanitize_public_path(path.relative_to(root).as_posix())
        lines.extend([f'**{PUBLIC_ROLE_DISPLAY}** Source `{relative}`:', ''])
        content = sanitize_public_text(read_text(path).strip())
        if not content:
            lines.append(f'**{PUBLIC_ROLE_DISPLAY}** > [empty]')
        else:
            lines.extend(f'**{PUBLIC_ROLE_DISPLAY}** > {line}' for line in content.splitlines())
        lines.append('')
    return '\n'.join(lines).rstrip() + '\n'


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Collect a starter Codex project history markdown file.')
    parser.add_argument('project_root', nargs='?', default='.')
    parser.add_argument('--out', default='docs/CODEX_HISTORY.md')
    parser.add_argument('--public', action='store_true', help='write a public-safe history artifact')
    parser.add_argument('--handoff', help='read a JSON worker handoff for public serialization')
    args = parser.parse_args(argv)

    root = Path(args.project_root).resolve()
    out = (root / args.out).resolve() if not Path(args.out).is_absolute() else Path(args.out)

    if args.public:
        handoff = None
        if args.handoff:
            handoff = json.loads(Path(args.handoff).read_text(encoding='utf-8'))
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(render_public_history(root, handoff=handoff, output_path=out), encoding='utf-8', newline='\n')
        try:
            shown = out.relative_to(root).as_posix()
        except ValueError:
            shown = 'public-history-output'
        print(shown)
        return 0

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

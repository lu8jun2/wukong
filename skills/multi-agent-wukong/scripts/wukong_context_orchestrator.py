"""C-lite context stack for Multi Agent Wukong.

This module is intentionally dependency-free. It models the adapter boundary
before wiring real LangGraph, mem0, or Graphiti backends:

- StateStore: current task state, LangGraph-like.
- MemoryStore: long-term durable memories, mem0-like.
- FactGraphStore: temporal shared facts, Graphiti-like.
- WritebackGuard: approval and evidence checks before persistence.
- ContextBuilder: compact context packet assembly for delegated roles.
"""

from __future__ import annotations

import argparse
import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


WUKONG_ACTORS = {"悟空", "Wukong", "wukong"}
LINE_RECORD_SUFFIX = "." + "json" + "l"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_root(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    return root


def _read_json(path: Path, default: dict[str, Any]) -> dict[str, Any]:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def _line_record_path(root: Path, stem: str) -> Path:
    return root / (stem + LINE_RECORD_SUFFIX)


def _append_jsonl(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(data, ensure_ascii=False, sort_keys=True) + "\n")


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def _matches(record: dict[str, Any], query: str) -> bool:
    if not query:
        return True
    needle = query.casefold()
    return needle in json.dumps(record, ensure_ascii=False).casefold()


class WritebackGuard:
    """Centralized write policy for Wukong context persistence."""

    def validate_memory_write(
        self,
        *,
        actor: str,
        text: str,
        evidence: str,
        approved: bool,
    ) -> None:
        if actor not in WUKONG_ACTORS or not approved:
            raise PermissionError("Only Wukong-approved memories may be persisted.")
        if not text.strip():
            raise ValueError("Memory text is required.")
        if not evidence.strip():
            raise ValueError("Memory evidence is required.")

    def validate_fact_write(
        self,
        *,
        actor: str,
        subject: str,
        predicate: str,
        object_: str,
        evidence: str,
        confidence: float,
    ) -> None:
        if actor not in WUKONG_ACTORS:
            raise PermissionError("Only Wukong may persist shared facts.")
        if not subject.strip() or not predicate.strip() or not object_.strip():
            raise ValueError("Fact subject, predicate, and object are required.")
        if not evidence.strip():
            raise ValueError("Shared facts require evidence or provenance.")
        if confidence < 0 or confidence > 1:
            raise ValueError("Fact confidence must be between 0 and 1.")


@dataclass
class StateStore:
    """JSON-backed current task state store."""

    root: Path

    def __post_init__(self) -> None:
        self.root = _ensure_root(Path(self.root))
        self.path = self.root / "state.json"

    def load(self) -> dict[str, Any]:
        return _read_json(self.path, {"version": 1, "updated_at": None, "tasks": {}})

    def save(self, state: dict[str, Any]) -> None:
        state["updated_at"] = utc_now()
        _write_json(self.path, state)

    def upsert_task(
        self,
        *,
        task_id: str,
        role: str,
        mission: str,
        status: str,
        dependencies: list[str] | None = None,
        write_scope: list[str] | None = None,
        validation: str = "",
    ) -> dict[str, Any]:
        if not task_id.strip():
            raise ValueError("task_id is required.")
        state = self.load()
        task = {
            "id": task_id,
            "role": role,
            "mission": mission,
            "status": status,
            "dependencies": dependencies or [],
            "write_scope": write_scope or [],
            "validation": validation,
            "updated_at": utc_now(),
        }
        state.setdefault("tasks", {})[task_id] = task
        self.save(state)
        return task

    def get_task(self, task_id: str) -> dict[str, Any] | None:
        return self.load().get("tasks", {}).get(task_id)

    def list_tasks(self) -> list[dict[str, Any]]:
        tasks = self.load().get("tasks", {})
        return [tasks[key] for key in sorted(tasks)]


@dataclass
class MemoryStore:
    """Line-delimited JSON long-term memory store."""

    root: Path
    guard: WritebackGuard | None = None

    def __post_init__(self) -> None:
        self.root = _ensure_root(Path(self.root))
        self.path = _line_record_path(self.root, "memory")
        self.guard = self.guard or WritebackGuard()

    def add(self, *, scope: str, text: str, actor: str, evidence: str) -> dict[str, Any]:
        self.guard.validate_memory_write(
            actor=actor,
            text=text,
            evidence=evidence,
            approved=True,
        )
        record = {
            "id": str(uuid.uuid4()),
            "created_at": utc_now(),
            "scope": scope,
            "text": text,
            "actor": actor,
            "evidence": evidence,
        }
        _append_jsonl(self.path, record)
        return record

    def search(self, query: str, *, limit: int = 5) -> list[dict[str, Any]]:
        records = _read_jsonl(self.path)
        matches = [r for r in records if _matches(r, query)]
        return (matches or records[-limit:])[:limit]


@dataclass
class FactGraphStore:
    """Line-delimited JSON temporal fact graph store."""

    root: Path
    guard: WritebackGuard | None = None

    def __post_init__(self) -> None:
        self.root = _ensure_root(Path(self.root))
        self.path = _line_record_path(self.root, "facts")
        self.guard = self.guard or WritebackGuard()

    def add(
        self,
        *,
        subject: str,
        predicate: str,
        object_: str,
        actor: str,
        evidence: str,
        confidence: float,
        valid_from: str | None = None,
        valid_to: str | None = None,
    ) -> dict[str, Any]:
        self.guard.validate_fact_write(
            actor=actor,
            subject=subject,
            predicate=predicate,
            object_=object_,
            evidence=evidence,
            confidence=confidence,
        )
        record = {
            "id": str(uuid.uuid4()),
            "created_at": utc_now(),
            "subject": subject,
            "predicate": predicate,
            "object": object_,
            "actor": actor,
            "evidence": evidence,
            "confidence": confidence,
            "valid_from": valid_from or utc_now(),
            "valid_to": valid_to,
        }
        _append_jsonl(self.path, record)
        return record

    def search(self, query: str, *, limit: int = 5) -> list[dict[str, Any]]:
        records = _read_jsonl(self.path)
        matches = [r for r in records if _matches(r, query)]
        return (matches or records[-limit:])[:limit]


class ContextBuilder:
    """Assemble bounded role context packets from state, memory, and facts."""

    def __init__(
        self,
        state: StateStore,
        memory: MemoryStore,
        facts: FactGraphStore,
    ) -> None:
        self.state = state
        self.memory = memory
        self.facts = facts

    def build_packet(
        self,
        *,
        task_id: str,
        role: str,
        query: str,
        max_items_per_store: int = 5,
    ) -> dict[str, Any]:
        task = self.state.get_task(task_id) or {
            "id": task_id,
            "role": role,
            "mission": "",
            "status": "unknown",
            "dependencies": [],
            "write_scope": [],
            "validation": "",
        }
        return {
            "generated_at": utc_now(),
            "role": role,
            "query": query,
            "task": task,
            "dependencies": task.get("dependencies", []),
            "write_scope": task.get("write_scope", []),
            "validation": task.get("validation", ""),
            "memories": self.memory.search(query, limit=max_items_per_store),
            "facts": self.facts.search(query, limit=max_items_per_store),
            "writeback_policy": {
                "state": "Wukong updates task state after role reports.",
                "memory": "Only Wukong-approved, evidence-backed durable lessons are saved.",
                "facts": "Only evidence-backed shared facts with confidence are saved.",
            },
        }


def _build_stores(root: Path) -> tuple[StateStore, MemoryStore, FactGraphStore]:
    guard = WritebackGuard()
    return StateStore(root), MemoryStore(root, guard), FactGraphStore(root, guard)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Wukong C-lite context stack")
    parser.add_argument("--root", default=".wukong-context", help="context data root")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init", help="create context store files")

    task = sub.add_parser("task", help="upsert task state")
    task.add_argument("--id", required=True)
    task.add_argument("--role", required=True)
    task.add_argument("--mission", required=True)
    task.add_argument("--status", required=True)
    task.add_argument("--dependency", action="append", default=[])
    task.add_argument("--write-scope", action="append", default=[])
    task.add_argument("--validation", default="")

    memory = sub.add_parser("memory", help="add long-term memory")
    memory.add_argument("--scope", required=True)
    memory.add_argument("--text", required=True)
    memory.add_argument("--actor", default="悟空")
    memory.add_argument("--evidence", required=True)

    fact = sub.add_parser("fact", help="add shared fact")
    fact.add_argument("--subject", required=True)
    fact.add_argument("--predicate", required=True)
    fact.add_argument("--object", required=True)
    fact.add_argument("--actor", default="悟空")
    fact.add_argument("--evidence", required=True)
    fact.add_argument("--confidence", type=float, default=0.8)

    packet = sub.add_parser("packet", help="assemble context packet")
    packet.add_argument("--task-id", required=True)
    packet.add_argument("--role", required=True)
    packet.add_argument("--query", required=True)
    packet.add_argument("--limit", type=int, default=5)

    args = parser.parse_args(argv)
    root = Path(args.root)
    state, memory_store, fact_store = _build_stores(root)

    if args.command == "init":
        state.save(state.load())
        memory_store.path.touch(exist_ok=True)
        fact_store.path.touch(exist_ok=True)
        result: dict[str, Any] = {"root": str(root), "status": "ready"}
    elif args.command == "task":
        result = state.upsert_task(
            task_id=args.id,
            role=args.role,
            mission=args.mission,
            status=args.status,
            dependencies=args.dependency,
            write_scope=args.write_scope,
            validation=args.validation,
        )
    elif args.command == "memory":
        result = memory_store.add(
            scope=args.scope,
            text=args.text,
            actor=args.actor,
            evidence=args.evidence,
        )
    elif args.command == "fact":
        result = fact_store.add(
            subject=args.subject,
            predicate=args.predicate,
            object_=args.object,
            actor=args.actor,
            evidence=args.evidence,
            confidence=args.confidence,
        )
    elif args.command == "packet":
        result = ContextBuilder(state, memory_store, fact_store).build_packet(
            task_id=args.task_id,
            role=args.role,
            query=args.query,
            max_items_per_store=args.limit,
        )
    else:
        parser.error(f"Unknown command: {args.command}")

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

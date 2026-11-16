"""Per-project memory with atomic append-only records and compact orientation."""
from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from .contracts import CheckResult, Decision, EvidenceCard
from .permissions import inside


def _json(obj: object) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2, default=str)


def _atomic_write(path: Path, data: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                     delete=False) as fh:
        fh.write(data)
        temp = Path(fh.name)
    os.replace(temp, path)


def new_project(workspace: Path, name: str, goal: str) -> Path:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", name):
        raise ValueError("Project name must contain only letters, numbers, - and _")
    if not goal.strip():
        raise ValueError("Objective cannot be empty")
    root = Path(workspace).resolve()
    root.mkdir(parents=True, exist_ok=True)
    project = root / name
    if project.exists():
        raise FileExistsError(f"Project already exists: {project}")
    project.mkdir()
    for subdir in ("source", "literature", "decisions", "graphs", "experiments",
                   "certificates", "reports", "logs", "evidence", "artifacts"):
        (project / subdir).mkdir()
    _atomic_write(project / "OBJECTIVE.md", f"# Objective\n\n{goal.strip()}\n")
    _atomic_write(project / "MEMORY_CORE.md", f"# Current state\n\nObjective: {goal.strip()}\nStatus: INTAKE\n")
    _atomic_write(project / "INDEX.json", _json({"version": 1, "evidence": [], "decisions": [],
                                                 "checks": [], "certificates": []}))
    _atomic_write(project / "graphs" / "decision_graph.json",
                  _json({"nodes": [], "edges": []}))
    return project


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for data in iter(lambda: f.read(1024 * 1024), b""):
            h.update(data)
    return h.hexdigest()


def record(project: Path, category: str, identifier: str,
           value: EvidenceCard | Decision | CheckResult) -> Path:
    categories = {"evidence": EvidenceCard, "decisions": Decision, "checks": CheckResult}
    if category not in categories or not isinstance(value, categories[category]):
        raise ValueError("Invalid record type/category")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,100}", identifier):
        raise ValueError("Invalid record ID")
    root = Path(project).resolve(strict=True)
    folder = "reports" if category == "checks" else category
    target = inside(root, f"{folder}/{identifier}.json")
    if target.exists():
        raise FileExistsError("Records are immutable; use a new ID")
    _atomic_write(target, _json(asdict(value)))
    index_path = inside(root, "INDEX.json")
    index = json.loads(index_path.read_text(encoding="utf-8"))
    index[category].append({"id": identifier, "path": str(target.relative_to(root)),
                            "sha256": sha256_file(target),
                            "timestamp": datetime.now(timezone.utc).isoformat()})
    _atomic_write(index_path, _json(index))
    return target


def compact_orientation(project: Path, *, objective: str, state: str,
                        blockers: tuple[str, ...], next_step: str) -> None:
    """Stores a small canonical view; full evidence stays in immutable records."""
    lines = ["# Current state", f"Objective: {objective}", f"Status: {state}",
             "Blockers:", *(f"- {x}" for x in blockers), f"Next step: {next_step}"]
    _atomic_write(inside(project, "MEMORY_CORE.md"), "\n".join(lines) + "\n")

"""Version-aware handoff to existing scientific RAG skill; no fake invocation."""
from __future__ import annotations

import json
import re
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path

from .contracts import CasePacket

REPO_URL = "https://github.com/Josch01/skill-investigacion-cientifica-rag"
PINNED_COMMIT = "cc3388d4eca22de293763e6426746e5b6f85c2ea"
EXPECTED_VERSION = "3.1.0"


@dataclass(frozen=True)
class BridgeCheck:
    status: str
    version: str | None
    commit: str | None
    reason: str


def inspect_skill(path: Path, *, expected_version: str = EXPECTED_VERSION,
                  expected_commit: str = PINNED_COMMIT) -> BridgeCheck:
    root = Path(path).resolve()
    skill = root / "SKILL.md"
    if not skill.is_file():
        return BridgeCheck("BLOCKED", None, None, "Local SKILL.md unavailable")
    content = skill.read_text(encoding="utf-8")
    match = re.search(r"(?m)^\s*version:\s*['\"]?([^'\"\s]+)", content)
    version = match.group(1) if match else None
    try:
        proc = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"],
                              capture_output=True, text=True, timeout=5, check=False)
        commit = proc.stdout.strip() if proc.returncode == 0 else None
    except (FileNotFoundError, subprocess.TimeoutExpired):
        commit = None
    if version != expected_version or commit != expected_commit:
        return BridgeCheck(
            "BLOCKED", version, commit,
            "Skill version/commit differs from pin; audit and update pin before use",
        )
    return BridgeCheck("READY", version, commit, "Version and source commit verified")


def handoff(packet: CasePacket, local_skill: Path) -> dict:
    check = inspect_skill(local_skill)
    if check.status != "READY":
        return {"status": "BLOCKED", "bridge": asdict(check)}
    return {
        "status": "HANDOFF_READY",
        "bridge": asdict(check),
        "case_packet": asdict(packet),
        "instructions": [
            "Invoke the selected scientific skill in a compatible agent runtime.",
            "Apply its INTERPRETER and dynamic ROUTER; retain source provenance.",
            "Return an evidence/certification artifact with exact scope and assumptions.",
            "An exported handoff is NOT proof that the external skill was executed.",
        ],
    }

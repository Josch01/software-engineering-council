"""Durable conversational project state; records decisions, not full chat transcripts.

The host AI conducts the conversation. This module is a small audit trail, not an
LLM runtime and not evidence that specialist reasoning or tests happened.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from .memory import _atomic_write, sha256_file
from .budgets import ResourceBudget
from .permissions import inside

EVENTS = frozenset({
    "FINDING", "PROPOSAL", "QUESTION", "USER_OBJECTIVE", "USER_APPROVAL",
    "USER_REJECTION", "PLAN", "IMPLEMENTED", "TEST_RESULT", "ADVERSARIAL_AUDIT",
    "BLOCKER", "CLOSED",
})
WRITABLE_EVENTS = {"PLAN", "IMPLEMENTED"}
ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,90}")


def _project(project: Path) -> Path:
    root = Path(project).resolve(strict=True)
    if not root.is_dir() or not (root / "OBJECTIVE.md").is_file():
        raise ValueError("Expected an initialized council project")
    return root


def _state_path(root: Path) -> Path:
    return inside(root, "CONVERSATION_STATE.json")


def _load(root: Path) -> dict:
    path = _state_path(root)
    if not path.is_file():
        raise FileNotFoundError("Conversation not started")
    value = json.loads(path.read_text(encoding="utf-8"))
    if value.get("schema") != "sec.conversation/1":
        raise ValueError("Unsupported conversation state schema")
    return value


def start_conversation(project: Path, source: Path, initial_request: str) -> dict:
    """Start with source understanding; no assumed optimization or permission to edit."""
    root = _project(project)
    target = Path(source).resolve(strict=True)
    if not target.is_file() or target.suffix != ".py":
        raise ValueError("Expected an existing .py file")
    if target.stat().st_size > ResourceBudget().max_file_bytes:
        raise ValueError("Source exceeds bounded intake size; narrow the scope")
    if not initial_request.strip() or len(initial_request) > 12_000:
        raise ValueError("An initial user request is required")
    path = _state_path(root)
    if path.exists():
        raise FileExistsError("Conversation already exists; resume it without resetting")
    state = {
        "schema": "sec.conversation/1",
        "status": "IN_DISCUSSION",
        "phase": "UNDERSTAND_SOURCE",
        "original_user_request": initial_request,
        "objective": None,
        "source": {"path": str(target), "sha256_at_start": sha256_file(target)},
        "source_edit_authorized": False,
        "proposals": {},
        "approved_proposals": [],
        "open_questions": [],
        "key_findings": [],
        "events": [],
        "next_event_number": 1,
        "scientific_certification": "NOT_PERFORMED",
        "technical_acceptance": "NOT_PERFORMED",
    }
    _atomic_write(path, json.dumps(state, indent=2, ensure_ascii=False))
    return summary(state)


def summary(state: dict) -> dict:
    return {
        "status": state["status"], "phase": state["phase"],
        "source": state["source"]["path"],
        "objective": state["objective"], "proposals": state["proposals"],
        "approved_proposals": state["approved_proposals"],
        "open_questions": state["open_questions"],
        "key_findings": state["key_findings"],
        "events_recorded": len(state["events"]),
        "source_edit_authorized": state["source_edit_authorized"],
        "scientific_certification": state["scientific_certification"],
        "technical_acceptance": state["technical_acceptance"],
    }


def resume_conversation(project: Path) -> dict:
    return summary(_load(_project(project)))


def add_event(
    project: Path, *, kind: str, detail: str, actor: str = "agent",
    proposal_id: str | None = None, evidence_refs: tuple[str, ...] = (),
    user_confirmed: bool = False,
) -> dict:
    """Record compact durable facts. Never treat a model's claims as run results."""
    root = _project(project)
    state = _load(root)
    if state["status"] == "CLOSED":
        raise PermissionError("Cannot change a closed conversation")
    if kind not in EVENTS:
        raise ValueError("Unsupported event type")
    if not detail.strip() or len(detail) > 3000:
        raise ValueError("Event detail required (max 3000 characters)")
    if actor not in {"agent", "user", "checker", "reviewer"}:
        raise ValueError("Unsupported actor")
    if proposal_id and not ID.fullmatch(proposal_id):
        raise ValueError("Invalid proposal id")
    if kind in {"USER_OBJECTIVE", "USER_APPROVAL", "USER_REJECTION"}:
        if actor != "user" or not user_confirmed:
            raise PermissionError("Explicitly confirmed user decisions only")
    if kind == "PROPOSAL":
        if not proposal_id or proposal_id in state["proposals"]:
            raise ValueError("New proposal needs a unique ID")
        state["proposals"][proposal_id] = {"summary": detail, "state": "PROPOSED"}
        state["phase"] = "DISCUSS_OPTIONS"
    elif kind in {"USER_APPROVAL", "USER_REJECTION"}:
        if not proposal_id or proposal_id not in state["proposals"]:
            raise ValueError("Decision must reference an existing proposal")
        current = state["proposals"][proposal_id]["state"]
        if current != "PROPOSED":
            raise ValueError("This proposal has already been decided")
        chosen = "APPROVED" if kind == "USER_APPROVAL" else "REJECTED"
        state["proposals"][proposal_id]["state"] = chosen
        if chosen == "APPROVED":
            state["approved_proposals"].append(proposal_id)
            state["source_edit_authorized"] = True
            state["phase"] = "PLAN"
    elif kind == "USER_OBJECTIVE":
        if state["objective"] != detail:
            for old_id in state["approved_proposals"]:
                state["proposals"][old_id]["state"] = "NEEDS_RECONFIRMATION"
            state["approved_proposals"] = []
            state["source_edit_authorized"] = False
        state["objective"] = detail
        state["phase"] = "GOAL_DEFINED"
    elif kind == "FINDING":
        state["key_findings"].append({
            "detail": detail, "evidence_refs": list(evidence_refs),
            "verification": "USER_OR_AGENT_REPORTED_NOT_CERTIFIED",
        })
        state["phase"] = "DIAGNOSE"
    elif kind == "QUESTION":
        state["open_questions"].append(detail)
    elif kind == "PLAN":
        if not state["objective"] and not state["approved_proposals"]:
            raise PermissionError("No agreed objective or approved proposal to plan")
        state["phase"] = "PLAN"
    elif kind == "IMPLEMENTED":
        if not state["source_edit_authorized"] or not state["approved_proposals"]:
            raise PermissionError("Source changes require an approved proposal")
        state["phase"] = "IMPLEMENTED_PENDING_TESTS"
        state["technical_acceptance"] = "NOT_PERFORMED"
    elif kind == "TEST_RESULT":
        if actor != "checker":
            raise PermissionError("Only deterministic checkers may record test results")
        state["phase"] = "AWAITING_REVIEW"
    elif kind == "ADVERSARIAL_AUDIT":
        if actor != "reviewer":
            raise PermissionError("Audits must declare reviewer role")
        state["phase"] = "AUDIT_RECORDED"
    elif kind == "BLOCKER":
        state["phase"] = "BLOCKED"
    elif kind == "CLOSED":
        if not user_confirmed or actor != "user":
            raise PermissionError("Closing a conversational project needs user confirmation")
        state["status"] = "CLOSED"
        state["phase"] = "CLOSED"

    event = {
        "number": state["next_event_number"],
        "kind": kind, "detail": detail, "actor": actor,
        "proposal_id": proposal_id, "evidence_refs": list(evidence_refs),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }
    state["events"].append(event)
    state["next_event_number"] += 1
    _atomic_write(_state_path(root), json.dumps(state, indent=2, ensure_ascii=False))
    return summary(state)

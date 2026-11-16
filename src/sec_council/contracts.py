"""Typed contracts. A model's statement is never an executed test result."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class TaskKind(str, Enum):
    CODE_AUDIT = "CODE_AUDIT"
    OPTIMIZATION = "OPTIMIZATION"
    DATA_SCIENCE = "DATA_SCIENCE"
    LITERATURE = "LITERATURE"
    THEORY = "THEORY"
    IMPLEMENTATION = "IMPLEMENTATION"
    GENERAL = "GENERAL"


class GateStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"
    INCONCLUSIVE = "INCONCLUSIVE"
    NOT_RUN = "NOT_RUN"


class EpistemicType(str, Enum):
    LITERATURE = "L"
    DEDUCTION = "D"
    CONJECTURE = "C"
    NUMERICAL = "N"
    HYPOTHESIS = "H"
    REFUTATION = "X"
    UNVERIFIED = "U"
    DECISION = "DEC"


@dataclass(frozen=True)
class TaskRequest:
    goal: str
    source_paths: tuple[str, ...] = ()
    user_constraints: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.goal.strip():
            raise ValueError("The objective cannot be empty")


@dataclass(frozen=True)
class Route:
    kind: TaskKind
    lead: str
    reviewer: str | None
    workers: tuple[str, ...]
    scientific_escalation: bool
    needs_clarification: bool
    clarification_question: str | None
    rationale: str

    @property
    def all_agents(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys((self.lead, *(self.workers), *((self.reviewer,) if self.reviewer else ()))))


@dataclass(frozen=True)
class CheckResult:
    check_id: str
    status: GateStatus
    detail: str
    evidence_paths: tuple[str, ...] = ()
    produced_by: str = "deterministic-checker"
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class EvidenceCard:
    evidence_id: str
    title: str
    source_url: str
    locator: str
    claim: str
    assumptions: tuple[str, ...]
    epistemic_type: EpistemicType
    verified: bool = False
    sha256: str | None = None

    def __post_init__(self) -> None:
        if not self.claim.strip() or not self.source_url.strip() or not self.locator.strip():
            raise ValueError("Evidence requires claim, source URL and locator")
        if self.verified and not self.sha256:
            raise ValueError("Verified evidence must identify its source hash")


@dataclass(frozen=True)
class Decision:
    decision_id: str
    proposal: str
    rationale: str
    evidence_ids: tuple[str, ...]
    alternatives: tuple[str, ...] = ()
    status: str = "PROPOSED"

    def __post_init__(self) -> None:
        if self.status not in {"PROPOSED", "ACCEPTED", "REJECTED", "NEEDS_EVIDENCE"}:
            raise ValueError("Invalid decision state")
        if self.status == "ACCEPTED" and not self.evidence_ids:
            raise ValueError("Accepted technical decisions require evidence IDs")


@dataclass(frozen=True)
class CasePacket:
    goal: str
    scope: str
    known_hypotheses: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    blockers: tuple[str, ...]
    assigned_question: str
    scientific_status: str = "UNVERIFIED"

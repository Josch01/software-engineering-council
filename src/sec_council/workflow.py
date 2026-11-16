"""Auditable finite-state workflow. Passing tests cannot certify science."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .contracts import CheckResult, GateStatus


class Phase(str, Enum):
    INTAKE = "INTAKE"
    SCOPED = "SCOPED"
    REVIEWED = "REVIEWED"
    IMPLEMENTED = "IMPLEMENTED"
    TESTED = "TESTED"
    AUDITED = "AUDITED"
    RELEASED = "RELEASED"
    BLOCKED = "BLOCKED"


ALLOWED = {
    Phase.INTAKE: {Phase.SCOPED, Phase.BLOCKED},
    Phase.SCOPED: {Phase.REVIEWED, Phase.BLOCKED},
    Phase.REVIEWED: {Phase.IMPLEMENTED, Phase.TESTED, Phase.BLOCKED},
    Phase.IMPLEMENTED: {Phase.TESTED, Phase.BLOCKED},
    Phase.TESTED: {Phase.AUDITED, Phase.IMPLEMENTED, Phase.BLOCKED},
    Phase.AUDITED: {Phase.RELEASED, Phase.IMPLEMENTED, Phase.BLOCKED},
    Phase.BLOCKED: {Phase.SCOPED},
    Phase.RELEASED: set(),
}


@dataclass
class Workflow:
    phase: Phase = Phase.INTAKE
    events: list[str] = field(default_factory=list)

    def advance(self, target: Phase, *, checks: tuple[CheckResult, ...] = (),
                independently_reviewed: bool = False) -> None:
        if target not in ALLOWED[self.phase]:
            raise ValueError(f"Invalid transition: {self.phase.value} -> {target.value}")
        if target == Phase.TESTED:
            if not checks or any(c.status != GateStatus.PASS for c in checks):
                raise PermissionError("TESTED requires executed passing deterministic checks")
        if target == Phase.RELEASED:
            if not independently_reviewed or not checks or any(
                c.status != GateStatus.PASS for c in checks
            ):
                raise PermissionError("RELEASED requires technical checks and independent review")
        self.events.append(f"{self.phase.value}->{target.value}")
        self.phase = target

"""Independent technical acceptance without overstating scientific evidence."""
from __future__ import annotations

from .contracts import CheckResult, GateStatus


def technical_gate(checks: tuple[CheckResult, ...], *,
                   independent_reviewer: str | None = None,
                   author: str | None = None) -> dict:
    if not checks:
        return {"status": GateStatus.BLOCKED.value, "reason": "No executed checks"}
    if any(c.status == GateStatus.FAIL for c in checks):
        return {"status": GateStatus.FAIL.value, "reason": "One or more checks failed"}
    if any(c.status != GateStatus.PASS for c in checks):
        return {"status": GateStatus.BLOCKED.value, "reason": "Checks unresolved or unrun"}
    if not independent_reviewer or independent_reviewer == author:
        return {"status": GateStatus.BLOCKED.value, "reason": "Independent review missing"}
    return {"status": GateStatus.PASS.value,
            "reason": "Technical checks pass with independent review",
            "scientific_claims": "NOT_CERTIFIED"}

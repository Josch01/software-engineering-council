"""Explicit role permissions and safe project-relative paths."""
from __future__ import annotations

from pathlib import Path

ROLE_RIGHTS: dict[str, frozenset[str]] = {
    "director": frozenset({"route", "propose", "approve_scope"}),
    "literature-researcher": frozenset({"read", "search", "propose", "write_evidence"}),
    "optimization-expert": frozenset({"read", "propose"}),
    "data-scientist": frozenset({"read", "propose"}),
    "numerical-analyst": frozenset({"read", "propose", "write_artifact"}),
    "python-engineer": frozenset({"read", "propose", "write_patch"}),
    "test-engineer": frozenset({"read", "run_sandbox", "write_check"}),
    "adversarial-auditor": frozenset({"read", "review", "object"}),
    "scientific-lead": frozenset({"read", "propose", "request_scientific_audit"}),
    "deterministic-checker": frozenset({"read", "write_check"}),
}

FORBIDDEN_MODEL_ACTIONS = frozenset({"certify_scientific_claim", "forge_test_result", "override_gate"})


def authorize(role: str, action: str) -> None:
    if action in FORBIDDEN_MODEL_ACTIONS or action not in ROLE_RIGHTS.get(role, frozenset()):
        raise PermissionError(f"Role {role!r} is not authorized for {action!r}")


def inside(root: Path, relative: str | Path) -> Path:
    """Reject absolute paths, traversal and symlinks resolving outside the root."""
    base = Path(root).resolve(strict=True)
    sub = Path(relative)
    if sub.is_absolute():
        raise PermissionError("Absolute paths are disallowed")
    candidate = (base / sub).resolve(strict=False)
    if not candidate.is_relative_to(base):
        raise PermissionError("Path escapes the authorized workspace")
    return candidate


def require_explicit_approval(*, changes_external_system: bool, approved: bool) -> None:
    if changes_external_system and not approved:
        raise PermissionError("Explicit user approval required for external mutations")

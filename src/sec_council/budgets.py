"""Fail-closed resource and context budgets."""
from __future__ import annotations

from dataclasses import asdict, dataclass


class BudgetExceeded(RuntimeError):
    pass


@dataclass(frozen=True)
class ResourceBudget:
    max_agents: int = 4
    max_initial_papers: int = 5
    max_pdf_bytes: int = 20_000_000
    max_files_scanned: int = 250
    max_file_bytes: int = 256_000
    max_log_bytes: int = 2_000_000
    max_case_chars: int = 12_000
    max_cpu: float = 4.0
    max_ram_mb: int = 4096
    timeout_seconds: int = 900
    max_search_queries: int = 8

    def __post_init__(self) -> None:
        fields = asdict(self)
        if any(not isinstance(v, (float, int)) or v <= 0 for v in fields.values()):
            raise ValueError("Budgets must be positive")
        if self.max_agents > 4 or self.max_initial_papers > 20:
            raise ValueError("Council/paper limits exceed governance ceiling")
        if self.timeout_seconds > 3600:
            raise ValueError("Maximum execution timeout is 3600 seconds")

    def enforce(self, category: str, observed: int | float) -> None:
        quotas = {
            "agents": self.max_agents,
            "papers": self.max_initial_papers,
            "pdf_bytes": self.max_pdf_bytes,
            "files": self.max_files_scanned,
            "file_bytes": self.max_file_bytes,
            "log_bytes": self.max_log_bytes,
            "case_chars": self.max_case_chars,
            "search_queries": self.max_search_queries,
        }
        if category not in quotas:
            raise KeyError(f"Unknown budget: {category}")
        if observed > quotas[category]:
            raise BudgetExceeded(f"{category}: {observed} exceeds {quotas[category]}")

    def compact_case(self, text: str) -> str:
        self.enforce("case_chars", len(text))
        return text

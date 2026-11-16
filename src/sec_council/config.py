"""Load explicit execution limits from TOML; no implicit permission escalation."""
from __future__ import annotations

import tomllib
from pathlib import Path

from .budgets import ResourceBudget

SETTINGS = {
    ("council", "max_agents"): "max_agents",
    ("research", "max_initial_papers"): "max_initial_papers",
    ("research", "max_search_queries"): "max_search_queries",
    ("research", "max_pdf_bytes"): "max_pdf_bytes",
    ("context", "max_case_chars"): "max_case_chars",
    ("context", "max_files_scanned"): "max_files_scanned",
    ("context", "max_file_bytes"): "max_file_bytes",
    ("context", "max_log_bytes"): "max_log_bytes",
    ("execution", "max_cpu"): "max_cpu",
    ("execution", "max_ram_mb"): "max_ram_mb",
    ("execution", "timeout_seconds"): "timeout_seconds",
}


def load_budget(path: Path) -> ResourceBudget:
    with Path(path).open("rb") as fh:
        data = tomllib.load(fh)
    values: dict[str, int | float] = {}
    for (section, option), field in SETTINGS.items():
        if option in data.get(section, {}):
            value = data[section][option]
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError(f"Budget field {section}.{option} must be numeric")
            values[field] = value
    return ResourceBudget(**values)

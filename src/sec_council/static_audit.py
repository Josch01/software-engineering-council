"""Non-executing Python inventory. AST does NOT establish numerical correctness."""
from __future__ import annotations

import ast
import os
from dataclasses import asdict, dataclass
from pathlib import Path

from .budgets import BudgetExceeded, ResourceBudget
from .memory import sha256_file

EXCLUDE = {".git", ".venv", "venv", "node_modules", "__pycache__", ".mypy_cache",
           ".pytest_cache", "dist", "build", "data", "datasets", "artifacts", "logs"}


@dataclass
class FileInventory:
    path: str
    sha256: str
    bytes: int
    lines: int
    functions: list[str]
    classes: list[str]
    imports: list[str]
    warnings: list[str]
    syntax: str


class Inspector(ast.NodeVisitor):
    def __init__(self) -> None:
        self.functions: list[str] = []
        self.classes: list[str] = []
        self.imports: list[str] = []
        self.warnings: list[str] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.functions.append(node.name)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.functions.append(node.name)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.classes.append(node.name)
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:
        self.imports.extend(a.name for a in node.names)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        self.imports.append(node.module or ".")
        if any(a.name == "*" for a in node.names):
            self.warnings.append(f"wildcard import at line {node.lineno}")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Name) and node.func.id in {"eval", "exec"}:
            self.warnings.append(f"dynamic {node.func.id} at line {node.lineno}")
        self.generic_visit(node)


def inventory(root: Path, budget: ResourceBudget | None = None) -> dict:
    budget = budget or ResourceBudget()
    root = Path(root).resolve(strict=True)
    if not root.is_dir():
        raise NotADirectoryError(str(root))
    results: list[FileInventory] = []
    count = 0
    oversized: list[str] = []
    for current, dirs, filenames in os.walk(root, followlinks=False):
        dirs[:] = sorted(d for d in dirs if d not in EXCLUDE
                         and not (Path(current) / d).is_symlink())
        for filename in sorted(filenames):
            path = Path(current) / filename
            if path.suffix != ".py" or path.is_symlink():
                continue
            count += 1
            budget.enforce("files", count)
            relative = path.relative_to(root).as_posix()
            size = path.stat().st_size
            if size > budget.max_file_bytes:
                oversized.append(relative)
                continue
            try:
                content = path.read_text(encoding="utf-8")
            except UnicodeError:
                results.append(FileInventory(relative, sha256_file(path), size, 0,
                                             [], [], [], ["non-UTF8 source"], "FAIL"))
                continue
            inspector = Inspector()
            try:
                inspector.visit(ast.parse(content, filename=relative))
                syntax = "PASS"
            except SyntaxError as exc:
                syntax = "FAIL"
                inspector.warnings.append(f"syntax error line {exc.lineno}: {exc.msg}")
            results.append(FileInventory(
                relative, sha256_file(path), size, len(content.splitlines()),
                inspector.functions, inspector.classes, inspector.imports,
                inspector.warnings, syntax,
            ))
    return {
        "root": str(root),
        "files_seen": count,
        "files_analyzed": len(results),
        "oversized_files_skipped": oversized,
        "files": [asdict(r) for r in results],
        "syntax_gate": "FAIL" if any(r.syntax != "PASS" for r in results) else (
            "INCONCLUSIVE" if oversized or not results else "PASS"),
        "scientific_correctness": "NOT_ASSESSED",
        "note": "AST inventory and syntax checks do not verify algorithm semantics, numerical stability or convergence.",
    }

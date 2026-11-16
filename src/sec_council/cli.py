"""A CLI deliberately separating static inspection, online research, and execution."""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from .budgets import ResourceBudget
from .contracts import CasePacket, TaskRequest
from .literature import cited_references, doi_metadata, download_pdf, search_openalex
from .memory import new_project
from .router import route
from .sandbox import run_python_docker
from .scientific_bridge import handoff
from .static_audit import inventory


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sec-council", description="Software Engineering Council")
    commands = parser.add_subparsers(dest="command", required=True)

    init = commands.add_parser("init", help="Create project state and memory")
    init.add_argument("name")
    init.add_argument("--goal", required=True)
    init.add_argument("--workspace", type=Path, default=Path("projects"))

    router = commands.add_parser("route", help="Classify task and select minimal council")
    router.add_argument("goal")
    router.add_argument("--source", action="append", default=[])

    audit = commands.add_parser("audit", help="Read-only Python AST inventory")
    audit.add_argument("path", type=Path)

    research = commands.add_parser("search", help="OpenAlex metadata search")
    research.add_argument("query")
    research.add_argument("--limit", type=int, default=5)
    research.add_argument("--online", action="store_true")

    doi = commands.add_parser("doi", help="Crossref DOI metadata")
    doi.add_argument("identifier")
    doi.add_argument("--online", action="store_true")

    refs = commands.add_parser("references", help="OpenAlex reference IDs")
    refs.add_argument("openalex_id")
    refs.add_argument("--limit", type=int, default=10)
    refs.add_argument("--online", action="store_true")

    pdf = commands.add_parser("pdf", help="Download approved open-access PDF")
    pdf.add_argument("url")
    pdf.add_argument("target", type=Path)
    pdf.add_argument("--online", action="store_true")

    bridge = commands.add_parser("bridge", help="Prepare handoff to scientific RAG skill")
    bridge.add_argument("--skill-path", type=Path, required=True)
    bridge.add_argument("--goal", required=True)

    run = commands.add_parser("run", help="Docker-only Python execution")
    run.add_argument("--source", type=Path, required=True)
    run.add_argument("--script", required=True)
    run.add_argument("--logs", type=Path, default=Path("projects") / "runs")
    run.add_argument("--approve-execution", action="store_true")

    return parser


def dispatch(args: argparse.Namespace) -> dict:
    if args.command == "init":
        return {"status": "CREATED", "path": str(new_project(args.workspace, args.name, args.goal))}
    if args.command == "route":
        chosen = route(TaskRequest(args.goal, tuple(args.source)))
        data = asdict(chosen)
        data["all_agents"] = chosen.all_agents
        return data
    if args.command == "audit":
        return inventory(args.path)
    if args.command == "search":
        return {"papers": [asdict(p) for p in search_openalex(
            args.query, limit=args.limit, network_approved=args.online)]}
    if args.command == "doi":
        return doi_metadata(args.identifier, network_approved=args.online)
    if args.command == "references":
        return {"references": cited_references(
            args.openalex_id, limit=args.limit, network_approved=args.online)}
    if args.command == "pdf":
        return download_pdf(args.url, args.target, network_approved=args.online)
    if args.command == "bridge":
        packet = CasePacket(args.goal, "Mathematical/theoretical question", (), (), (),
                            "Evaluate exact assumptions and certify only if applicable")
        return handoff(packet, args.skill_path)
    if args.command == "run":
        return asdict(run_python_docker(
            args.source, args.script, args.logs, approved=args.approve_execution,
            budget=ResourceBudget()))
    raise ValueError("Unknown command")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        result = dispatch(args)
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
        return 2 if str(result.get("status", "")).upper() in {"BLOCKED", "FAIL"} else 0
    except (OSError, ValueError, RuntimeError, PermissionError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, ensure_ascii=False),
              file=sys.stderr)
        return 2

"""A CLI deliberately separating static inspection, online research, and execution."""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from .budgets import ResourceBudget
from .config import load_budget
from .pipeline import analyze_project
from .contracts import CasePacket, TaskRequest
from .literature import cited_references, doi_metadata, download_pdf, search_openalex
from .memory import new_project
from .router import route
from .sandbox import run_python_docker
from .scientific_bridge import handoff
from .static_audit import inventory
from .conversation import start_conversation, resume_conversation, add_event
from .skills import activate_skill, load_skill, read_resource


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

    analyze = commands.add_parser("analyze", help="Create bounded project dossier and task plan")
    analyze.add_argument("name")
    analyze.add_argument("--goal", required=True)
    analyze.add_argument("--source", type=Path)
    analyze.add_argument("--workspace", type=Path, default=Path("projects"))
    analyze.add_argument("--config", type=Path)
    analyze.add_argument("--online", action="store_true")
    analyze.add_argument("--initial-papers", type=int, default=3)
    analyze.add_argument("--download-pdfs", action="store_true")
    analyze.add_argument("--skill", help="Skill alias, local directory or GitHub repo URL")
    analyze.add_argument("--skill-ref", help="GitHub revision for skill")
    analyze.add_argument("--registry", type=Path,
                         default=Path(__file__).resolve().parents[2] / "config" / "skills.json")
    analyze.add_argument("--native-subagents", action="store_true",
                         help="Only when the host supports native subagents")

    skill_command = commands.add_parser("skill", help="Load a user-selected skill")
    actions = skill_command.add_subparsers(dest="skill_action", required=True)
    default_registry = Path(__file__).resolve().parents[2] / "config" / "skills.json"
    skill_list = actions.add_parser("list", help="List configured skill aliases")
    skill_list.add_argument("--registry", type=Path, default=default_registry)
    for action in ("inspect", "read", "activate"):
        sub = actions.add_parser(action, help=f"{action} selected skill")
        sub.add_argument("source", help="Skill alias, local path or GitHub repository URL")
        sub.add_argument("--registry", type=Path, default=default_registry)
        sub.add_argument("--ref", help="Optional pinned GitHub commit or simple branch")
        sub.add_argument("--online", action="store_true", help="Authorize remote skill read")
        if action == "read":
            sub.add_argument("--file", required=True, help="Relative referenced skill resource")
        if action == "activate":
            sub.add_argument("--project", type=Path, required=True)
            sub.add_argument("--goal", required=True)
            sub.add_argument("--native-subagents", action="store_true",
                             help="Assert the host really supports native subagents")
            sub.add_argument("--max-roles", type=int, default=4)

    dialogue = commands.add_parser("dialogue", help="Durable conversational project state")
    dialogue_actions = dialogue.add_subparsers(dest="dialogue_action", required=True)
    start = dialogue_actions.add_parser("start", help="Record a no-edit code conversation")
    start.add_argument("--project", required=True, type=Path)
    start.add_argument("--file", required=True, type=Path)
    start.add_argument("--message", required=True)
    status = dialogue_actions.add_parser("status", help="Read compact current project context")
    status.add_argument("--project", required=True, type=Path)
    event = dialogue_actions.add_parser("record", help="Record a durable project milestone")
    event.add_argument("--project", required=True, type=Path)
    event.add_argument("--kind", required=True)
    event.add_argument("--detail", required=True)
    event.add_argument("--actor", choices=("agent", "user", "checker", "reviewer"),
                       default="agent")
    event.add_argument("--proposal-id")
    event.add_argument("--evidence-ref", action="append", default=[])
    event.add_argument("--user-confirmed", action="store_true",
                       help="Only if an actual user message explicitly confirmed this decision")

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
    if args.command == "skill":
        if args.skill_action == "list":
            if not args.registry.is_file():
                return {"status": "BLOCKED", "reason": "Skill registry unavailable"}
            return {"status": "OK", "registry": str(args.registry),
                    "skills": json.loads(args.registry.read_text(encoding="utf-8"))}
        selected = load_skill(args.source, registry_path=args.registry if args.registry.is_file()
                              else None, ref=args.ref, online=args.online)
        if args.skill_action == "inspect":
            return {"status": "OK", "skill": selected.metadata()}
        if args.skill_action == "read":
            return {"status": "OK", "resource": read_resource(
                selected, args.file, online=args.online)}
        return activate_skill(skill=selected, goal=args.goal, project=args.project,
                              supports_native_subagents=args.native_subagents,
                              max_roles=args.max_roles)
    if args.command == "analyze":
        budget = load_budget(args.config) if args.config else ResourceBudget()
        selected = (load_skill(args.skill, registry_path=args.registry if args.registry.is_file()
                              else None, ref=args.skill_ref, online=args.online)
                    if args.skill else None)
        output = analyze_project(workspace=args.workspace, project_name=args.name,
                                 goal=args.goal, source=args.source, online=args.online,
                                 initial_papers=args.initial_papers,
                                 download_pdfs=args.download_pdfs, budget=budget)
        if selected:
            output["skill_session"] = activate_skill(
                skill=selected, goal=args.goal, project=Path(output["project"]),
                supports_native_subagents=args.native_subagents,
                max_roles=budget.max_agents)
        return output
    if args.command == "dialogue":
        if args.dialogue_action == "start":
            result = start_conversation(args.project, args.file, args.message)
        elif args.dialogue_action == "status":
            result = resume_conversation(args.project)
        else:
            result = add_event(args.project, kind=args.kind, detail=args.detail,
                               actor=args.actor, proposal_id=args.proposal_id,
                               evidence_refs=tuple(args.evidence_ref),
                               user_confirmed=args.user_confirmed)
        return {"status": "OK", "conversation": result}
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

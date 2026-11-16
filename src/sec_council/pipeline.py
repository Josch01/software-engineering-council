"""One-shot, explicitly bounded intake pipeline; no simulated LLM execution."""
from __future__ import annotations

import json
import re
from dataclasses import asdict
from pathlib import Path

from .budgets import ResourceBudget
from .contracts import TaskRequest
from .graph import Edge, EvidenceGraph, Node
from .literature import download_pdf, search_openalex
from .memory import _atomic_write, compact_orientation, new_project
from .router import route
from .static_audit import inventory


def _candidate_questions(kind: str, has_source: bool) -> list[str]:
    if kind in {"CODE_AUDIT", "OPTIMIZATION"}:
        return [
            "¿Cuál es la función objetivo exacta, el dominio y las restricciones?",
            "¿Qué criterio de éxito se prioriza: precisión, tiempo, memoria o garantías?",
            "¿Qué datos, semillas, tolerancias y presupuesto de evaluaciones se usarán?",
        ]
    if kind == "DATA_SCIENCE":
        return [
            "¿Cómo se obtuvieron los datos y cuáles son las particiones de entrenamiento/test?",
            "¿Qué métrica y baseline independiente determinan el éxito?",
        ]
    if kind == "THEORY":
        return [
            "¿Cuál es el enunciado exacto y qué hipótesis deben conservarse?",
            "¿Qué nivel de demostración se requiere: local, global o certificado computacional?",
        ]
    return ["¿Qué entregables y criterios de aceptación concretos se esperan?"]


def analyze_project(
    *, workspace: Path, project_name: str, goal: str, source: Path | None = None,
    online: bool = False, initial_papers: int = 3, download_pdfs: bool = False,
    budget: ResourceBudget | None = None,
) -> dict:
    """Produce an actual audit intake dossier and bounded research metadata.

    All specialized analysis tasks remain NOT_RUN until a compatible agent runtime
    or human reviewer performs them. We never record a synthetic PASS.
    """
    budget = budget or ResourceBudget()
    if download_pdfs and not online:
        raise PermissionError("PDF acquisition requires explicit online approval")
    if not 1 <= initial_papers <= budget.max_initial_papers:
        raise ValueError("Requested papers exceed budget")
    source = Path(source).resolve(strict=True) if source else None
    req = TaskRequest(goal, (str(source),) if source else ())
    chosen = route(req, max_agents=budget.max_agents)
    project = new_project(workspace, project_name, goal)
    graph = EvidenceGraph()
    graph.add_node(Node("objective", "GOAL", goal, status="USER_DEFINED"))
    findings = None
    research = []
    acquisition = []
    blockers = []
    if source is not None:
        findings = inventory(source, budget)
        if findings["syntax_gate"] != "PASS":
            blockers.append("Source syntax incomplete/invalid or skipped files")
        for item in findings["files"]:
            node_id = "code:" + item["sha256"][:16]
            graph.add_node(Node(node_id, "PYTHON_FILE", item["path"],
                                item["sha256"], status=item["syntax"]))
            graph.add_edge(Edge("objective", node_id, "DEPENDS_ON"))
    if online:
        try:
            research = [asdict(p) for p in search_openalex(
                goal, limit=initial_papers, network_approved=True, budget=budget)]
        except (OSError, ValueError, RuntimeError) as exc:
            blockers.append(f"Research metadata unavailable: {type(exc).__name__}: {exc}")
        for idx, paper in enumerate(research):
            node_id = f"paper:{idx}"
            graph.add_node(Node(node_id, "PAPER_METADATA", paper["title"],
                                paper["openalex_id"], status="UNVERIFIED_FULL_TEXT"))
            if download_pdfs and paper.get("pdf_url"):
                target = project / "literature" / f"paper_{idx + 1}.pdf"
                try:
                    acquisition.append(download_pdf(
                        paper["pdf_url"], target, network_approved=True, budget=budget))
                except (OSError, ValueError, RuntimeError, PermissionError) as exc:
                    acquisition.append({
                        "source": paper["pdf_url"], "status": "BLOCKED",
                        "reason": f"{type(exc).__name__}: {exc}",
                    })
    obligations = [
        {"id": "TASK-01", "assigned_to": chosen.lead, "status": "NOT_RUN",
         "purpose": "Reconstruct problem, assumptions and code-to-algorithm mapping"},
        {"id": "TASK-02", "assigned_to": "literature-researcher", "status": "NOT_RUN",
         "purpose": "Verify full-text evidence and applicability if needed"},
        {"id": "TASK-03", "assigned_to": chosen.reviewer or "independent-reviewer",
         "status": "NOT_RUN", "purpose": "Independent adversarial review"},
        {"id": "TASK-04", "assigned_to": "test-engineer", "status": "NOT_RUN",
         "purpose": "Design and execute task-specific numerical/regression tests in sandbox"},
    ]
    open_questions = _candidate_questions(chosen.kind.value, source is not None)
    if chosen.needs_clarification and chosen.clarification_question:
        open_questions.insert(0, chosen.clarification_question)
    if chosen.scientific_escalation:
        blockers.append("Scientific certification requires pinned external skill handoff")
    status = "BLOCKED" if findings and findings["syntax_gate"] == "FAIL" else "NEEDS_REVIEW"
    report = {
        "status": status,
        "project": str(project),
        "goal": goal,
        "source": str(source) if source else None,
        "route": {**asdict(chosen), "all_agents": chosen.all_agents},
        "inventory": findings,
        "research_metadata": research,
        "pdf_downloads": acquisition,
        "obligations": obligations,
        "open_questions": open_questions,
        "blockers": blockers,
        "executed_tests": [],
        "scientific_certification": "NOT_PERFORMED",
        "technical_acceptance": "NOT_PERFORMED",
        "note": "An intake dossier is not a completed code or scientific audit.",
    }
    path = project / "reports" / "intake.json"
    _atomic_write(path, json.dumps(report, indent=2, ensure_ascii=False, default=str))
    _atomic_write(project / "reports" / "tasks.json",
                  json.dumps(obligations, indent=2, ensure_ascii=False))
    _atomic_write(project / "graphs" / "decision_graph.json",
                  json.dumps(graph.to_dict(), indent=2, ensure_ascii=False))
    summary = [
        "# Intake dossier", f"Status: {status}", f"Goal: {goal}",
        f"Lead: {chosen.lead}", f"Reviewer: {chosen.reviewer or 'not selected'}",
        f"Code files analyzed: {findings['files_analyzed'] if findings else 'not provided'}",
        f"Metadata papers found: {len(research)}", "## Pending tasks",
        *(f"- {x['id']}: {x['purpose']} [{x['status']}]" for x in obligations),
        "## Open questions", *(f"- {q}" for q in open_questions),
        "## Blockers", *(f"- {b}" for b in blockers),
        "\nNo algorithmic or scientific correctness is certified at this stage.",
    ]
    _atomic_write(project / "reports" / "intake.md", "\n".join(summary) + "\n")
    compact_orientation(
        project, objective=goal, state=status, blockers=tuple(blockers),
        next_step="Review open questions and assign bounded specialist tasks",
    )
    # Keep stdout compact; detailed dossier remains on disk.
    return {
        "status": status, "project": str(project),
        "report": str(path), "lead": chosen.lead, "reviewer": chosen.reviewer,
        "code_files_analyzed": findings["files_analyzed"] if findings else 0,
        "papers_found": len(research), "pending_tasks": len(obligations),
        "open_questions": open_questions, "blockers": blockers,
        "technical_acceptance": "NOT_PERFORMED",
    }

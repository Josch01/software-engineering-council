"""Cheap deterministic triage; domain claims require specialist review."""
from __future__ import annotations

from .contracts import Route, TaskKind, TaskRequest

THEORY = ("demuestra", "teorema", "identificabilidad estructural", "simetría", "simetria",
          "álgebra diferencial", "algebra diferencial", "proof", "prove", "theorem")
OPT = ("optimización", "optimizar", "optimization", "optimizer", "metaheur",
       "acor", "cma-es", "evolutivo", "differential evolution", "algoritmo genético",
       "genetic algorithm", "convergencia", "objective function")
DATA = ("xgboost", "machine learning", "red neuronal", "neural network", "pinn",
        "clasificación", "regresión", "dataset", "ciencia de datos", "data science")
LITERATURE = ("artículo", "articulo", "papers", "literatura", "bibliografía", "doi",
              "referencias", "state of the art")
CODE = ("auditar código", "revisar código", "código existente", "refactor",
        "code review", "debug", "script", "implementación", "implementacion")
BUILD = ("crear programa", "escribir código", "implementa", "build", "desarrolla",
         "crear aplicación", "hacer archivo python")


def route(request: TaskRequest, max_agents: int = 4) -> Route:
    if not 1 <= max_agents <= 4:
        raise ValueError("max_agents must be in 1..4")
    q = request.goal.casefold()
    has_source = bool(request.source_paths) or any(word in q for word in CODE)
    theory = any(word in q for word in THEORY)
    optimization = any(word in q for word in OPT)
    data = any(word in q for word in DATA)
    literature = any(word in q for word in LITERATURE)
    build = any(word in q for word in BUILD)

    if theory and not has_source:
        kind, lead, reviewer, workers = TaskKind.THEORY, "scientific-lead", "adversarial-auditor", ()
    elif has_source:
        kind, lead = TaskKind.CODE_AUDIT, "python-engineer"
        reviewer = "adversarial-auditor"
        workers = ("optimization-expert",) if optimization else (("data-scientist",) if data else ())
    elif optimization:
        kind, lead, reviewer, workers = TaskKind.OPTIMIZATION, "optimization-expert", "adversarial-auditor", ("numerical-analyst",)
    elif data:
        kind, lead, reviewer, workers = TaskKind.DATA_SCIENCE, "data-scientist", "adversarial-auditor", ()
    elif literature:
        kind, lead, reviewer, workers = TaskKind.LITERATURE, "literature-researcher", "adversarial-auditor", ()
    elif build:
        kind, lead, reviewer, workers = TaskKind.IMPLEMENTATION, "python-engineer", "adversarial-auditor", ()
    else:
        kind, lead, reviewer, workers = TaskKind.GENERAL, "director", None, ()

    # Source review invokes the theory bridge when the user asks to certify a mathematical claim.
    escalate = theory
    if has_source and theory and "scientific-lead" not in workers:
        workers = (*workers, "scientific-lead")
    if max_agents == 1:
        reviewer, workers = None, ()
    ordered = tuple(dict.fromkeys((lead, *workers, *((reviewer,) if reviewer else ()))))
    if len(ordered) > max_agents:
        retained = ordered[:max_agents - (1 if reviewer else 0)]
        ordered = (*retained, reviewer) if reviewer and reviewer not in retained else retained
        workers = tuple(x for x in ordered if x not in (lead, reviewer))
    needs = kind == TaskKind.GENERAL and len(q.split()) < 4
    return Route(
        kind=kind, lead=lead, reviewer=reviewer, workers=tuple(workers),
        scientific_escalation=escalate, needs_clarification=needs,
        clarification_question=("¿Qué problema, entradas, salidas y restricciones debo analizar?"
                                if needs else None),
        rationale="Routing by source availability and technical domain; no scientific claim certified.",
    )

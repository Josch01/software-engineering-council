# Software Engineering Council

**An auditable scientific-software engineering council** for optimization, Python code review, data science and evidence-based technical decisions. Spanish-first documentation; Python 3.11+.

[![CI](https://github.com/Josch01/software-engineering-council/actions/workflows/ci.yml/badge.svg)](https://github.com/Josch01/software-engineering-council/actions/workflows/ci.yml)

## Skill-driven, one-host design

**The user chooses the skill. The current host AI reads that skill and dynamically selects its own roles.** No mandatory Gemini+Codex collaboration, no forced second model. If the host supports native subagents it may spawn them; otherwise it uses sequential bounded role passes. A CLI manifest does not execute any LLM or create a real native subagent.

Choose a skill by alias, local folder or public GitHub repository (remote requires --online).
The repository ships with aliases software-engineering-council and scientific-rag
(the latter pinned to a known reviewed commit). Add more aliases in config/skills.json.

~~~bash
sec-council skill list
sec-council skill inspect scientific-rag --online
sec-council init case01 --goal "Estudiar el problema" --workspace projects
sec-council skill activate scientific-rag --goal "Estudiar el problema" --project projects/case01 --online
sec-council analyze case02 --goal "Auditar ACOR" --source ./my_project --skill scientific-rag --online
~~~

For local skills:
~~~bash
sec-council skill inspect /path/to/skill
sec-council skill activate /path/to/skill --goal "Investigar" --project projects/case01
sec-council skill read /path/to/skill --file agents/ROUTER.md
~~~

The activation creates skill_session/ACTIVE_SKILL.md (exact snapshot),
HOST_INSTRUCTIONS.md and SESSION.json with a content hash and role-selection policy.
The same host reads these files, chooses a minimal panel and invokes native subagents
ONLY if its runtime supports them. Otherwise it performs scoped sequential passes.
An explicit --native-subagents flag asserts that capability; the CLI does not verify
or create native agents. Remote skill files are treated as selected instructions,
never as executable downloaded code.

## Current scope: v0.2.0 (skill-driven foundation)

This repository implements a **working CLI**, integrated bounded project-intake dossiers (`analyze`), deterministic task routing, typed contracts, project memory, AST-only source inventory, gated metadata research through OpenAlex/Crossref, restricted open-access PDF download, OpenAlex reference discovery, scientific-skill handoff verification, and opt-in Docker-only execution with CPU/RAM/time/log budgets.

It does **not** yet implement native agent spawning, an autonomous LLM runtime, long-running multiagent orchestration, deep semantic verification of numerical algorithms, vector retrieval, graphical UX, or automatic mathematical certification. A prompt is not an executor; an AST syntax PASS is not algorithm correctness; an external skill handoff is not a skill invocation.

### Install

~~~bash
git clone https://github.com/Josch01/software-engineering-council.git
cd software-engineering-council
python -m pip install -e ".[dev,pdf]"
python -m unittest discover -s tests -v
~~~

No account credentials are required to run offline commands.

### First commands

~~~bash
sec-council init caso-acor --goal "Auditar implementación ACOR" --workspace projects
# Or: create a whole intake dossier automatically (choose a new project name)
sec-council analyze caso-acor-auto --goal "Auditar implementación ACOR" --source ./my_project --workspace projects
# Optional evidence discovery, authorized explicitly:
sec-council analyze caso-acor-rag --goal "Ant colony optimization continuous domains" --source ./my_project --online --initial-papers 3 --download-pdfs
sec-council route "Audita este código de optimización ACOR" --source ./my_project
sec-council audit ./my_project
sec-council search "ant colony optimization continuous domains" --limit 5 --online
sec-council doi 10.1016/j.ejor.2007.02.045 --online
sec-council references https://openalex.org/W2741809807 --limit 5 --online
sec-council pdf https://arxiv.org/pdf/1706.03762 projects/caso-acor/literature/paper.pdf --online
sec-council bridge --goal "¿Es demostrable la convergencia global?" --skill-path ../skill-investigacion-cientifica-rag
~~~

Research requests require explicit --online. External PDF URLs are restricted to a conservative allowlist of public open-access hosts; not all OpenAlex PDF URLs qualify. Metadata and reference IDs are not full-text verification. The pinned scientific bridge only issues a handoff when the local skill's commit and version match; it does not execute a separate agent.

### Execute an untrusted Python script

Execution is disabled unless explicitly approved. The only supported path is **Docker**, not unsandboxed host Python. Load an approved Python image beforehand (for example, python:3.12-slim). No pull takes place during execution.

~~~bash
sec-council run --source ./my_project --script main.py --logs ./projects/runs --approve-execution
~~~

The container has no network, read-only source, read-only root filesystem, non-root user, dropped capabilities, no-new-privileges, and CPU/RAM/pid/time/log quotas. No guarantee of sandbox security can be made against every Docker/OS vulnerability; use an appropriately secured machine. Docker Desktop is required for this execution path on Windows. Script dependencies must already be available inside the approved image.

### Results and evidence

- Code inspection: AST inventory, file hashes, discovered functions/imports, syntax and warnings. **Scientific correctness: NOT_ASSESSED**.
- Research: metadata with a **metadata_only** flag. Source download must be explicitly requested; PDF extraction is opt-in.
- Execution: CheckResult with status PASS / FAIL / BLOCKED / INCONCLUSIVE, elapsed time, code hash and compact log path.
- Technical release: requires executed checks and independent review. Scientific claims need a separate scientific certification workflow.
- Projects: create project-local OBJECTIVE.md, MEMORY_CORE.md, INDEX.json, graphs, evidence, certificates, reports, logs and artifacts. Decisions require explicit evidence IDs.

### Architecture

- src/sec_council/contracts.py: task, evidence, decision and gate contracts
- router.py: minimal specialist selection (up to four)
- budgets.py: resource/context budgets
- permissions.py: role matrix and project path policy
- workflow.py: finite-state transitions and acceptance gates
- graph.py, memory.py: provenance graph and immutable records
- static_audit.py: safe read-only Python inventory
- literature.py: OpenAlex, Crossref, guarded PDF ingestion and optional pypdf extraction
- scientific_bridge.py: pinned interoperability with the existing scientific RAG skill
- sandbox.py: Docker-only bounded execution
- gates.py: independent technical review
- skills.py: explicit skill selection, bounded reading and same-host activation manifests
- cli.py: explicit user-facing commands

See SKILL.md and AGENTS.md for operating rules, protocols/ for decision gates, agents/ for role charters.

### Scientific RAG interoperability

Reference: [skill-investigacion-cientifica-rag](https://github.com/Josch01/skill-investigacion-cientifica-rag), version **3.1.0** pinned at commit cc3388d4eca22de293763e6426746e5b6f85c2ea (as inspected during bootstrap). The bridge refuses stale or mismatched local copies. Update pins **after** reviewing upstream changes, not automatically. Scientific authority and certification remain with that repository's protocols.

### Safety, reliability and roadmap

No API tokens or copyrighted PDFs should be committed. Data/papers and project outputs are excluded from Git. Never use search snippets as verified paper claims. Novelty, convergence, identifiability, and global optimality require evidence matching their precise scope. Code can be syntactically correct and scientifically wrong.

**Next milestones:** domain-aware numerical audit plugins; exact equation-to-implementation maps; controlled paper ingestion and evidence ledger; provider adapters for Codex/Gemini with strict data contracts; multiagent scheduling with write locks; benchmarking/repeated stochastic trials; artifact consistency gates and adversarial evaluation. Do not label any of these implemented until they pass tests.

## License

No license has been selected; default copyright rules apply until the owner chooses one.

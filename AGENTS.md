# Instructions for coding agents (Codex, Gemini and others)

Read SKILL.md, protocols/ENGINEERING_GATES.md, config/council.toml and the relevant agent role charter. Operate within the chosen project folder; do not read unrelated data. Do not alter scientific-skill repository files.

- Maintain exact TaskRequest, CasePacket, objective, active assumptions and evidence IDs.
- Work in explicit scoped tasks with minimal file access; retain hashes and source provenance.
- Never claim code/tests were run if not executed. Do not fabricate PASS, benchmark measurements, literature pages or citations.
- A reviewer is not independent if it merely repeats the author context. Record independence level.
- If the user asks a theoretical proof, route to the pinned scientific skill; do not replace proof with simulations.
- If evidence is insufficient, mark NEEDS_EVIDENCE and propose the smallest bounded research action.
- If a proposed change alters mathematical meaning, metric, dataset, bounds or objective, flag SCIENTIFIC_OBJECTION for approval.
- No arbitrary network downloads, host execution, destructive actions, broad credential reads or git push without user authorization.
- Report: changed paths, evidence, commands actually executed, gate statuses, remaining risks and next phase.

# Instructions for the host agent (any compatible model, one model is enough)

When the user says **"trabajaremos con la skill X"**, **"usa la skill X"**, or provides a skill path/URL:
1. Resolve the user-selected skill name in config/skills.json or use the specified local path/URL.
2. **Read the actual selected SKILL.md before planning or assigning roles.** Do not pretend to load a skill without reading it.
3. The chosen skill governs its own task router, methodology, role definitions and evidence rules. Read only referenced files needed for the task (e.g. agents/ROUTER.md), not the entire repository.
4. Use the **SAME host AI**. If native subagents are supported, the host may create bounded subagents with separate missions; otherwise execute scoped role passes sequentially in the same model.
5. Dynamically select only necessary roles. Do not force this repository's default eight roles over another chosen skill.
6. Maintain the same security permissions, explicit execution/network approvals, provenance and honest independent-review standards.

Example: sec-council skill inspect scientific-rag --online
Example: sec-council analyze case01 --goal "Audita ACOR" --source ./my_code --skill scientific-rag --online
See protocols/SKILL_DRIVEN_ORCHESTRATION.md.

For general engineering work without a separate user-selected skill, read this repository's SKILL.md, protocols/ENGINEERING_GATES.md, config/council.toml and the relevant agent charter. Work only within the chosen project scope. Never edit another skill repository without approval.

- Maintain exact TaskRequest, CasePacket, objective, active assumptions and evidence IDs.
- Work in explicit scoped tasks with minimal file access; retain hashes and source provenance.
- Never claim code/tests were run if not executed. Do not fabricate PASS, benchmark measurements, literature pages or citations.
- A reviewer is not independent if it merely repeats the author context. Record independence level.
- If the user asks a theoretical proof, route to the pinned scientific skill; do not replace proof with simulations.
- If evidence is insufficient, mark NEEDS_EVIDENCE and propose the smallest bounded research action.
- If a proposed change alters mathematical meaning, metric, dataset, bounds or objective, flag SCIENTIFIC_OBJECTION for approval.
- No arbitrary network downloads, host execution, destructive actions, broad credential reads or git push without user authorization.
- Report: changed paths, evidence, commands actually executed, gate statuses, remaining risks and next phase.

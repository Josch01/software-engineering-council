# Skill-driven orchestration: one host model, dynamic roles

A request like "trabajaremos con la skill X" selects a skill, not another AI model.
The agent must read that skill's actual SKILL.md first and obey its task router,
decision rules, evidence requirements, and certification gates.

## Loading
- Accept an explicitly chosen local path, registry alias or exact GitHub repo URL.
- Remote reads require --online and preferably a pinned commit/ref.
- Load only SKILL.md initially; retrieve agents/ROUTER.md, protocols, templates
  and other referenced resources when needed and within a byte budget.
- Store version, source and SHA256. Do not execute downloaded code.
- Never allow a skill to bypass explicit approval, resource limits or source integrity.

## How the host decides
1. Identify the exact obligation and whether the known context already answers it.
2. Determine which specialist roles (if any) materially reduce uncertainty.
3. Assign narrow Case Packets with goals, hypotheses, evidence IDs and budgets.
4. Use native subagents only if this particular host actually supports them.
5. Otherwise perform sequential role passes, marking their independence honestly.
6. Ask a targeted user question if essential information is genuinely missing.
7. Test and review the work; separate technical PASS from mathematical proof.
8. Persist compact decisions, citations and audit artifacts. Do not claim results
   from merely writing a proposed plan.

## Independence
NATIVE_SUBAGENTS means actual host runtime availability has been confirmed.
SEQUENTIAL_ROLE_PASSES are perspectives within the same model and MUST NOT
be reported as an independent scientific second review.

## Scope precedence
An explicit user-selected skill controls its domain methodology and choice of
specialist roles. Safety, permissions, provenance, bounded execution and honest
representation of what was actually run remain non-overridable.

## Agent delivery contract
Task_ID | Role | Precise_question | Assumptions | Evidence_IDs |
Read_allowlist | Write_allowlist | Resource_budget | Expected_output |
Independent_review_requirement | Stop_condition | Status

No provider switching is needed; the same current host executes each role.

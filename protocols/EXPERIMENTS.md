# Experiment protocol

- Define input data/source/hash, dataset partitions, objective, constraints, tolerances, environment and computational limits.
- Deterministic methods: record versions and numerical tolerances. Stochastic methods: record independent seeds and distributions.
- Baselines must use comparable evaluation budget and appropriate tuning. Compare time, number of objective calls, memory, statistical spread and failure cases, not only best loss.
- Preserve full raw output under projects/*/logs, expose only compact checks to agents.
- STOP on timeout, output-budget, memory-limit, missing dependencies or invalid data. Do not invent measurements.
- Distinguish: a repeatable numerical experiment [N] from a mathematical demonstration [D].
- The final reviewer must test a plausible counterexample or failure mode where feasible.

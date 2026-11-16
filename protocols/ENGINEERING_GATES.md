# Engineering gates

## Gate E0: scope
Pass only with an explicit purpose, read/write boundaries and resource budget. Unknown objective -> BLOCKED until clarified.

## Gate E1: baseline inspection
List source file hashes, functions, interfaces, objective definitions, constraints and tests; do not execute code during inventory. Syntax pass is not semantic pass.

## Gate E2: research sufficiency
Claim -> verified source ID + exact locator + assumptions + applicability. Metadata-only entries are DISCOVERED, not evidence for the source's equations. Traverse citations only for an identified missing premise.

## Gate E3: patch review
Minimal diff, compatibility, backward behavior, data leakage, numerical instability and reproducibility checked. Material scope/metric/hypothesis changes need an explicit objection.

## Gate E4: deterministic checks
Executed tests, bounded sandbox, environment, input/source hash, seed/tolerance, logs and status. BLOCKED on timeout, unrun checks or incomplete traceability. A test's process exit=0 supports execution success only.

## Gate E5: adversarial audit
Independent reviewer checks code-to-algorithm equivalence, untested edge cases, fair baseline and unsupported claims. The reviewer cannot self-certify.

## Gate E6: release
PASS only if relevant deterministic checks PASS and independent review is recorded. Scientific theorems are NOT_CERTIFIED by this gate and require separate science protocol.

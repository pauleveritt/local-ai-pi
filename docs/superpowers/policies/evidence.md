# Evidence Policy

Every claim in the course that a technique *helps* must be backed by a dated
report in `docs/superpowers/research/`, produced by the eval harness, not by
prose assertion. This is the course's own application of its central lesson:
telemetry and validation are the source of truth; an agent's report is not
evidence.

## Tiers

Borrowed from the prior work's evidence ledger. Every number carries a tier.

- **GREEN** — deterministic and artifact-backed. A GREEN claim names the report
  file and the run it came from. A GREEN number with no artifact behind it may
  not be published.
- **YELLOW** — real but noisy (small n, confounded, high-variance). A YELLOW
  claim must carry a one-line note stating the confound or the sample size.
- **RED** — estimated, illustrative, or from no live run. RED numbers are never
  presented as results; they may appear only as explicitly-labelled expectations.

## Rules

1. Show the failure before teaching the fix. A chapter introduces a technique
   only after a recorded run demonstrates the failure it addresses.
2. Report the literal result — the exact acceptance-command output, the changed
   file set, the turn count — not a summary of it.
3. A passing smoke test is not a passing phase. Acceptance means the phase
   contract's literal requirements are met, checked explicitly.
4. Comparisons report raw timing and turn counts, not session lifetime, and name
   the resolved model. Fewer turns or a cache hit does not by itself prove an
   improvement.
5. If the baseline does not reproduce a failure on the target model, the
   corresponding improvement is moved to backlog with a note — it is not taught
   as if the failure were live.
6. **Validate the oracle before trusting a batch.** An oracle's verdict is
   not evidence until the oracle has been shown to accept a known-good
   solution (see `tests/test_oracle.py`). Any change to the workload, the
   workspace stamp, or the acceptance command re-triggers this validation
   before the next published batch.

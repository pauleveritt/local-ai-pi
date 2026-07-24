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
7. **No chapter may claim a success-rate delta.** Detecting a realistic
   mechanism effect (e.g. 75% → 90%) needs ~100 runs per arm; at 130–380s
   per steered run across ~8 mechanisms that is never affordable, so such a
   claim would always be made on evidence too thin to support it. Every
   mechanism claims one of:
   - **structural impossibility** — the mechanism makes failure X
     unreachable. Evidence: one artifact trace of it firing, plus n=8–16
     showing the task still completes.
   - **behavioral-incidence change** — a high-frequency, per-run countable
     signal (inherited-file write attempts, replace-vs-extend,
     self-report-vs-verdict disagreement). Evidence: n=16 with counts.
   - **rare-outcome change** — only for unsteered arms, n≥20–25 per arm,
     reported with the exact test and p-value.

   Success rate may be reported as context, always with its interval.

8. **A gate is not passed until a different model has tried to break it.**
   Every adversarial review round in this project's history was run by a
   different model than the one that produced the work, and every round found
   a defect the author had missed and self-review had cleared: a guardrail
   wired to an event that structurally could not observe its own target
   failure; a path-traversal bypass; a guard that blocked the project's own
   test command; and two live oracle defeats found hours after the hardening
   commit that was supposed to close them. The reverse holds too — a forensic
   replay overturned an amendment written the same day by the same assistant.

   Therefore: for any change to the **grading path, the acceptance suites, or
   the harness's measurement code**, the task's gate requires a review by a
   model other than the one that wrote it, and the review's findings are
   recorded with the change. Chapter prose and reports are exempt; what grades
   models is not.

   The reason this is a rule and not advice: **an author's confidence carries
   no information about whether the work is correct.** Every defect above was
   committed by an author who believed the work was done. Self-review cannot
   be the last step, because the thing being reviewed is the reviewer.

(artifact-retention)=

## Artifact retention

Reports name the session that produced each row — `` `e2e126110318` `` — but do
**not** link the transcript, because transcripts are not published.

They are written to `docs/section-*/research/sessions/<id>.jsonl` and are
gitignored. That is deliberate: a single delegating run has exceeded 60 MB, and
a batch of sixteen routinely exceeds the practical size of a GitHub Pages
deployment. Linking them anyway produced 40 dead download links on the live
site — the failure this note exists to prevent, found 2026-07-24.

Consequences, which a reader is owed plainly:

- A published report is **checkable in structure but not re-derivable from
  source** by a reader. The counts, the changed-file sets, and the verdicts are
  what is published; the raw transcript stays with whoever ran the batch.
- The fix is a **distilled per-run artifact** — the tool-call sequence and the
  verdict, a few KB — small enough to commit and publish. That derivation is
  owed by [reboot Task 7](../plans/2026-07-24-grading-path-reboot.md); until it
  ships, reports cite IDs as plain text.
- Transcripts backing a **withdrawn** batch may be deleted to reclaim disk, but
  only after confirming no surviving report's finding was replay-derived from
  them, and only with an inventory record. See the
  [SP2 deletion record](../../section-3-sdd/research/2026-07-24-sp2-session-deletion-record.md).

## Measurement doctrine

The rules above govern what may be *claimed*. These four govern how a batch is
*constructed* — each was adopted after a measurement it invalidated, and each
was previously reachable only by reading a plan header. This section is the
single authoritative statement; the source documents keep the full argument and
the incident that produced it.

**D1 — Incremental seeded start state.** A phase-N run starts from the
committed reference solution of phases 1..N−1, overlaid before the pristine
commit. A run from an empty workspace measures phases 1..N combined and must
not be labelled phase N.
*Invalidated:* "Phase 2: 0/8", which was actually Phases 1+2.
([oracle-repair Amendment 1](../plans/2026-07-24-oracle-repair.md))

**D2 — Failure-mode incidence is the primary metric.** Each chapter names a
failure mode and reports its incidence, not a success rate. Batches are n=16
unsteered / n=8 steered, and **every escalation decision operates on pooled
results only** — ≥15/16 escalate, ≤12/16 candidate ditch, 13–14 ambiguous and
decided with the human. Two n=4 samples of the identical configuration
returned 4/4 and 2/4; that is why sub-batches never decide alone.
([oracle-repair Amendment 2](../plans/2026-07-24-oracle-repair.md))

**D3 — The acceptance suite is harness-owned and human-authored.** It lives in
`examples/acceptance/phase-<N>/`, is overlaid *after* the model finishes, is
cumulative across phases 1..N, and is the sole grade. The model's own suite is
run separately as the false-self-report signal. Non-vacuity is gated in both
directions: the suite must pass the reference solution *and* fail a
deliberately broken one. Authoring it is human work by design — it is the one
artifact that must not be written by a model, because it is what grades models.
*Invalidated:* every batch graded by `tests/test_app.py`, a file the model
rewrites. ([oracle-repair Amendment 3](../plans/2026-07-24-oracle-repair.md))

**D4 — The grader accepts no model-controlled input.** Grading happens outside
the workspace, in a fresh directory holding an explicit allowlist of the
model's source artifacts and **no configuration files of any kind**. A positive
count of *executed* tests is required; `returncode == 0` alone is not evidence.
This replaces blacklisting — removing `conftest.py`, re-stamping
`pyproject.toml` — which closed two vectors while `pytest.ini`, `tox.ini`,
`setup.cfg`, and an import-time `os._exit(0)` each still forged a green result.
An allowlist is only as tight as the tools it can see (`lessons.md` #8).
([grading-path reboot, Task 2](../plans/2026-07-24-grading-path-reboot.md))

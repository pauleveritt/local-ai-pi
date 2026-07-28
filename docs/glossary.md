# Glossary

This glossary defines the eval-testing dialect used throughout the course. Every
term is cross-referenceable: write `{term}`term name`` to link to it from any page.

```{glossary}

Eval harness
Harness
  The automation suite in `harness/` that provisions workspace, runs the agent
  headless, captures output, and judges results. The harness is the course's
  measurement instrument — every evidence report depends on it.

Workspace
  A disposable temp directory where the agent does its work. The harness
  provisions it with a pristine git commit so `git diff` shows only what the
  model changed.

Pristine commit
  The `git init && git commit` baseline the harness makes before the agent
  runs. All changes are measured against this commit, guaranteeing the diff
  reflects only the model's work.

Stamp
  The harness writes the workspace's `pyproject.toml` rather than copying it
  from the example source. This isolates the harness from the example's
  state and lets the harness inject load-bearing configuration.

Seed
  A reference solution overlaid into the workspace before the agent runs
  (e.g. Phase 1 reference seeded before a Phase 2 run). The seed is committed
  into the pristine baseline so the agent's change surface reflects only the
  phase under test.

Session
  One headless Pi invocation from start to finish, captured as a JSONL
  artifact. A session includes every event — tool calls, model responses,
  subprocess output — that Pi emitted.

Run
  Synonym for {term}`session` in most contexts. One agent invocation.

Batch
  A set of *n* runs with identical configuration, aggregated into one evidence
  report. Published baselines use n=8; scouts use n=4.

Arm
  A named configuration variant being compared to other arms in a controlled
  experiment. For example, Arm A (untuned steered) versus Arm B (tuned steered).

Profile
Invocation profile
  An enum value that determines which extensions and flags are active during a
  run. SP1 means bare agent (no delegation), SP2 means subagent + orchestrator.

Scout
  A small n=4 probe batch used to locate where the model starts failing.
  Part of the "scout then pool" protocol.

Pool
Pooling
  Adding more runs to a scout batch (4 → 8) to improve statistical confidence
  when the scout locates a ditch.

Scout-then-pool
  The combined protocol: scout phases at n=4 until a {term}`ditch` is found,
  then pool to n=8 at that phase for statistical confidence. The course's
  standard measurement protocol.

Outcome
  How a session ended: `exited` (normal), `timeout` (wall-clock limit),
  `exited-with-hang` (agent finished but process lifecycle misbehaved), or
  `crashed` (non-zero exit other than timeout). Timeout and crash are failures;
  exit-hang is treated as non-failure for task metrics because it reflects
  server symptoms, not agent competence.

Success
Success rate
  A run is successful when its {term}`outcome` is ``exited`` or
  ``exited-with-hang`` (not timeout/crash), the {term}`acceptance oracle` passes (pytest exit 0), and the
  model actually wrote something (non-zero {term}`change surface`).

Stop condition
  What tells the agent it is done and should stop working. The
  {term}`implementer`'s stop condition is its validation command passing —
  when the command drifts, the agent falsely stops. The harness's
  stop condition is the independent {term}`acceptance oracle`, which is
  authoritative.

Acceptance oracle
Oracle
  The pass/fail judge: `uv run pytest -q` executed in the workspace after the
  agent finishes. If the tests pass, the agent succeeded. The oracle is the
  gatekeeper of every evidence claim.

Oracle validation
  Running the oracle against a known-good {term}`reference solution` to prove
  the oracle itself works. Rule 6 of the {term}`evidence policy`: an oracle's
  verdict is not evidence until the oracle has been validated at least once.

Oracle gate
  The precondition check before any batch is trusted: the oracle must first
  pass {term}`oracle validation` against the reference solution.

Smoke test
  A quick sanity check ("does the app start?"). The {term}`evidence policy`
  rule 3 draws a hard line: a passing smoke test is not a passing phase.
  Acceptance means the phase contract's literal requirements are met, checked
  explicitly by the {term}`acceptance oracle`.

Reference solution
  A fully spec-compliant, human-authored solution in
  `examples/agentclinic/reference/` that the oracle must accept. Deliberately
  contains no pytest workarounds — it tests the oracle, not the model.

Change surface
  The union of `git diff` (tracked changes) plus untracked files after the
  agent runs. Represents everything the model touched.

Drift
  When a steered agent narrows its work to pass the test at the cost of
  spec compliance — e.g. hardcoding the expected response instead of building
  the requested feature. Measured in steered arms as a failure mode. See also
  {term}`overreach`, {term}`validation command drift`.

Overreach
  A specific {term}`drift` mode: the {term}`implementer` creates files outside
  its Allowed Files list — e.g. building Phase 2 files during a Phase 1 run.
  Named as a primary failure mode in the SP2 baseline (4/8 pre-tuning).

Validation command drift
  A specific {term}`drift` mode: the {term}`implementer` runs a narrower
  validation command than the {term}`packet` specifies (e.g.
  `uv run pytest -q tests/test_app.py` instead of `uv run pytest -q`).
  The narrower command passes in isolation; the full command fails.
  This is the motivating failure for the Terminal Validation chapter.

Repair
  A follow-up {term}`subagent` call dispatched by the {term}`orchestrator` to
  fix a failed {term}`implementer` run. Repair attempts are capped by the
  orchestrator's repair policy ("at most once" post-tuning).

Repair spiral
  When {term}`repair` attempts never converge — the {term}`orchestrator`
  keeps dispatching fixes, the {term}`implementer` keeps producing broken
  output, and the run burns through its time budget. Distinct from
  {term}`overreach`, though the two often co-occur.

Evidence report
  A dated Markdown file in a section's `research/` directory. Each report
  contains a per-row table linking every run to its {term}`session artifact`,
  plus an assessed {term}`evidence tier` line.

Session artifact
Artifact
  The raw JSONL file from a Pi session — the ground-truth record. Every
  number in an {term}`evidence report` must be traceable to a session
  artifact. The course's rule: no claim outruns its artifact.

Evidence tier
Tier
Tier line
  Every number in an evidence report carries a tier:
  {term}`GREEN` (deterministic, artifact-backed),
  {term}`YELLOW` (real but noisy — small *n*, confounded, high-variance),
  or {term}`RED` (estimated/illustrative, never presented as results).
  The tier line in each report explicitly assesses which tier applies and why.

GREEN
  Deterministic and artifact-backed. A GREEN claim names the report file and
  the run it came from. A GREEN number with no artifact behind it may not be
  published.

YELLOW
  Real but noisy — small *n*, confounded, or high-variance. A YELLOW claim
  must carry a one-line note stating the confound or sample size.

RED
  Estimated, illustrative, or from no live run. RED numbers are never
  presented as results; they may appear only as explicitly-labelled expectations.

Superseded
  A banner marking an evidence report whose numbers were invalidated by an
  oracle defect. Superseded reports are kept for the historical record — never
  deleted — but are no longer citable as live evidence. Every superseded
  report links to the incident report that invalidated it.

Evidence policy
  The rules in `docs/superpowers/policies/evidence.md` governing when and how
  claims may be published. Currently six rules: show the failure before the
  fix, report literal results, acceptance ≠ smoke test, compare raw timing
  and turns, do not teach an absent failure, and validate the oracle before
  trusting a batch.

Evidence ledger
  The complete collection of dated {term}`evidence report` entries forming the
  course's evidence chain. Every "this helps" claim must cite a report in the
  ledger.

Adversarial review
  Testing a {term}`guardrail` by actively trying to break it — e.g. path
  traversal to bypass a path guard, or crafting a bash command that triggers a
  false positive. The Section IV design cites adversarial-review findings from
  the prior course as raw material.

Cross-model review
  Using a different model to verify work: a stronger model settles the design,
  a cheaper model executes it, an independent checker decides whether it
  worked. This is LESSONS.md #3 applied to the course's own construction
  (documented in `how-this-was-built.md`).

Smoking gun
  The first phase where the unsteered SLM's success rate drops below 50%.
  Proves the course premise that steering is needed. Finding the smoking gun
  is the goal of the {term}`scout`-then-{term}`pool` protocol.

Ditch
  The phase where the model predictably fails — the course's measurement
  target. "Locate the ditch" means scout phases in order until one drops
  below the threshold. All improvement chapters measure against the ditch.

Escalation
  Two meanings in this course:

  1. **Phase escalation** — the protocol for locating the {term}`ditch`:
     scout Phase 1, then Phase 2 if Phase 1 passes, then Phase 3 if Phase 2
     passes. Stop at the first phase below threshold.
  2. **Fix escalation** — the method of trying the cheapest intervention first
     (prompt/packet tuning), measuring, and only escalating to a
     mechanism-level fix if the failure persists. The Terminal
     Validation chapter is structured around this: wrapper script first
     (prompt-level), validate tool second (mechanism-level), only if drift
     remains.

Before-picture
After-picture
  The measurement taken before and after an intervention. Every guardrail
  chapter is structured this way: show the before-picture from the relevant
  baseline, apply the mechanism, present the after-picture. The SP2
  post-tuning baseline (5/8) is the before-picture for all of Section IV.

No-ditch contingency
  Pre-registered rule: if all phases pass at 4/4, record the result honestly
  and return to the human. Do not invent a harder workload unilaterally.

Telemetry
  Structured metrics extracted from a {term}`session artifact` — wall time,
  turn count, subagent call count, packet size, drift incidence. Telemetry is
  the raw material evidence reports are built from.

Subagent
  In SP2 (steered) runs, a child agent dispatched by the orchestrator to
  perform a discrete unit of work. Subagent delegation is the steering
  mechanism Section 3 teaches.

Orchestrator
  In SP2 runs, the top-level agent that decomposes work and dispatches
  {term}`subagent` calls. The orchestrator never writes code directly — it
  plans and delegates. Also called the {term}`parent`.

Parent
  The top-level agent session that dispatches {term}`subagent` calls.
  Synonym for {term}`orchestrator` in the SP2 architecture.

Child
  The subprocess spawned by the subagent extension to execute a
  {term}`specialist`'s work. The child runs `pi --mode json -p --no-session`
  with the specialist's system prompt and restricted tools. Its event stream
  is currently discarded by the shipped extension (see
  {term}`telemetry gap` #1).

Specialist
  A `.md` file in `.pi/agents/` with YAML frontmatter defining a callable
  subagent. The frontmatter declares the agent's name, description, allowed
  tools, and model; the body is the system prompt. The {term}`implementer` and
  scout are both specialists.

Discovery
  The subagent extension's scan for {term}`specialist` files. The
  `discoverAgents` function searches `.pi/agents/` (project-local) and
  `~/.pi/agent/agents/` (user-level). Without a matching specialist file,
  discovery returns empty and delegations fail with "Unknown agent."

Implementer
  The {term}`specialist` that builds code from a {term}`packet`. Its system
  prompt constrains it to read, write, bash, and validate — no exploration,
  no redesign. The implementer is the workhorse of the SP2 architecture.

Handoff
  The information passed from {term}`orchestrator` to {term}`implementer` —
  the {term}`packet`. A lossy handoff is one where the orchestrator
  paraphrases the roadmap instead of passing it verbatim, producing a packet
  that omits acceptance strings or allowed files. Packet verbatim extraction
  is the defense.

Packet
  The serialized task specification sent from {term}`orchestrator` to
  {term}`subagent`. Contains the task (phase extracted verbatim from the
  roadmap), allowed files, acceptance strings, and the validation command.

Packet fidelity
  A metric that mechanically checks whether a {term}`packet`'s acceptance
  strings and allowed-files list match the roadmap verbatim. Distinguishes
  "good packet, {term}`implementer` failed" from "bad packet, implementer
  never had a chance." One of the five {term}`telemetry gap` entries identified by
  the SP2 deep-dive.

Guardrail
  An umbrella term for mechanism-level protections that keep the agent on
  track: path guard, turn cap, repeat breaker, output cap. Guardrails are
  built as Pi {term}`hook` callbacks — TypeScript extensions that intercept events —
  and are the subject of Section IV. Contrasts with prompt/packet tuning,
  which is cheaper but not structurally enforceable.

Circuit breaker
  A {term}`guardrail` that stops a runaway process. Examples: a turn cap that
  aborts the session after N {term}`turn` cycles, a repeat breaker that counts
  consecutive identical tool calls and aborts on threshold.

Hook
  An event listener callback registered via `pi.on()` in a Pi extension.
  Hooks are the core extension API primitive — every {term}`guardrail` in
  Section IV is a hook. The hello-world extension in Section I teaches seven
  hooks spanning the full {term}`lifecycle`.

Lifecycle
Event lifecycle
  The ordered sequence of Pi events: `session_start` →
  `agent_start` → `tool_call` → `tool_execution_start` →
  `tool_execution_end` → `turn_end` → `agent_end`. Every agent run
  traces this path. Extensions hook into specific points in the lifecycle to
  observe, measure, or intervene.

Turn
  One cycle of the agent loop: the model reasons, calls tools, sees results.
  A single prompt can trigger many turns in sequence — each `turn_end` event
  is the seam between cycles.

Telemetry gap
  An identified deficiency in the harness's measurement coverage. The SP2
  deep-dive identified five: (1) child session JSONL not captured,
  (2) harness pytest output discarded on failure, (3) {term}`packet fidelity`
  not measured, (4) {term}`validation command drift` not detected,
  (5) self-report vs harness verdict agreement not measured.

SLM
Small language model
  A language model small enough to run locally on consumer hardware. The
  course uses `omlx/gemma-4-12B-it-MLX-8bit` as its reference SLM. Contrasts
  with the "godbox" experience of large remote models.

```

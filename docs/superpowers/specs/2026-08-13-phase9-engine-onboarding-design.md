# Phase 9 — An engine you can install

**Date:** 2026-08-13
**Status:** design — approved before any cycle

## Direction, one sentence

> Make the engine adoptable by a Python developer running a small local
> model in Pi: a one-file install that puts the guards in every session, a
> README whose setup section serves both the engine and the evals, and an
> honest pilot number for what the guards change.

## Why this phase, and why now

The engine works, but it has no user-facing front door. The loop breaker is
one installable file and one documented page; the rest of the guards are
contributor-facing source sitting next to research machinery. The bounded
executor (`tools/deliver_candidate`) works and is tested, but reaching it
means a checkout of this repository and reading `harness/runner.py` to
understand it. The README advertises "a bounded executor for your own
repository" but the pitch — *install the engine and your small model
behaves better* — has no number of its own.

Two collaborators are about to join. Before they arrive, the product path
needs to be legible to the people it serves, and legible to the
collaborators who will explain it. This phase gives the engine a
user-facing install, a shared setup section, a `docs/engine/` section, and
one pilot comparison behind the pitch.

## What this phase is not

- **Not the npm package.** The eventual install destination is `npm
  install` of a package (published, local tarball, or from a checkout).
  This phase ships the interim file-copy and records the packaging seam;
  the package itself is a later phase.
- **Not orchestration consolidation.** Bundling the bounded implementer
  into `engine.ts` is deferred to the packaging effort: it would churn
  `tools/deliver_candidate.py`'s digest-pinned import closure and the
  tests that pin it, for no user-visible gain in a docs phase.
- **Not new guards.** The bundle contains what exists — `loop-breaker` and
  `preserve-symbols`. The candidate well (turn budgets, tool-output limits,
  churn breakers, …) stays in the backlog.
- **Not the caps.** `author-cap`, `envelope-cap`, `probe-cap`,
  `proposal-limit` are research calibration for screening arms — named only
  by `tools/screen_workload.py`, `tools/replicate.py`, and
  `tools/build_export.py`, which deliberately does **not** carry them into
  the export. They are not everyday product and are not in the user bundle.
- **Not the eval CLI.** Phase 8 (the `harness.cli` registries and
  subcommands, `docs/evals.md`) is a separate effort. This phase's README
  eval section documents what exists today and does not pre-empt Phase 8;
  if Phase 8 lands first, the eval section links to `docs/evals.md`
  instead.
- **Not confirmatory evidence.** The shootout is a pilot, indexed as pilot,
  with its non-claims written down.

## Decisions locked in brainstorming

**D1 — The user bundle is the two guards, not the caps.** The everyday
install carries `loop-breaker.ts` (the evidenced guard — 261 turns, 245 of
them the identical `ls -R`) and `preserve-symbols.ts` (refuses an `edit`
that deletes a public symbol). The caps stay research-only.

**D2 — Interim install: one self-contained file.** `engine.ts` is a single
file the user copies into `~/.pi/agent/extensions/`, matching the loop
breaker's existing 2-minute story. Two files are acceptable only if a
loader constraint demands it (e.g., Pi's runtime cannot load a bundled
file and needs the types split out). Placement is user-scope, because a
delegated child loads user-scope extensions but not project ones — the
documented gotcha the loop-breaker page already teaches.

**D3 — The executor is onboarded from a checkout, untouched.** The
power-tool path is `uv sync` once, then
`uv run python -m tools.deliver_candidate …` from a clone of this
repository. Its machinery, its closure, and its tests are not changed by
this phase. Orchestration consolidation into the shared bundle is deferred
to the packaging effort (see "What this phase is not").

**D4 — The shootout is pilot evidence.** One suite, 4–6 attempts per arm,
with-engine versus the same suite without it. Recorded as pilot in
`docs/engine/shootout.md`, indexed as pilot in `evidence-index.md`, with
explicit non-claims. No pooling with confirmatory results. If it surfaces a
harness defect, fix and re-run; if the number is disappointing, record it
honestly.

**D5 — The README setup section is shared.** The setup instructions (uv;
ruff/pyrefly/pytest for evals; local model and local server) apply to both
the engine and the evals, so they sit in their own README section outside
the engine and eval sections, and the long form stays in `docs/setup.md`.

**D6 — No new dependencies, no new guards, no manifest.** Nothing is added
to `pyproject.toml`; bun (already in the repo) is the bundler. No
manifest, no Makefile/Justfile target, no comparison automation — those
are Phase 8's and the backlog's territory.

## Section 1 — The engine bundle (`engine.ts`)

The two guards are pure decision functions over tool calls. Their only
imports are type-only (`./types`, the Pi SDK), so they bundle cleanly; the
installed loop breaker already proves the one-file pattern — it
self-registers on `pi.on("tool_call")` and has no runtime imports.

Deliverable: a checked-in installable bundle at
`.pi/extensions/engine.ts` — the same location the loop-breaker install
copy lives in today — produced by bundling the guard sources
(`extensions/guards/loop-breaker.ts` + `extensions/guards/preserve-symbols.ts`
+ their types) with `bun build`, keeping the type-only SDK import and the
self-registration. The install command in the README then reads
`cp .pi/extensions/engine.ts ~/.pi/agent/extensions/`, one line, exactly the
loop-breaker pattern. Bundling the sources, not reimplementing them, is
mandatory: the guard philosophy (`types.ts` docstring) is that a second
implementation of a guard policy can diverge with no test noticing. The
bundle is the shipped artifact and is driven by the same replay fixtures as
the sources.

The guard sources stay in place. `tools/deliver_candidate.py`'s
`IMPLEMENTER_EXTENSION_CLOSURE` and its digest-pinned tests are untouched;
`deliver_candidate` keeps loading the closure it pins today.

**Install verification (hermetic):** the repo already has a test seam for a
fresh agent dir (`tests/test_agent_dir.py`, `PI_CODING_AGENT_DIR`). The
cycle's tests prove the bundle fires on the recorded loop fixture and
stays silent on a clean accepted run — the same two fixtures
`guards.test.ts` already replays — and that the install instructions in
the README and `docs/engine/` stay in lockstep with the artifact (the
`tests/test_loop_breaker_doc.py` pattern).

## Section 2 — README restructure

The README is the GitHub front door (Sphinx home stays `docs/index.md`).
Four parts, in order:

1. **Why** — the pitch stays: small local models, measured,
   verify-don't-assert.
2. **The engine** — why/how/what of the engine, the minimal install
   (`cp .pi/extensions/engine.ts ~/.pi/agent/extensions/`, one line), the
   everyday steering story, and a one-liner for the executor from a
   checkout. Links to `docs/engine/index.md`.
3. **Setup (shared — outside the engine and eval sections)** — `uv`; the
   quality gates `ruff` / `pyrefly` / `pytest` for evals; the local model
   and local server (`omlx start`, the `base_url` gotcha). Points at
   `docs/setup.md` for the long form.
4. **The evals** — what the evals measure, how to run one today (the
   harness), and where the evidence lives. Does not pre-empt Phase 8's
   CLI or `docs/evals.md`.

`docs/index.md` (Sphinx home) gains a matching engine link and toctree so
the two front doors agree on what the product path is.

## Section 3 — `docs/engine/`

A user-facing section, distinct from the contributor-facing
`docs/setup.md` / `docs/contributing.md` / `docs/sdd.md`:

- **`docs/engine/index.md`** — the detailed why/how/what: what the engine
  does, the two faces (install for everyday steering; run the executor for
  a reviewed candidate), the evidence in one paragraph, where to go next.
- **`docs/engine/architecture.md`** — the problems being solved (the
  261-turn loop run; the `/about`-route-deleting edit; a model that cannot
  see its own repetition) and the architecture: guards as pure decision
  functions, one file per concern, the replay seam, and how the executor's
  bounded implementer (typed handoff → mutation engine → preservation
  validation → candidate ref) works underneath.
- **`docs/engine/shootout.md`** — the Section 4 write-up, labeled pilot,
  cross-linked from `evidence-index.md`.

Existing pages keep their jobs: `docs/loop-breaker.md` stays the deep page
for guard #1 and is linked from the engine index; `docs/setup.md` stays the
long form the README setup section points at; `ROADMAP.md` and `BRIEF.md`
stay labeled historical.

Pages that quote the bundle's constants or refusal text get the
`test_loop_breaker_doc.py` treatment — a test that pins the quoted
artifact so the page cannot drift.

## Section 4 — The shootout pilot

**Question:** does loading the guards change accepted rates on a suite,
compared with the same suite, task, prompt, and model without them?

**The engine arm:** a small, explicit seam in the harness — an extension
set carrying `engine.ts` loaded into `run_suite`, everything else identical
to the control arm. Implemented as an extension-only `Improvement` or an
`extensions=` parameter on `run_suite`, whichever the implementation finds
cleaner; it must not disturb the `EXTENSIONS` default, the recorded
conditions, or `run_batch`'s checkpoint contract. Phase 8's CLI is not
involved.

**Scale:** one suite, chosen with the owner at implementation for being the
one whose failure modes the guards actually address (loop repetition,
symbol-deleting edits); 4–6 attempts per arm; the default model
(`DEFAULT_MODEL`); no improvement prompt. The runs need the local model
server and take a few hours of wall time.

**Evidence handling:** the write-up lands in `docs/engine/shootout.md`,
labeled pilot, indexed in `evidence-index.md`, and states what it does
**not** establish. Pilot results are not pooled with the Phase 7
confirmatory result. A harness or validation defect found by the run is
fixed and the run redone; a disappointing number is recorded honestly —
the README's "verify, don't assert" framing survives either way, and the
existing loop-breaker evidence stands alone.

## Test strategy

Hermetic throughout; no live model, no Pi, no network.

- **Bundle (cycle 1):** existing guard tests keep passing
  (`bun test extensions/`, `tests/test_extensions.py`); a test drives the
  shipped bundle against the recorded loop fixture (fires) and a clean
  accepted run (silent) — the `guards.test.ts` replay pattern applied to
  the bundle; a drift test pins the install instructions and quoted
  constants (`test_loop_breaker_doc.py` pattern, extended to the README
  engine section and `docs/engine/`); `deliver_candidate`'s closure tests
  stay green.
- **README and `docs/engine/` (cycles 2–3):** Sphinx builds clean under
  `-W`; links resolve; drift tests green.
- **Shootout (cycle 4):** a hermetic test proves the seam resolves the
  engine extension set without a model server and leaves recorded
  conditions unchanged; the pilot itself is a research run, not a unit
  test.

## Constraints and norms

- **No new dependencies.** Nothing added to `pyproject.toml`; bun is
  already in the repo.
- **No new guards; no executor changes.** The bundle ships what exists;
  `deliver_candidate`'s closure, cell machinery, and tests are untouched.
- **Phase 8 seams respected.** No registry/CLI work here; if Phase 8 lands
  first, the README eval section links to `docs/evals.md`.
- **Quality gates:** `uv run ruff check .`, `uv run ruff format --diff`,
  `uv run pyrefly check`, `uv run pytest`, `bun test` — all green before
  pushing.
- **Sphinx clean under `-W`.**
- **Working style:** branch `engine-onboarding` off `main`, worktree in
  `.worktrees/`. The phase opens with the ROADMAP entry and this spec;
  then four cycle commits, one per cycle, test-first, messages in repo
  style (`feat(phase9): …`, `docs(phase9): …`).
- **Verify, don't assert.** Measured claims are tested or recorded, never
  asserted; the friendly-install claim is proven against a fresh agent dir.

## Definition of done

- A developer following only the README can: (a) install the engine with
  one copy command into user scope; (b) set up uv, the quality gates, and
  the local model/server via the shared setup section; (c) run an eval;
  and (d) read an honest pilot number for with-engine versus without in
  `docs/engine/shootout.md`.
- `extensions/engine.ts` exists, is self-contained, is checked in, fires
  on the recorded loop fixture, and stays silent on a clean run.
- The README has the four parts, `docs/engine/` exists with index and
  architecture, and both front doors (README and `docs/index.md`) agree on
  the product path.
- The pilot is run, written up as pilot, and indexed in
  `evidence-index.md`; `ROADMAP.md` carries the Phase 9 entry with its four
  cycles.
- `uv run pytest` green, all quality gates green, Sphinx clean under `-W`.

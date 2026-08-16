# Phase 13 — The orchestrator, in TypeScript

**Date:** 2026-08-16
**Status:** shape — to be brainstormed into a full spec
**Context:** Written from a disposable spike (`ts-engine-core`, one
session, 10 commits, not merged and not intended to be — see "Spike
findings" below). The spike's code is reference material, not a
deliverable; a real Phase 13 build starts fresh with proper feature
cycles, informed by what the spike learned.

## Direction, one sentence

> Port the delivery lifecycle — worktree isolation, writable-scope check,
> validation, candidate ref — from `harness/candidate.py` into
> `packages/engine/` so `/implement` runs against any repository from a
> packaged install, with no Python and no checkout dependency.

## This reverses a recorded non-goal and a recorded decision

Two prior phase documents said this direction was out of scope. Both
should be read as superseded by this shape, not silently:

- **Phase 10's non-goal:** "It does **not** do TypeScript orchestration —
  the orchestrator's substrate is the Python CLI, and TS orchestration may
  never happen." (`ROADMAP.md`, Phase 10 entry)
- **Phase 11 shape's recorded decision:** "The executor stays a CLI; the
  extension is the front... Fully collapsing into the extension means
  porting the bounded-implementer lifecycle to TypeScript and
  re-establishing its cell/test machinery there — a large effort for
  little measured gain right now. Recorded as a decision, not an open
  question." (`docs/superpowers/specs/2026-08-14-phase11-contract-authoring-bridge-shape.md:98-106`)

Both were reasonable calls made without the cost data this spike now
provides. The "large effort" estimate was untested; the spike put a
number on it (below). This shape doesn't argue the earlier calls were
wrong when made — only that the shape doc's own convention (record a
decision, don't erase it) means this reversal belongs in writing, in the
same place, not as a quiet drift.

## The goal

`/implement` today (`packages/engine/orchestrator.ts` on `main`) spawns
`uv run python -m tools.deliver_candidate`. That means:

- The packaged install (`pi install git:...`, Phase 12's deliverable)
  ships a command that only works from inside a checkout of this
  repository — `tools/` has to exist on disk relative to the spawn.
- `--repo` and the spawn `cwd` are both `ctx.cwd`, so the target
  repository can only ever be this one. A user can never point
  `/implement` at their own project.

Phase 13 closes that gap by making the *product* half of the lifecycle —
not the measurement half — native to the package.

## What stays out, deliberately (mirrors Phase 11's split)

The eval harness (`harness/`, `tools/deliver_candidate.py`) has two kinds
of code mixed together in `harness/candidate.py`'s `deliver()`:

- **Product-shaped:** preflight (refuse a dirty repo), worktree add/remove,
  the writable-scope check, run validation, commit-or-discard, the
  candidate ref. This is what an end user needs and what this phase ports.
- **Measurement-shaped:** cell resolution, model pinning, extension-closure
  digests, the model-server liveness probe, the void/retry branch that
  separates "your server is down" from "the model burned its budget", grading,
  telemetry. This exists to protect denominators across a batch. A person
  running one task has no denominators — the spike's ported `Receipt` has
  two outcomes (`candidate-created` / `discarded`), not the harness's three
  plus retry state, on purpose.

The harness keeps the second half. Whether the harness's `run_model` ever
calls the new TS-ported first half instead of spawning `pi` directly is a
**separate, later decision** (see Open Questions) — this phase does not
require it, and doing it prematurely, without the differential test named
below, is exactly the kind of change that would corrupt eval denominators
silently.

## Spike findings (2026-08-16, `ts-engine-core`, not merged)

n=1 build, one session. These are risk-surfacing findings, not reliability
claims — treated the way Phase 11's own spike findings are: evidence to
carry into the real cycles, not a substitute for building them.

- **The port is small.** The full product lifecycle — bounded child
  runner, git primitives, scope check, receipt, the lifecycle itself, the
  default model-spawning `runModel`, a CLI entry point, and the
  orchestrator rewire — was ~700 lines across 8 files, all reachable by
  tests with **zero model calls** (every branch of `deliver()` is testable
  against a stub `runModel`). This is the concrete number the "large
  effort" estimate in the Phase 11 decision above was missing.

- **A real platform gap, not a hypothetical one.** Python's
  `subprocess.Popen(..., start_new_session=True)` plus `os.killpg` reaches
  a whole process group on timeout. Bun's `process.kill(-pid, sig)` throws
  `RangeError: pid must be a positive integer` — there is no direct
  equivalent. Confirmed both by the build and independently reproduced by
  a second review (killing only the direct child of `sh -c "sleep 30 &
  wait"` left the backgrounded grandchild holding the pipe open
  indefinitely; a real model child that backgrounds work would leak the
  same way). The fix shells out to `kill(1)` with the negative pid, which
  does reach the group. **A real cycle needs to decide this deliberately**,
  not rediscover it under time pressure — it is exactly the kind of gap
  that only shows up when a timed-out child has spawned a subprocess.

- **Python's `fnmatch` and every Node globber disagree, and the disagreement
  is large enough to matter.** `harness/candidate.py`'s writable-scope check
  uses `fnmatch`, where `*` crosses `/` — so `src/*` matches `src/a/b.py`.
  Minimatch, picomatch, and `Bun.Glob` all disagree. If the TS port used a
  standard Node globber, the product would silently discard candidates the
  eval accepts as in-scope — the exact divergence a shared lifecycle exists
  to prevent. The spike hand-ported `fnmatch.translate()`; a first
  differential test (357 generated pattern/path pairs against real Python)
  passed and still missed a real bug (a bracket class starting with `]`,
  fixed after the fact); a second, independent differential sweep (~1,500
  pairs) found a further gap in reversed character ranges (`[z-a]`), which
  Python normalizes to "matches nothing" and the port's first pass throws
  a `SyntaxError` on instead — uncaught, propagating out of the scope
  check. **This is the single highest-value thing to carry forward
  un-re-derived: fnmatch parity needs a maintained differential-test
  harness, run against real Python on every change, not a hand-written
  table trusted once.**

- **The harness and the product currently disagree about what `/implement`
  even runs — this was found by review, not by the build, and it's the
  most important single finding.** `main`'s ad-hoc `/implement` (no
  `--contract-task`) selects `PROBE_EXTENSION`
  (`extensions/probe-cap.ts`, a turn/tool budget capper) with a stock
  `read,bash,edit,write` child — a child that *can* write files. The
  ported orchestrator, to run at all outside a checkout, has to spawn the
  contract-requiring `extensions/implementer/implementer.ts` instead
  — and that extension refuses to call any tool at all when no
  `HandoffContract` is supplied (`implementer.ts:69-72`: "Do not call
  tools; report this configuration failure"). Neither flavor ever builds
  one. So today, on `main`, `/implement` can plausibly write something;
  after a naive TS port with no other change, it never can. **A real
  Phase 13 cannot silently swap the child extension as a side effect of
  the substrate change — it has to either carry the probe-cap flavor
  forward as the product's default child, or make Phase 13 explicitly
  dependent on Phase 11 shipping a contract, and say which.** See the
  Phase 11 research log
  (`docs/superpowers/research/2026-08-15-phase11-handoff-to-construction.md`,
  "Outside confirmation" section, added 2026-08-16) for the full detail
  from the Phase 11 side.

- **The packaging promise was already broken by a smaller, earlier change,
  and nobody had checked.** Six doc pages promised a two-file `cp` install
  once `orchestrator.ts` gained even one local import (`./core/*`). Any
  phase that adds a local import to `orchestrator.ts` needs to re-verify
  the install docs, not just the code — this is a doc-test gap
  (`tests/test_package_install.py`, `tests/test_engine_doc.py`) worth
  keeping regardless of whether this phase's specific `core/` design
  survives.

## Confirmed against `main`, 2026-08-16

Two things the Phase 11 contract-file work's own runnability check hit
directly, while dogfooding `/implement` through a live, non-interactive
`pi` session
(`docs/superpowers/research/2026-08-16-phase11-contract-file-smoke.md`,
"The `/implement` command itself"). Recorded here because both are
exactly the kind of gap this phase exists to close, not new information
about the port's design.

- **The single-repo limitation above isn't just narrow, it's silent.**
  Pointing `/implement` at a different repository doesn't error — `uv
  run` there resolves *that* repository's own `pyproject.toml`, fails to
  find `tools.deliver_candidate`, and exits fast with nothing visible
  (`ctx.ui.notify` produces no output in `--print` mode either, so there
  is no signal at all). A contributor who tries `/implement` against
  their own project today gets what looks like instant success and is
  actually nothing happening.
- **`harness/candidate.py`'s worktree mechanism assumes `.git` is a
  directory, and breaks inside a linked git worktree.** `deliver()`
  creates its candidate worktree at `<repo>/.git/satyrn-worktrees/...`;
  inside a linked worktree (`.git` is a plain gitlink *file* there, not a
  directory) `git worktree add` fails with `Not a directory`. Not
  hypothetical — this project's own contributor workflow
  (`superpowers:using-git-worktrees`) routinely puts people in exactly
  that shape. Whatever ends up owning worktree isolation in the port
  should either handle this case or refuse it with a clear message, not
  reproduce today's silent-ish failure.

## Open questions

1. **Does the harness's `run_model` ever call the ported TS lifecycle, or
   do the two stay permanently parallel?** If yes, it needs a differential
   test — same task, both paths, diff the receipts — run before the
   switch, not after; the harness's tri-state outcome
   (`candidate-created` / `discarded` / `infrastructure-failure` plus its
   liveness-probe voiding logic) has no equivalent in the product-shaped
   receipt this shape describes, and collapsing that distinction changes
   what a batch's denominators mean.
2. **Which `/implement` child does the TS product ship with — probe-cap
   (stock tools, currently what `main` actually runs) or the contract-
   requiring implementer — and is that decision made here or deferred to
   Phase 11?** This is the finding above, and it is the one open question
   this shape treats as blocking: shipping Phase 13 without answering it
   ships a `/implement` that regresses from "sometimes writes something"
   to "never does," silently.
3. **Does `extensions/implementer/` move into the package?** The spike
   used a `SATYRN_IMPLEMENTER` env var as an explicit, named stopgap
   because the implementer extension is not part of `packages/engine/`
   and an installed engine cannot resolve a path into this repository's
   `extensions/` tree. Moving it is mechanical but touches the pinned
   extension-closure digests (`workloads/svcs/cells/*.toml`,
   `resolve_cell`'s `extensions_sha256`) that Phase 7's measurement
   depends on — exactly the kind of change that should not ride along
   with a lifecycle port, per the spike's own plan.
4. **Where does the fnmatch differential-test harness live, and does it
   run on every change to either `scope.ts` or `harness/candidate.py`'s
   use of `fnmatch`?** Not optional — see the spike finding above. A
   generate-pairs-and-compare-to-real-Python script, committed and wired
   into whichever suite runs on this file, is cheap and the alternative is
   a silent scope-policy divergence between the two paths.
5. **Does the receipt need a third outcome for parity with the harness,
   even in the product path?** The spike's two-outcome receipt was a
   deliberate simplification for a single-user tool with no denominators.
   If open question 1 resolves toward a shared implementation, the
   product receipt may need to grow the `infrastructure-failure` /
   liveness-probe distinction back, purely to satisfy the harness's needs
   — in which case the "no denominators, no third outcome" argument in
   this shape's own "What stays out" section would need revisiting.

## What this shape does not decide

- It does **not** decide open question 2, which flavor of child
  `/implement` ships with — that decision has real behavioral
  consequences and belongs to a real cycle, not this document.
- It does **not** commit to porting the harness's `run_model` onto the new
  CLI — that is recorded as an open question, gated on a differential
  test that does not yet exist.
- It does **not** scope the implementer-bundling work (open question 3) —
  only names it and the pinned-digest risk it carries.
- It does **not** carry forward any code from the `ts-engine-core` spike as
  something to be merged. The spike is disposable; the findings above are
  not.

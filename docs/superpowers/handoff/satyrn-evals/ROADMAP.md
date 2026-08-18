# Roadmap: satyrn-evals

Read `BRIEF.md` first. This list is settled; brainstorm within a phase, not
across the list.

Each phase ends with a command a contributor can run, and evidence naming a
success fixture and a failure fixture.

## Phases

| # | Delivers | Done when | Explicitly out |
|---|---|---|---|
| **V1** | `satyrn-evals grade TASK PATCH` | One bundled task accepts its named good patch and rejects its named broken patch. Regrading is offline and deterministic. The default tier passes in single-digit seconds, and a **planted process-spawning test fails the build**. | Capture, model, engine |
| **V2** | `satyrn-evals capture --revert SHA` | The generated synthetic task is winnable by construction: its source diff grades accepted, and the reverted base is rejected. | History mining, prose generation |
| **V3** | `satyrn-evals attempt TASK -- COMMAND...` persists an attempt | Evals runs `COMMAND... CONTRACT` in a disposable worktree, captures stdout, stderr and the Git diff, and can regrade a **fake** command's retained artifacts offline. | Real engine, repetition |
| **V4** | One real engine attempt | `satyrn-engine attempt` (engine E5) runs against the bundled task and produces the same artifact set as V3. A failure leaves enough evidence to diagnose without rerunning. | Batch, A/B, claims |
| **V5** | `satyrn-evals run --n 8` and a diagnostic summary | Interrupted output stays readable. Every attempt records identities and artifacts. The summary reports verdict reasons, repeated identical calls, churn, tool calls, context and timeouts. | Confidence intervals, condition enforcement, canary, publication |

V1–V3 proceed independently of the engine, because V3 uses a fake command.
V4 depends on engine E5 — **not** on a packaged or published engine.

## The bundled task

`examples/duration/` from the prior repository: a spec, an acceptance suite, a
known-good `reference/duration.py`, and a known-broken `broken/duration.py`.
Its only imports are `pytest` and the module under test, so grading it needs
no network and no dependency resolution.

Deliberately rejected: `examples/agentclinic/phase-1/` has the same shape but
requires FastAPI, Jinja2 and turbohtml. `workloads/svcs/` requires a network
clone and a real dependency resolve.

## Capture

A task is admitted only when four deterministic checks pass:

1. the base passes preservation tests;
2. the oracle rejects the base;
3. the target passes preservation and oracle tests;
4. the target diff, restricted to writable paths, is accepted.

A human writes **only** the behavioral brief and the writable paths. The tool
derives commits, patches, commands and observed oracle outcomes. The prior
project made humans hand-author roughly twenty fields a tool can compute, and
ran the cheap disqualifiers *last* — which is why capturing eight tasks cost a
whole phase, not because the checks are expensive.

**The fifth check is the baseline probe** (see `BRIEF.md`), and it is the only
capture step that spends model time. An afternoon of capture is four free
checks plus one paid one. It belongs to V2 and V3.

**Do not scan arbitrary Git history yet.** After three manually captured
tasks, compare their selection steps and automate only what actually repeats.

## Design work this project owes: a suite with headroom

Not a phase. A prerequisite for V5's summary being informative, and genuinely
unsolved.

Three questions to answer before or alongside V5:

- **What property of a task predicts a mid-range baseline?** The prior
  project's envelope screen found two hard walls — no enumeration tool, and an
  output-token limit smaller than the target file — that put tasks at the
  floor for reasons unrelated to difficulty. Those are engine limits
  masquerading as task difficulty.
- **Is difficulty a task property, or a task-plus-engine property?** If the
  latter, a task's band is not permanent, the baseline probe must be re-run
  when the engine changes materially, and "capture once" means something
  weaker than it sounds.
- **Does a suite need a difficulty spread rather than a target band**, so that
  ceiling and floor tasks are present deliberately as controls?

Until this is designed, point V5 at the two recorded discriminating tasks and
say plainly that the sample is two.

## Deferred, with the condition that reopens each

- **Automated commit mining** — after three manual captures show which steps
  repeat.
- **Paired A/B of two engine versions** — when a contributor needs "did my fix
  help" answered across versions. Arms interleave; the results schema carries
  no seconds field.
- **Resumable large batches** — for eight short runs this is claims-layer
  instinct. Carry the prior checkpoint verbatim if it transplants cleanly; do
  not rebuild it.
- **The claims layer** entire.

Two behaviors arrive **with their consumer**, not on day one: position-keyed
node census (with the first Sybil-style task), and materialize /
export-substitution / mtime normalization (with V2–V3, since the leak channel
only exists once tasks come from real repositories).

## Concept budget

Maintained from phase one. Seed terms: **task**, **oracle**, **preservation**,
**baseline probe**, **attempt command**, **verdict**.

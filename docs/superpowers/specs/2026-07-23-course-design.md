# local-ai-pi — Course Design (master spec)

Date: 2026-07-23
Status: approved in brainstorming, decomposed into per-phase sub-projects

This is the whole-course design. It is deliberately high-level: each of the four
Parts is its own sub-project with its own detailed spec and plan, brainstormed
and built in sequence. This document fixes the spine, the constraints, the repo
layout, and the method so that each sub-project spec can be written against a
stable frame.

## Purpose

Teach how to keep a small local model (SLM) on track during real Python
development under the Pi agent harness, using only built-in Pi features. The
course is organized as: measure first, then improve, and prove each improvement
helped.

The through-line is `LESSONS.md` point → the built-in Pi mechanism that
addresses it → a measured before/after. No technique is adopted on faith.

## Non-negotiable constraints

- **Built-in Pi only.** No forked Pi, no patched runtime, no Pyrefly, no
  external type-checker, no bolt-on verification toolchain. Every mechanism the
  course teaches is a capability Pi ships out of the box (events, `setActiveTools`,
  `sendUserMessage`, `appendEntry`, `registerCommand`, the subagent example
  pattern, `models.json`, compaction settings).
- **Evidence-gated.** A technique is kept only if a measured run shows it helps.
  Techniques are introduced *after* their motivating failure is shown, never
  before.
- **The example app is fixed; the phase framing evolves.** The SLM builds the
  same AgentClinic FastAPI complaints board throughout, and its final acceptance
  behavior is constant — the app is held fixed so that steering is the only
  variable. What varies deliberately is how the work is *framed as phases*. Most
  of the course uses the existing overly-detailed, implementation-heavy roadmap
  (reused from the prior OpenCode course) as the baseline workload. Later
  chapters introduce a **higher-level, business/user-story roadmap** consumed by
  the planner tool-agent (Part III); the planner's job is to turn that looser
  roadmap into the same right-sized phase contracts. Both roadmaps target the
  identical app — the shift from detailed to higher-level framing is itself a
  late-course subject, not a change of workload.
- **The target model is a real SLM.** Gemma-class local models served via LM
  Studio or oMLX, the same family the lessons were recorded against.

## Why "built-in Pi only" is achievable, not aspirational

The constraint has a concrete precedent. A prior Pi spike (Tainie) concluded it
had to **fork the Pi runtime** in exactly one place: a repeated-identical-failing
-tool-call circuit breaker patched into `packages/agent/src/agent-loop.ts`
(`~/PycharmProjects/pi-circuitbreaker`, commit `30f2c382`). That is the single
loudest SLM failure — the 170-identical-malformed-call loop. This course reaches
the same behavior with **no fork**: the Part IV repeat-breaker is a pure
extension hooking `tool_execution_start`/`tool_execution_end`, and it was
live-proven against `gemma-4-12b-it-mlx` in the reference repo (a schema-rejected
call does fire `tool_execution_end`, which the extension counts and aborts on).
The one place a prior effort felt forced to fork, this course achieves built-in —
and with stronger evidence than the fork carried (the fork was verified against
stubs, not a live model). The other Tainie fork was of *pyrefly*, an external
type checker, whose entire verify-loop this course excludes by design.

## The four Parts

### Part I — Pi extension basics

Goal: the reader can write and load a Pi extension and knows the shape of the
event lifecycle. Deliverable: a hello-world extension (e.g. `session_start`
notify), and a short chapter walking the lifecycle events the rest of the course
uses (`session_start`, `agent_start`, `tool_call`, `tool_execution_*`,
`turn_end`, `agent_end`) plus `appendEntry` for writing evidence into the
session.

### Part II — Measurement (the smoking gun)

Goal: the reader can measure a run and has *seen the ditch*. This Part is
load-bearing; every later claim depends on it.

Deliverables:
- A telemetry reader. The primary source is the `pi --mode json` event stream
  (`message_end` events carry per-turn usage — input/output/cache/turns — as the
  subagent example already demonstrates). Note the tension the chapter must
  resolve: a headless `pi -p --no-session` run writes **no** on-disk session
  JSONL, so the harness either captures the stdout stream or keeps sessions on to
  read the file. The reader surfaces turns, tool calls, timing, tokens/cache
  where available, and custom `appendEntry` events.
- A minimal eval "session": provision a disposable workspace from the example
  app, run pi headless against one phase, capture the diff, run the acceptance
  tests, and reduce to a structured result.
- An evidence ledger with honest tiers (a measured/artifact-backed result is not
  the same as an estimate), so the course's own numbers are auditable.
- **The baseline run**: the out-of-the-box SLM attempting a real phase with no
  steering, recorded as a dated report in `docs/superpowers/research/`. This is
  the smoking gun the rest of the course answers.

Inspiration, not dependency: the eval-harness shape is informed by the Tainie
eval driver (`~/projects/t-strings/tainie`, `src/tainie/eval/`), but this course
reimplements a minimal version and shares none of its type-checker machinery.

### Part III — Spec-driven development on Pi

Goal: teach SDD on Pi, and honestly test whether a subagent fleet helps.

#### How a Pi "subagent" actually works (the mechanism this Part teaches)

Pi has no native subagent primitive by design (the coding-agent README lists
"no sub-agents" alongside "no MCP, no permission popups"). Unlike OpenCode —
where a subagent is a declarative frontmatter config (model, tools, a
`permission` block) the runtime enforces — a Pi subagent is a **composition of
two things you own**:

1. **The mechanism is a registered tool.** The `examples/extensions/subagent`
   extension calls `pi.registerTool({ name: "subagent", execute })`. The
   `execute` function is arbitrary TypeScript that spawns a separate
   `pi --mode json -p --no-session` subprocess for the specialist, streams its
   JSONL events over stdout, and returns the final result to the parent. You own
   the delegation semantics — schema-checking the packet before spawning, sizing
   it, chaining, parallelism, retry-with-a-narrower-packet.
2. **The specialist is data.** An `agents/<name>.md` file: frontmatter
   (`name`, `description`, `tools`, `model`) plus a system-prompt body,
   discovered from `~/.pi/agent/agents/` and project-local `.pi/agents/`.

Two consequences drive the whole Part, and both improve on the OpenCode
limitations recorded in `LESSONS.md`:

- **The child is a full `pi` process, so it loads the project's extensions.**
  This is the seam where the permission enforcement OpenCode gave declaratively
  (a `permission` block constraining the child from outside) is instead obtained
  *from inside*: a child running in the project inherits whatever guardrail
  extensions the project ships, enforced in its own lifecycle. Two honest
  qualifications the chapter must state: (a) those guardrails do not exist yet at
  Part III — they are built in Part IV — so Part III makes this an explicit
  **forward promise** and the actual demonstration (a subagent composed with the
  guardrails) lives in a Part IV chapter where both exist; and (b) inheritance is
  **project-global, not per-specialist**: the `tools:` frontmatter restricts a
  specialist's tool surface per-role, but per-role path or behavior guards (e.g.
  "the implementer, specifically, may not touch `specs/`") would require
  per-spawn plumbing — env vars or per-role config the guardrail reads — which
  this course does not design. The child guardrail does not know it is "the
  implementer." Constrain the child by the code it runs, but do not overclaim
  OpenCode's per-agent permission parity.
- **From the parent, a delegation is a tool call.** So it is observable and
  governable through the same event hooks as any tool: `tool_call` can block it,
  `tool_execution_end` sees it fail, the repeat-breaker counts a runaway
  re-delegation, `appendEntry` logs it as evidence. The parent's extension code
  cannot hook the child's `turn_end` directly — it only reads the child's
  emitted JSONL — but it fully governs the *delegation*.

What this does **not** fix for free, and what the Part must therefore measure:
the paraphrase-drift handoff (`LESSONS.md #4`) lives in the task string, which is
still a model relaying another model's instruction; and there is no automatic
nesting-depth cap (a spawned process can spawn again). Both are governable with
your own code, not a runtime flag.

#### Deliverables

- The roadmap-and-packet method: a phase contract, the handoff packet, and the
  acceptance command, applied to the example app.
- An orchestrator subagent, built as the registered-tool mechanism above. This
  is the one plain deliverable of the Part; everything below is evidence-gated.
- *(evidence-gated, not a promised deliverable)* A **planner specialist — the
  reserved role for the "galaxy brain."** The
  course does not banish open-ended reasoning; it assigns it to one up-front
  role. The planner runs on a **bigger model** and its job is to turn
  business/user-story phases (deliberately *not* implementation-heavy) into a
  roadmap of right-sized phase contracts. It is a **hybrid tool-agent**: the
  model supplies judgment (what does this story imply?), while deterministic
  TypeScript in the tool's `execute` does the mechanical assembly and sizing —
  reading named targets, computing the changed-file surface, extracting exact
  literals/routes from the spec, and enforcing a token budget on the packet.
  This is `LESSONS.md #3/#4`'s "big-brain planner → little-brain implementer"
  split, with the planner realized as a Pi specialist rather than a chat window,
  and it is the mechanical expression of `LESSONS.md #1` ("structure beats
  strings"): assembly and sizing are code, not SLM improvisation.
- *(evidence-gated)* A fleet beyond the orchestrator: planner, implementer,
  verifier. Each specialist is admitted only if a measured run shows it beats the
  simpler shape it replaces. This re-opens the question the prior course closed
  negatively —
  `LESSONS.md #4` recorded the orchestrator hop *drifting* via paraphrase — and
  answers it with this harness's own measurements rather than assuming either
  outcome.

#### The hard, evidence-gated research thread: oracle derivation

A business-focused phase is *harder* than the current implementation-heavy
phases in one specific way: the current phases embed their own acceptance oracle
(`Scope creep never ends.`, the 303 with `follow_redirects=False`), but a
user-story phase does not hand you the oracle — the planner must **derive** one.
Deriving a correct, complete acceptance check from a vague story is close to the
"galaxy-brain" work `LESSONS.md #1` warns against delegating, which is exactly
why it is assigned to the bigger-model planner and not the SLM implementer.
Whether the planner can derive oracles that are both correct and right-sized is
the central open question of this Part. It is a named, evidence-gated thread: the
planner ships only if measured runs show its derived oracles hold up against the
phases the SLM then implements. Until then it is a hypothesis under test, not a
foregone deliverable.

### Part IV — Keeping the SLM on track

Goal: the catalog of improvements, each a built-in Pi feature mapped to a lesson
and measured.

Candidate improvements (final set and order fixed in the Part IV sub-project
spec), each with its motivating lesson:
- Structural orientation via `before_agent_start` system-prompt injection — L5.
- Tool-surface restriction via `setActiveTools` — L6, L8.
- Context-scaled tool-output truncation — L8.
- Protected-path guard on `tool_call` — L8, L12.
- Repeated-failing-call circuit breaker on `tool_execution_*` — L1, L11.
- Turn cap on `turn_end` — L11. (Note the two soft edges the reference
  implementation documents: the effective bound is `maxTurns + 1`, and steer
  delivery cannot be confirmed through the public API — `clearSteeringQueue` is
  not on `ExtensionAPI`, so an undelivered correction is recorded as
  `delivered: "unknown"`. The chapter must state both rather than imply a hard
  cap and guaranteed delivery.)
- Model *selection* via `models.json`; **sampling tuning is not a `models.json`
  capability** — L10. The `models.json` schema exposes `contextWindow`,
  `maxTokens`, and `compat`, but not `temperature`/`top_p`/`top_k`. The lesson's
  low-entropy sampling (`temperature: 0.2`, etc.) is set **server-side in LM
  Studio / oMLX**, or injected per-request via a `before_provider_request`
  payload mutation. The chapter teaches whichever the target backend supports;
  it does not claim `models.json` carries sampling.
- Context budgeting and compaction settings (`compaction.reserveTokens`,
  `keepRecentTokens`, `enabled`) — L9.

The guardrails among these (output cap, path guard, repeat breaker, turn cap)
were already designed and implemented once against Pi in the prior repo. That
work is **reference material**, not a transplant: this course rebuilds them live,
chapter by chapter, so the reader constructs them. Reference:
`local-ai-gemma` branch `slm-guardrails` —
`docs/superpowers/specs/2026-07-22-slm-guardrails-design.md`,
`docs/superpowers/plans/2026-07-22-slm-guardrails.md`, and the implementation
under `.pi/extensions/slm-guardrails/` (75 passing tests). The design decisions,
adversarial-review findings (path-traversal bypass, bash false-positive), and
live-verification evidence in those documents are the raw material for the
corresponding chapters.

## Repository layout

```
local-ai-pi/
  README.md                      # course framing
  LESSONS.md                     # the lesson catalog Part IV cites, adapted to Pi
  docs/
    superpowers/                 # how the COURSE is built (the method, applied to itself)
      roadmap.md                 # cross-phase index: sequence, status, backlog
      specs/  plans/  briefs/    # per-phase design, implementation, task briefs
      research/                  # dated EVIDENCE reports (the smoking gun, before/afters)
      archive/{specs,plans}/     # shipped / superseded
      policies/                  # durable rules (evidence tiers, etc.)
    chapters/                    # the COURSE CONTENT the reader consumes (Sphinx + MyST)
    conf.py  index.md            # Sphinx config and root document
  examples/
    agentclinic/                 # the example workload (spec triple + app as it is built)
  .superpowers/sdd/              # SDD execution scratch (gitignored)
```

`docs/superpowers/` is the development record (how the course is built);
`docs/chapters/` is the product (what the reader reads). Keeping them separate is
deliberate: the evidence behind a chapter's claims lives in
`docs/superpowers/research/`, auditable and apart from the prose.

Docs toolchain matches Tainie: Sphinx 9 + `myst_parser` + `furo`, built to
`docs/_build/`.

## Method — built the way it teaches

The course is constructed spec-driven, roadmap-tracked, and evidence-gated, using
Superpowers. Each Part is a sub-project: brainstorm → design spec → plan →
subagent-driven implementation → evidence report. `roadmap.md` tracks sequence
and status; completed specs/plans move to `archive/`; every measured claim is
backed by a dated report in `research/` under the evidence policy in
`policies/evidence.md`.

Sub-project order (each is built before the next begins):

0. **Scaffold** (this hand-off): repo skeleton, docs toolchain, roadmap, this
   spec, LESSONS.md, the example spec triple, and Part I's hello-world.
1. **Part II — measurement**, including the baseline smoking-gun report. Built
   before Part III/IV because they cannot be evaluated without it.
2. **Part III — SDD and the subagent fleet.**
3. **Part IV — the improvements catalog.**

Part I is folded into the scaffold sub-project because it is small and every
later Part needs a working extension to build on.

## Success criteria (whole course)

1. A reader following the chapters ends with a working eval harness and a
   catalog of Pi-native steering techniques, each demonstrated on the same app.
2. Every "this helps" claim in the course links to a dated report in
   `research/` produced by the harness, not to prose assertion.
3. The out-of-the-box baseline (the ditch) and at least one improved run are
   both recorded and comparable.
4. Nothing in the course requires a forked or patched Pi.

## Out of scope

- Porting or teaching Tainie, Pyrefly, or any type-checker-in-the-loop.
- Transplanting the prior guardrails code or its git history.
- Merging or altering `local-ai-gemma`; its `slm-guardrails` branch stays as
  read-only reference.

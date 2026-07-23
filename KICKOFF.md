# KICKOFF — read this first in a fresh session

You are picking up construction of **local-ai-pi**, a course that teaches how to
keep a small local model (SLM) on track during real Python development under the
Pi agent harness, using only built-in Pi features. This file orients a fresh
Claude Code session so you can continue without the brainstorming history.

## What this repo is

Read, in order:

1. [`README.md`](README.md) — the course framing and the four-Part arc.
2. [`docs/superpowers/specs/2026-07-23-course-design.md`](docs/superpowers/specs/2026-07-23-course-design.md)
   — the master design: constraints, the four Parts, repo layout, method, and the
   sub-project sequence. This is the authority for *what the course is*.
3. [`docs/superpowers/roadmap.md`](docs/superpowers/roadmap.md) — sequence and
   status. It tells you which sub-project is next.
4. [`docs/superpowers/policies/evidence.md`](docs/superpowers/policies/evidence.md)
   — the evidence policy every measured claim must satisfy (GREEN/YELLOW/RED).

## The hard constraints (do not drift from these)

- **Built-in Pi only.** No forked Pi, no Pyrefly, no external type-checker, no
  bolt-on toolchain. If a chapter needs a mechanism, it must be one Pi ships.
- **Evidence-gated.** Show the failure with recorded telemetry before teaching
  the fix. A technique is kept only if a measured run shows it helps. The reader
  never adopts a technique on faith.
- **The example is fixed.** The SLM builds the AgentClinic FastAPI app from the
  spec triple in [`examples/agentclinic/specs/`](examples/agentclinic/specs/).
- **Built the way it teaches.** Use Superpowers: brainstorm each sub-project,
  write its spec and plan under `docs/superpowers/`, build it subagent-driven,
  and record evidence in `docs/superpowers/research/`. Move shipped specs/plans to
  `archive/`.

## Where things live

- `docs/chapters/` — the course content the reader consumes (Sphinx + MyST).
- `docs/superpowers/` — how the course is built (specs, plans, roadmap, research,
  archive, policies). Development record, separate from the product.
- `examples/agentclinic/` — the example workload.
- `.superpowers/sdd/` — SDD execution scratch (gitignored).

## What is done

- **SP0 — Scaffold + Part I.** Repo skeleton, docs toolchain (Sphinx 9 +
  myst-parser + furo), roadmap, evidence policy, the example spec triple,
  `docs/lessons.md`, and Part I's hello-world extension + chapter.
- **SP1 — Part II (Measurement).** Telemetry reader (`harness/telemetry.py`),
  disposable workspace provisioning (`harness/workspace.py`), eval session
  runner (`harness/session.py`), n=8 baseline loop (`harness/runner.py`).
  Three Part II chapters. The smoking-gun baseline report lives at
  `docs/superpowers/research/2026-07-23-baseline-phase-1.md` — **0/8 success**
  on Phase 1 alone, the ditch the rest of the course answers. Built against
  `omlx/gemma-4-12B-it-MLX-8bit` on oMLX (not LM Studio — see Environment).

## What is NOT done

- Parts III, IV are unbuilt. Part III (SDD on Pi) is **next** and unblocked
  now that SP1's harness and baseline exist.

## Key design decision already made: how Pi subagents work

Part III depends on this; the master spec's "Part III" section has the full
version. **Important correction from the SP2 review (2026-07-23):** the master
spec frames a Pi subagent as something you build from scratch ("Pi has no
native subagent; a subagent is a composition you own"). That is *technically*
true — there is no runtime subagent primitive — but *pedagogically misleading*:
**Pi ships a complete subagent extension** in its examples directory at
`examples/extensions/subagent/` (in the installed package under
`@earendil-works/pi-coding-agent/examples/extensions/subagent/`).

The shipped `subagent` extension already provides everything SP2's brainstormed
design proposed to build from scratch and more: a registered `subagent` tool,
`agents/<name>.md` specialist discovery (frontmatter: `name`, `description`,
`tools`, `model` + system-prompt body), single/parallel/chain delegation modes,
streaming output, usage/cost tracking, and a security model for project-local
agents. A reader who `pi install`s it has the full mechanism.

So the course's Part III contribution is **not** "rebuild the extension in
TypeScript" — that would violate the "built-in Pi only" spirit and waste the
reader's time. The real deliverables are:

1. **Study and install** the shipped subagent example (Chapter 1 dissects
   `index.ts`/`agents.ts` to teach the mechanism).
2. **Author an `implementer` specialist** (`.pi/agents/implementer.md`) for the
   AgentClinic workload — the packet format, restricted tools, system prompt.
3. **Author the parent/orchestrator system prompt** that teaches the SLM to
   extract phases from the roadmap and construct tight packets.
4. **Measure** whether this shape beats the SP1 0/8 baseline.

Two consequences of the mechanism still hold (and the course teaches both):
the child is a full pi process so it **inherits the project's guardrail
extensions** (the permission enforcement OpenCode gave declaratively — from
inside the child, not asserted over it; demonstrated in a Part IV chapter where
the guardrails exist); and from the parent a delegation is just a **tool call**,
so every Part IV guardrail governs it. The reserved "galaxy-brain" role is a
**planner** specialist on a bigger model — a hybrid deterministic+model
tool-agent that turns business/user-story phases into right-sized packets and
derives their acceptance oracles. Oracle derivation is the central
evidence-gated research thread of Part III.

## Reference material (read-only, in a sibling repo)

The four guardrails in Part IV were already designed and implemented once against
Pi, in `../local-ai-gemma` on branch `slm-guardrails`. **Do not transplant that
code or its history** — Part IV rebuilds it live so the reader constructs it. Use
these as source material when you reach Part IV:

- `../local-ai-gemma/docs/superpowers/specs/2026-07-22-slm-guardrails-design.md`
  — the design, including the adversarial-review findings (path-traversal bypass,
  bash false-positive) and the live-verification results against
  `gemma-4-12b-it-mlx`.
- `../local-ai-gemma/docs/superpowers/plans/2026-07-22-slm-guardrails.md` — the
  7-task implementation plan (config → ledger → output-cap → path-guard →
  repeat-breaker+turn-cap → wiring → live verification).
- `../local-ai-gemma/.pi/extensions/slm-guardrails/` — the implementation, 75
  passing tests, runnable with `node --test` from that directory.

Also useful, as inspiration only (not a dependency): the Tainie eval driver at
`~/projects/t-strings/tainie/src/tainie/eval/` shows the shape of an eval
"session" (provision workspace → run headless → reduce to a result). This course
reimplements a minimal version and shares none of Tainie's type-checker
machinery.

## Environment notes (verified 2026-07-23, updated for oMLX)

- **Use the globally-installed `pi`, never the source checkout.** The runtime is
  the `pi` on PATH (`/Users/pauleveritt/.volta/bin/pi`, an installed release,
  0.81.1) — the same thing a reader following the course would run. The checkout
  at `~/PycharmProjects/pi` is **read-only source** for verifying mechanics
  (cite `file:line` from it when explaining how something works); it is not the
  runtime. Do not run pi from sources, `npm link`, or `pi-test.sh` the checkout,
  and do not rely on behavior only present there. If a mechanism is not in the
  installed release, record it as a finding — do not build a local pi to make it
  work.
- **oMLX serves the model, not LM Studio.** The course moved from LM Studio to
  oMLX during SP1. The server runs on `http://127.0.0.1:8001/v1` with the shared
  secret API key `not-needed` (passed as `Authorization: Bearer not-needed`).
  The model is `gemma-4-12B-it-MLX-8bit` (contextWindow 262144), registered in
  `~/.pi/agent/models.json` under provider `omlx`. Invoke as
  `--model omlx/gemma-4-12B-it-MLX-8bit`. The LM Studio entry in `models.json`
  still exists but is unused. Always run headless pi with `< /dev/null` to avoid
  the never-EOF stdin startup hang.
- Node 25.8.1 strips TypeScript types natively; the prior guardrails suite runs
  under `node --test` with no packages installed. Relative imports must use
  explicit `.ts` extensions.

## How to start

1. `git log --oneline` to confirm current state. SP0 and SP1 are done; SP2 is
   next.
2. **SP2 — Part III (SDD on Pi).** Invoke the brainstorming skill for
   sub-project 2. The design is reframed around the *shipped* Pi subagent
   example (see "Key design decision" above) — the course specializes it rather
   than rebuilding it. If the Superpowers skills are unavailable in your session,
   follow the same shape by hand: brainstorm a spec into
   `docs/superpowers/specs/`, write a plan into `plans/`, build it, and record
   evidence in `research/`.
3. Follow the master spec's sub-project order. Keep the roadmap current, and move
   shipped specs/plans to `archive/`.

## Design decisions already resolved (do not re-litigate)

A deep review (Fable, 2026-07-23) checked the design against Pi source and these
were settled:

- **Guardrail inheritance is a forward promise in Part III.** Part III teaches the
  subagent mechanism and parent-side governance; the "child inherits the
  guardrails" demonstration happens in a Part IV chapter where the guardrails
  actually exist. Inheritance is also project-*global*, not per-specialist — do
  not claim OpenCode's per-role permission parity.
- **`models.json` does not carry sampling params.** `temperature`/`top_p`/`top_k`
  are server-side (LM Studio/oMLX) or a `before_provider_request` payload
  mutation. `models.json` is for model selection, context window, and `compat`.
- **The app is fixed; the phase framing evolves.** Most chapters use the existing
  overly-detailed roadmap. Later chapters bring in a higher-level roadmap consumed
  by the planner tool-agent. Both target the same AgentClinic app.
- **The planner is evidence-gated, not a promised deliverable.** The plain
  Part III deliverables are the `implementer` specialist and the
  parent-as-orchestrator system prompt (there is no separate orchestrator
  subagent — that framing predates the reframe around the shipped example).
- **Squash-merge feature branches.** When a sub-project is complete, squash-merge
  the feature branch to `main` with a single commit (`SP<N>: <title>`) that
  summarizes the sub-project. This keeps `main` clean — one commit per
  sub-project — and matches Superpowers' finish-and-close workflow.

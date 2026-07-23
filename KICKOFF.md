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

## What is already done (sub-project 0, this hand-off)

- Repo skeleton, `.gitignore`, docs toolchain (`docs/conf.py`, `pyproject.toml`
  docs group), `docs/index.md`, `docs/chapters/index.md`.
- Master course design spec, roadmap, evidence policy.
- The example spec triple, copied into `examples/agentclinic/specs/`.
- `LESSONS.md`, copied from the prior course. **Caveat:** it still carries
  OpenCode-specific framing (`.opencode/`, `/phase`, `implementer1a`,
  provider names). Adapting it to Pi is course work, not done yet — treat it as
  raw source material for the lesson catalog Part IV cites, and give it a Pi pass
  when Part IV is built (or as a small dedicated task if you prefer).

## What is NOT done

- **Part I's hello-world extension is not written yet.** The scaffold sub-project
  includes it; it is the first thing to build. A minimal `.pi/extensions/`
  hello-world (e.g. `session_start` → `ctx.ui.notify`, plus an `appendEntry`
  showing how evidence gets written) with a chapter under `docs/chapters/`.
- Parts II, III, IV are unbuilt. Part II (Measurement) is **next** and is
  load-bearing — build it before III/IV, because they cannot be evaluated without
  its harness and baseline.

## Key design decision already made: how Pi subagents work

Part III depends on this; the master spec's "Part III" section has the full
version. In short: Pi has **no native subagent**. A subagent is a composition you
own — a registered tool whose `execute` spawns a child `pi --mode json` process
(the mechanism, TypeScript) plus an `agents/<name>.md` file (the specialist,
data). Think of a subagent as *a tool you wrote that happens to spawn another
agent*, not a config the runtime interprets. Two consequences: the child is a
full pi process so it **inherits the project's guardrail extensions** (this is
how you get the permission enforcement OpenCode gave declaratively — from inside
the child, not asserted over it); and from the parent a delegation is just a
**tool call**, so every Part IV guardrail governs it. The reserved "galaxy-brain"
role is a **planner** specialist on a bigger model — a hybrid deterministic+model
tool-agent that turns business/user-story phases into right-sized packets and
derives their acceptance oracles. Oracle derivation is the central evidence-gated
research thread of Part III.

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

## Environment notes (verified 2026-07-23)

- **Use the globally-installed `pi`, never the source checkout.** The runtime is
  the `pi` on PATH (`/Users/pauleveritt/.volta/bin/pi`, an installed release,
  0.81.1) — the same thing a reader following the course would run. The checkout
  at `~/PycharmProjects/pi` is **read-only source** for verifying mechanics
  (cite `file:line` from it when explaining how something works); it is not the
  runtime. Do not run pi from sources, `npm link`, or `pi-test.sh` the checkout,
  and do not rely on behavior only present there. If a mechanism is not in the
  installed release, record it as a finding — do not build a local pi to make it
  work.
- LM Studio serves `gemma-4-12b-it-mlx` on
  `localhost:1234`; a provider entry for it exists at `~/.pi/agent/models.json`
  (provider `lmstudio`, contextWindow 40960). Always run headless pi with
  `< /dev/null` to avoid the never-EOF stdin startup hang, and pass
  `--model lmstudio/gemma-4-12b-it-mlx` explicitly (pi's default provider is a
  different one).
- Node 25.8.1 strips TypeScript types natively; the prior guardrails suite runs
  under `node --test` with no packages installed. Relative imports must use
  explicit `.ts` extensions.

## How to start

1. `git log --oneline` to confirm current state. SP0 is done; SP1 is next.
2. **SP1 — Part II (Measurement).** Invoke the brainstorming skill for
   sub-project 1. If the Superpowers skills are unavailable in your session,
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
- **The planner is evidence-gated, not a promised deliverable.** Only the
  orchestrator subagent is a plain Part III deliverable.
- **Squash-merge feature branches.** When a sub-project is complete, squash-merge
  the feature branch to `main` with a single commit (`SP<N>: <title>`) that
  summarizes the sub-project. This keeps `main` clean — one commit per
  sub-project — and matches Superpowers' finish-and-close workflow.

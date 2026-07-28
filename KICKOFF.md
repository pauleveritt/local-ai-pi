# KICKOFF — read this first in a fresh session

You are picking up construction of **local-ai-pi**, a course that teaches how to
keep a small local model (SLM) on track during real Python development under the
Pi agent harness, using only built-in Pi features. This file orients a fresh
session; it does not carry current status — that lives in one place only (see
below), so this file can't go stale the way it did before.

## What this repo is — read, in order

1. [`README.md`](README.md) — the course framing.
2. [`docs/superpowers/specs/2026-07-23-course-design.md`](docs/superpowers/specs/2026-07-23-course-design.md)
   — the master design: constraints, the four Parts, repo layout, method. The
   authority for *what the course is*, not for *what's currently true* — some
   of its specifics (e.g. the original repo-layout diagram) have been
   superseded by later decisions; those supersessions are noted inline where
   they occur.
3. **[`docs/superpowers/roadmap.md`](docs/superpowers/roadmap.md) — the only
   source of current status.** Sequence, what's done, what's blocked, what's
   next, and why. Its "Next action" banner is kept current; nothing in this
   file duplicates it. If this file and the roadmap ever disagree on status,
   the roadmap is right.
4. [`docs/superpowers/policies/evidence.md`](docs/superpowers/policies/evidence.md)
   — the evidence policy every measured claim must satisfy (GREEN/YELLOW/RED
   tiers, and the numbered Rules — Rule 7 in particular governs what a chapter
   is allowed to claim from a batch of runs).

**Why status lives in exactly one place:** an earlier version of this file
carried its own "What is done" / "What is NOT done" sections describing a
specific SP-by-SP baseline. Those numbers were superseded by a grading-path
rebuild (the oracle was found to accept broken solutions; see the roadmap's
"Consequences" note) and this file was not updated — a fresh session reading
it first would have repeated a fixed mistake. Do not reintroduce a second
status section here. If you need current status, read the roadmap.

## The hard constraints (do not drift from these)

- **Built-in Pi only.** No forked Pi, no Pyrefly, no external type-checker, no
  bolt-on toolchain. If a chapter needs a mechanism, it must be one Pi ships.
- **Evidence-gated.** Show the failure with recorded telemetry before teaching
  the fix. A technique is kept only if a measured run shows it helps. The reader
  never adopts a technique on faith.
- **The example app is fixed; the phase framing evolves.** The SLM builds the
  same AgentClinic FastAPI app throughout. Most chapters use the existing
  detailed roadmap; later chapters introduce a higher-level, business/user-story
  variant targeting the identical app — see
  `examples/agentclinic/specs/roadmap-user-story.md` once it exists.
- **Built the way it teaches.** Use Superpowers: brainstorm each sub-project,
  write its spec and plan under `docs/superpowers/`, build it subagent-driven,
  and record evidence in `docs/section-*/research/`. Move shipped/superseded
  specs and plans to `docs/superpowers/archive/{specs,plans}/`.

## Where things live

- `docs/section-*/` — the course content the reader consumes (Sphinx + MyST).
  Each section lives in its own directory with co-located spec, plan, and
  research evidence.
- `docs/superpowers/` — cross-cutting development record: roadmap, policies,
  cross-phase specs/plans, `archive/` for superseded ones.
- `harness/` — the eval harness (telemetry reader, workspace provisioning,
  session runner, grading). `scripts/` holds the runnable batch/scout drivers.
- `examples/agentclinic/` — the example workload (spec triple + app).
- `.superpowers/sdd/` — SDD execution scratch (gitignored).

## How Pi subagents actually work (stable technical background, not status)

Relevant once you're working in Section III territory. The master spec's
original framing described a subagent as something built from scratch. In
reality **Pi ships a complete subagent extension** in its examples directory
(`examples/extensions/subagent/` in the installed package, under
`@earendil-works/pi-coding-agent/`). It provides: a registered `subagent` tool,
`agents/<name>.md` specialist discovery (frontmatter: `name`, `description`,
`tools`, `model` + system-prompt body), single/parallel/chain delegation,
streaming output, usage/cost tracking, and a security model for project-local
agents (`agentScope: "both"` is required for project-local `.pi/agents/`
discovery — the default `"user"` scope will not find them).

The course's contribution is specialization, not reimplementation: an
`implementer` specialist (`.pi/agents/implementer.md`) and a parent
orchestrator system prompt (`prompts/orchestrator.md`, deliberately kept out of
`.pi/agents/` so it can't be self-delegated to). A planner specialist that
derives acceptance oracles from higher-level phase descriptions is a reserved,
evidence-gated idea, not a built deliverable — check the roadmap's backlog for
its current status before assuming it exists.

Two structural points still hold regardless of current phase: the child is a
full `pi` process, so it inherits whatever guardrail extensions the project
ships (enforced from inside the child, not asserted over it — demonstrated
once a Part IV chapter exists to demonstrate it against); and from the parent,
a delegation is just a tool call, so any guardrail hooking `tool_call` governs
it.

## Reference material (read-only, in a sibling repo)

A prior spike designed and implemented four SLM guardrails against Pi, in
`../local-ai-gemma` on branch `slm-guardrails`. **Do not transplant that code
or its history** — this course rebuilds live so the reader constructs it. Use
as source material once Section IV work resumes — check the roadmap for
Section IV's current subject/mechanism first, since it may no longer be these
same four (the original catalog targeted a baseline this project's own
grading-path rebuild later superseded):

- `../local-ai-gemma/docs/superpowers/specs/2026-07-22-slm-guardrails-design.md`
  — the design, including adversarial-review findings and live-verification
  results against `gemma-4-12b-it-mlx`.
- `../local-ai-gemma/docs/superpowers/plans/2026-07-22-slm-guardrails.md` — the
  7-task implementation plan.
- `../local-ai-gemma/.pi/extensions/slm-guardrails/` — the implementation, 75
  passing tests, runnable with `node --test` from that directory.

Also useful as inspiration only (not a dependency): the Tainie eval driver at
`~/projects/t-strings/tainie/src/tainie/eval/` shows the shape of an eval
"session." This course reimplements a minimal version and shares none of its
type-checker machinery.

## Environment notes

- **Use the globally-installed `pi`, never the source checkout.** The runtime
  is the `pi` on PATH (`/Users/pauleveritt/.volta/bin/pi`, an installed
  release — check `pi --version`, it drifts; 0.82.0 as of 2026-07-28). The
  checkout at `~/PycharmProjects/pi` is **read-only source** for verifying
  mechanics (cite `file:line` from it); it is never the runtime. Do not run
  `pi` from sources, `npm link`, or `pi-test.sh` the checkout, and do not rely
  on behavior only present there — if a mechanism the course teaches isn't in
  the installed release, that's a finding, not a thing to work around with a
  local build.
- **oMLX serves the model, not LM Studio.** Server at
  `http://127.0.0.1:8001/v1`, shared secret `not-needed`. Model
  `gemma-4-12B-it-MLX-8bit` (contextWindow 262144), registered in
  `~/.pi/agent/models.json` under provider `omlx`. Invoke as
  `--model omlx/gemma-4-12B-it-MLX-8bit`. Always run headless pi with
  `< /dev/null` to avoid the never-EOF stdin startup hang.
- Node 25.8.1 strips TypeScript types natively; the guardrails reference repo's
  suite runs under `node --test` with no packages installed. Relative imports
  must use explicit `.ts` extensions.
- **Batch durability.** A long `run_baseline` batch (n=16, up to 900s/run) can
  be killed by session teardown or a hang; `run_baseline` supports a
  `checkpoint_path` that persists each completed `SessionResult` so a killed
  batch resumes rather than restarts. Use it for anything beyond a quick n=4
  scout — see `scripts/scout.py` / `scripts/steered_scout.py` for the pattern.

## How to start

1. Read `docs/superpowers/roadmap.md`'s "Next action" banner. That is the
   current phase, what's blocking it, and what's next — this file
   intentionally does not restate it.
2. `git log --oneline` and `git status` to confirm you're on the branch the
   roadmap describes (development happens on feature branches; check which
   one the roadmap's "Next action" banner assumes before making changes).
3. If the next step is genuinely new design work (a new chapter's mechanism, a
   sub-project not yet brainstormed), invoke the brainstorming skill rather
   than assuming a design from this file or from memory of a prior session.

## Design decisions still standing (do not re-litigate without new evidence)

- **Guardrail inheritance is a forward promise until a Part IV chapter exists
  to demonstrate it.** Inheritance is project-*global*, not per-specialist —
  do not claim OpenCode's per-role permission parity.
- **`models.json` does not carry sampling params.** `temperature`/`top_p`/`top_k`
  are server-side or a `before_provider_request` payload mutation.
  `models.json` is for model selection, context window, and `compat`.
- **The app is fixed; the phase framing evolves.** Most chapters use the
  existing detailed roadmap; a higher-level, business/user-story variant is
  introduced later, targeting the same app.
- **Squash-merge feature branches at completion.** When a sub-project is
  complete, squash-merge to `main` with a commit summarizing it. Individual
  commits during the work itself are expected and fine — this convention
  governs the merge, not the working history.

Anything not listed here as "standing" — specific pass/fail numbers, which
sub-project is next, which chapters exist — is status, and status lives in the
roadmap, not here.

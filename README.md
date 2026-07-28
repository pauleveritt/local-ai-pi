# Keeping a Small Local Model On Track — with Pi

A course teaching how to keep a small local model (SLM) on track while it does
real Python development, using the [Pi agent harness](https://pi.dev) and
**only built-in Pi features** — no forks and no bolt-on toolchains.

The spine of the course is: **teach evals, then progressively adopt built-in Pi
features, each one motivated by a specific lesson and validated by a measured
run.** Every improvement is a built-in Pi capability introduced to solve a
documented failure and proven by a before/after measurement.

**The reader never adopts a technique on faith.** Each part first shows the
failure with recorded telemetry, then applies one Pi mechanism, then measures
whether it actually helped. Techniques that do not move a metric are not kept.

## The arc

1. **Part I — Pi extension basics.** A hello-world extension and the event
   lifecycle in miniature: enough to read and hook the agent loop.
2. **Part II — Measurement (the smoking gun).** Read telemetry from
   `pi --mode json` and session JSONL, build a minimal eval harness, and run the
   out-of-the-box baseline that shows an SLM driving a real Python task into the
   ditch. This part is load-bearing: nothing later can claim an improvement
   without it.
3. **Part III — Spec-driven development on Pi.** The roadmap-and-packet method,
   a parent-as-orchestrator system prompt, an implementer specialist, and — only
   where the evidence supports it — a fleet of additional specialists.
4. **Part IV — Keeping the SLM on track.** The improvements, each a built-in Pi
   feature answering a documented lesson and measured with Part II's harness:
   structural orientation, tool restriction, output caps, path guards, a
   repeated-failure circuit breaker, a turn cap, model tuning, and context
   budgeting.

## The example workload

Throughout, the SLM builds the same small FastAPI application — the AgentClinic
complaints board — as a sequence of spec-driven phases. The app is deliberately
trivial; the point is the *steering*, not the app.

## Built the way it teaches

This course was itself written with [Superpowers](https://github.com/obra/superpowers)
spec-driven development, and the whole paper trail is in the repository.

Development is broken into a roadmap of **feature cycles**. Each cycle runs the
same loop — brainstorm a design, write a plan, implement it task by task,
verify, and record what actually happened — and each leaves the same artifacts
behind:

| Artifact | Where | What it is |
|---|---|---|
| **Roadmap** | [`docs/superpowers/roadmap.md`](docs/superpowers/roadmap.md) | The cross-cycle index: sequence, status, and a backlog whose items are held to a recurrence bar rather than scheduled because a neighbor shipped. |
| **Specs** | [`docs/superpowers/specs/`](docs/superpowers/specs/) | What each cycle builds and why, settled before any code exists — starting with the [master course design](docs/superpowers/specs/2026-07-23-course-design.md). |
| **Plans** | [`docs/superpowers/plans/`](docs/superpowers/plans/) | The work decomposed into small, individually testable tasks. |
| **Evidence** | [`docs/superpowers/research/`](docs/superpowers/research/) | Dated reports from real runs, with the raw session transcripts they were derived from. |
| **Policy** | [`docs/superpowers/policies/evidence.md`](docs/superpowers/policies/evidence.md) | The GREEN/YELLOW/RED tiers that decide what the course is allowed to assert. |

Nothing here is reconstructed after the fact. The specs were written before the
code, the reviews are recorded with the defects they caught, and no claim in the
chapters is allowed to outrun its artifact.

### Start from the beginning and build your own

Because every cycle is on disk and in the commit history, you can work through
this repository as a worked example rather than just reading its output:

- **Start at [`KICKOFF.md`](KICKOFF.md)** — the handoff document that seeded the
  project. It was extracted from the previous project's findings and is the
  single file a fresh agent session reads to pick up the work. Reading it first
  shows you what a project needs to have decided before implementation begins.
- **Follow the roadmap in order.** Each cycle's spec explains the reasoning,
  its plan shows the decomposition, and its commits show what actually landed —
  including the corrections. The reviews that caught real defects are part of
  the record.
- **Then fork the method, not the content.** The loop is
  brainstorm → spec → plan → implement → verify → record, with a roadmap
  tracking status and a backlog holding un-triggered work. None of that is
  specific to small local models or to Pi. Point it at your own project and the
  artifacts will look the same.

[How This Was Built](docs/how-this-was-built.md) covers the lineage and which
model tiers did which work.

## Reading the course

The chapters live under [`docs/`](docs/), one directory per section
(`section-1-hello-agent/`, `section-2-measurement/`, etc.), and are built with
Sphinx + MyST. The [evidence policy](docs/superpowers/policies/evidence.md) — the
GREEN/YELLOW/RED tiers every measured claim in the course must satisfy — governs
what the course is allowed to assert.

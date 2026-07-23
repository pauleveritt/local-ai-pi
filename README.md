# Keeping a Small Local Model On Track — with Pi

A course teaching how to keep a small local model (SLM) on track while it does
real Python development, using the [Pi agent harness](https://pi.dev) and
**only built-in Pi features** — no forks, no external type-checkers, no bolt-on
toolchains.

The spine of the course is: **teach evals, then progressively adopt built-in Pi
features, each one motivated by a specific lesson and validated by a measured
run.** Every improvement is a built-in Pi capability introduced to solve a
documented failure, and proven by a before/after measurement.

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
   an orchestrator subagent, and — only where the evidence supports it — a fleet
   of specialized subagents (planner, implementer, verifier).
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

This repository is itself spec-driven, roadmap-tracked, and evidence-gated.
[`docs/superpowers/roadmap.md`](docs/superpowers/roadmap.md) is the live index of
the course's own construction, and [`docs/superpowers/research/`](docs/superpowers/research/)
holds the dated evidence reports — including the baseline that motivates the
whole course. If you want to see the method the course teaches, read how the
course was built.

## Reading the course

The chapters live under [`docs/chapters/`](docs/chapters/) and are built with
Sphinx + MyST. See [CONTRIBUTING](docs/superpowers/policies/evidence.md) for the
evidence policy every measured claim in the course must satisfy.

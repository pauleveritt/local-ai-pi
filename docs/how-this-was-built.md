# How This Was Built

This course argues that you should not adopt a technique on faith — so it owes
you an account of its own construction. This page is that account: where the
material came from, how the writing is organized, and which models did which
work.

## Where it came from

The lineage runs backwards through two earlier efforts.

**The DeepLearning.AI course, plus a lot of local-agent experimentation.** The
starting point was not a plan but a pile of observations: running small local
models against real coding tasks, watching them stall, loop, and confidently
ship broken edits. Most of what became the lesson catalog started as notes from
runs that went wrong.

**[`local-ai-gemma`](https://github.com/pauleveritt/local-ai-gemma) — the
previous project.** Those experiments were consolidated into a teaching repo
built on the OpenCode harness, driving Gemma 4 12B through a spec-driven
roadmap. It produced [`lessons.md`](lessons.md): seventeen lessons ranked by demonstrated
impact, each traceable to session telemetry rather than intuition. It also
produced the failures this course exists to answer — the 27 stale edit anchors,
the recursive listing that poisoned a context window, the child that burned its
whole step budget in retry loops.

**This repository** is the successor, rebuilt on the [Pi agent
harness](https://pi.dev). The change of harness is not cosmetic. OpenCode gave
declarative subagents with permission blocks; Pi gives an event lifecycle and
extensions you write yourself. That difference is most of the curriculum.

The `local-ai-gemma` work is carried forward as *reference material*, not as
transplanted code. Where this course rebuilds something that already exists
there — the guardrails in Part IV, for instance — it rebuilds it live, chapter
by chapter, so the reader constructs it rather than inherits it.

## How the writing is organized

The course is built with [Superpowers](https://github.com/obra/superpowers)
spec-driven development. Development is broken into a roadmap of feature
cycles, and each cycle carries the same artifacts:

1. A **design spec** in `docs/superpowers/specs/` — what is being built and why,
   settled before any code exists.
2. An **implementation plan** in `docs/superpowers/plans/` — the work decomposed
   into small, individually testable tasks.
3. **Evidence** in `docs/superpowers/research/` — dated reports from real runs.

[`docs/superpowers/roadmap.md`](superpowers/roadmap.md) is the cross-cycle
index: sequence, status, and links. Items sit in its backlog held to a
recurrence bar rather than scheduled because a neighbor shipped.

This is the same method the course teaches, applied to the course itself. If you
want to see spec-driven development with an evidence gate in practice, read
`docs/superpowers/` rather than taking the chapters' word for it.

## Which models did what

The work is split across model tiers by what each tier is actually good at —
which is itself one of the course's lessons.

**Opus** extracted the kickoff document from the previous project. That step was
mostly reading: working through the Pi source to establish what the extension
API can and cannot do, reconciling it against `LESSONS.md`, and writing a
handoff a fresh session could execute from. The load-bearing work was noticing
what *wasn't* there — for example, that a tool call rejected by schema
validation never reaches the `tool_result` event, so a circuit breaker wired
there would be blind to the exact failure it was built for.

**Pi with DeepSeek v4 Pro** does the implementation, following the plans
task by task.

**GLM 5.2** does verification, reviewing the work against its spec.

The division is deliberate and matches `LESSONS.md #3`: a stronger model settles
the design and writes the contract; a cheaper model executes it; an independent
checker decides whether it worked. A plan detailed enough to remove decisions
from the implementer is what makes the cheaper tier viable — plan quality and
model tier are coupled, and you cannot economize on both at once.

## The Pi configuration

Model routing lives in Pi's user-global model registry at
`~/.pi/agent/models.json`, not in this repository — a reader following along
supplies their own. Two providers are configured:

- **`omlx`** — local models served by [oMLX](https://pi.dev) on
  `http://127.0.0.1:8001/v1`, including `gemma-4-12B-it-MLX-8bit`, the
  small-local-model subject of the course, plus Ornith, Qwen3-Coder, and Mellum2
  variants used for comparison.
- **`openrouter-curated`** — hosted models including GLM 5.2 and Kimi K3, used
  for the verification and heavier reasoning roles.

Each entry declares its `contextWindow` and `maxTokens`, which matter more than
they look: several course techniques scale their behavior to the model's
declared context window, and an inaccurate value silently miscomputes them.

Two notes for anyone reproducing this setup. Sampling parameters
(`temperature`, `top_p`, `top_k`) are **not** part of `models.json` — that
schema covers model selection, context window, and compatibility flags only.
Low-entropy sampling is configured server-side in LM Studio or oMLX. And the
course runs the **globally installed `pi` binary**, never a source checkout; a
mechanism absent from the released version is recorded as a finding, not worked
around with a local build.

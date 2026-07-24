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

## What the method actually caught

The model split above is not just a cost optimization; it turned out to be the
single most productive part of the process, and the evidence is uncomfortable.

**Every adversarial review round, run by a different model than the one that
wrote the work, found defects the author had missed** — including defects in
work that had just been reviewed by its own author:

- a spec review found the central guardrail wired to an event that
  structurally cannot observe the failure it was built for;
- a task review found a path-traversal bypass in code that had passed its
  implementer's self-review;
- a whole-branch review found a guard that blocked the project's own test
  command — a false positive that would have aborted legitimate runs;
- a deep review found two live defeats of an oracle that had been hardened
  hours earlier, and named the reason: every fix so far had blacklisted an
  open category rather than closing it.

The pattern holds in the other direction too. A forensic replay corrected an
amendment written by the same assistant a few hours before, and several of the
fabricated metrics catalogued in this project were produced by its own
automation and passed its own checks.

This is now a rule rather than an observation: evidence policy
[Rule 8](superpowers/policies/evidence.md#rules) requires cross-model review
before any gate on the grading path, the acceptance suites, or measurement
code can pass.

The durable finding: **self-review is not a substitute for review by a
different model, and an author's confidence carries no information about
whether the work is correct.** Where a claim mattered, it was verified by
execution — reproducing a defeat, running a mutation test, replaying an
artifact — not by reading. That discipline, not any individual model's
capability, is what kept the evidence chain honest.

## The Pi configuration

Model routing lives in Pi's user-global model registry at
`~/.pi/agent/models.json`, not in this repository — a reader following along
supplies their own. Two providers are configured:

- **`omlx`** — local models served by [oMLX](https://pi.dev) on
  `http://127.0.0.1:8001/v1`. Six models are registered:

  | Model ID | Context Window | Max Tokens | Reasoning |
  |----------|---------------|------------|-----------|
  | `gemma-4-12B-it-MLX-8bit` | 262,144 | 8,192 | No |
  | `Ornith-1.0-9B-8bit` | 40,000 | 32,000 | Yes |
  | `Ornith-1.0-35B-8bit` | 80,000 | 32,000 | Yes |
  | `mlx-community--Qwen3-Coder-30B-A3B-Instruct-4bit` | 262,144 | 16,384 | No |
  | `mellum2-mlx-q8` | 32,000 | 32,000 | No |
  | `mellum2-thinking-mlx-q8` | 40,960 | 32,000 | Yes |

  Gemma 4 12B IT (8-bit MLX quantized) is the primary small-local-model subject
  of the course. Ornith, Qwen3-Coder, and Mellum2 variants are used for
  comparison runs and as the implementation tier on heavier phases.
- **`openrouter-curated`** — hosted models including GLM 5.2 and Kimi K3, used
  for the verification and heavier reasoning roles.

Each entry declares its `contextWindow` and `maxTokens`, which matter more than
they look: several course techniques scale their behavior to the model's
declared context window, and an inaccurate value silently miscomputes them.

## Local development environment

The repository is tooled for a single-developer workflow on macOS. Every
operation runs through `uv` and the `Justfile`; there is no `Makefile`,
`tox`, or `pip` invocation anywhere.

### Python toolchain: uv + Ruff + PyRefly

**[uv](https://docs.astral.sh/uv/)** manages the virtual environment and all
Python tooling. A single `uv sync` installs the docs dependency group. There
is no application runtime dependency list — the harness, tests, and docs
scripts import only the standard library plus `pytest`. Everything else is a
dev-time tool.

**[Ruff](https://docs.astral.sh/ruff/)** handles linting and formatting.
`just lint`, `just fmt-check`, and `just quality` gate every commit.

**[PyRefly](https://pyrefly.org)** is the type checker, run manually:

```bash
rtk err pyrefly check
```

It is wrapped through RTK for compact output (pyrefly has no native RTK
filter, so the `err` subcommand strips ANSI and progress-bar noise).

### Task runner: Justfile

The [`Justfile`](https://github.com/casey/just) at the repo root collects
every repeatable operation:

| Command | What it does |
|---------|-------------|
| `just install` | `uv sync` |
| `just docs` | Build Sphinx HTML |
| `just docs-live` | Auto-reload docs server, opens Firefox |
| `just lint` / `just fmt-check` | Ruff check / format check |
| `just quality` | Both lint and format check |
| `just test` | `uv run pytest` (passes args through) |
| `just clean` | Remove all build artifacts |

### Documentation: Sphinx + MyST + Furo

The docs are written in **[MyST](https://myst-parser.readthedocs.io/)**
(Markdown flavored with Sphinx directives), built by
**[Sphinx](https://www.sphinx-doc.org/)** 9.x, and themed with
**[Furo](https://pradyunsg.me/furo/)**. `sphinx-autobuild` provides
live-reload during writing.

Dependencies are pinned in `pyproject.toml` under the `[dependency-groups]
docs` key:

```toml
[dependency-groups]
docs = [
    "sphinx>=9.1.0",
    "furo>=2025.12.19",
    "myst-parser>=5.0.0",
    "sphinx-autobuild>=2025.8.25",
]
```

### Pi configuration

Pi's global settings live in `~/.pi/agent/settings.json`:

```json
{
  "compaction": { "enabled": true, "reserveTokens": 16384 },
  "defaultProvider": "deepseek",
  "defaultModel": "deepseek-v4-pro",
  "defaultThinkingLevel": "high",
  "theme": "dark"
}
```

Two packages are installed globally and active in every Pi session:

- **`git:github.com/obra/superpowers`** — the [Superpowers](https://github.com/obra/superpowers)
  skill library (brainstorming, writing plans, TDD, systematic debugging,
  code review, git worktrees, verification-before-completion). The course
  itself is built with Superpowers; the repo's `docs/superpowers/` directory
  follows its spec-plan-evidence pattern.
- **`npm:@upstash/context7-pi`** — the [Context7](https://context7.com)
  documentation lookup package. Resolves library IDs and fetches up-to-date
  API docs and code examples directly in-session. The Pi builds all of Part III
  and IV using it for current FastAPI, Jinja2, and pytest signatures rather
  than relying on training-data recall.

Custom skills live in `~/.agents/skills/` (registered via the `"skills"`
setting above). Currently: `arxiv-search` for paper lookups.

Two project-local extensions sit in the repo's `.pi/extensions/`:

- **`hello-world.ts`** — the minimal Pi extension the reader builds in
  Section I. It registers one tool and is the only extension whitelisted
  during eval harness runs (via `--extension` with `--no-extensions`).
- **`rtk.ts`** — transparently rewrites shell commands through
  [RTK](https://github.com/rtk/rtk), a Rust CLI proxy that strips token
  noise from verbose dev tools (pytest, ruff, uv, git). Most commands
  are auto-rewritten; `rtk gain` and `rtk discover` surface savings
  analytics. The extension ensures this happens inside Pi sessions
  without the user prefixing every command.

These two extensions do not overlap. `hello-world.ts` is the course object;
`rtk.ts` is the development accelerator. The eval harness explicitly loads the
former and excludes the latter so measurement runs are not contaminated by
the RTK rewrite layer.

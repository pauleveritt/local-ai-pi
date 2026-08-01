# Keeping a Small Local Model On Track — with Pi

This project investigates, measures, and teaches how to keep small local coding
models on track during real Python development with the [Pi agent
harness](https://pi.dev). It will produce a working and supported Pi extension
plus eval system.

It is not a production agent framework, a general-purpose coding assistant, or
a long-term model-training project. The material uses **Gemma 4 12B** as its
small local model and adopts Pi features only when a measured run shows why
they are needed.

## Status and success

This is an active experiment and course under construction; working artifacts
exist, but the claims and roadmap are still evolving. The experiment will
eventually be discarded, the SDD rewritten, and the real project restarted at
[`github.com/satyrn-ai`](https://github.com/satyrn-ai).

Success means producing a working Pi extension and eval system, supported by
honest measurements, documented methods, and recorded false starts—not merely a
trained model.

## Ground rules

- Measure before scaling training or evaluation work.
- Record decisions, false directions, and negative results.
- Use tests and executable verification.
- Review specs and plans before implementation.
- Never make claims stronger than the evidence.
- Keep the core corpus and eval tooling dependency-light and reproducible.

The reader never adopts a technique on faith. Each part shows a failure with
recorded telemetry, applies one Pi mechanism, and measures whether it helped.
Techniques that do not move a metric are not kept.

## The arc

1. **Part I — Pi extension basics.** A hello-world extension and the event
   lifecycle in miniature: enough to read and hook the agent loop.
2. **Part II — Measurement.** Read telemetry from `pi --mode json` and session
   JSONL, build a minimal eval harness, and establish a valid baseline before
   making improvement claims.
3. **Part III — Spec-driven development on Pi.** Use a roadmap-and-packet
   method, a parent-as-orchestrator system prompt, and an implementer
   specialist—adding more specialists only when evidence supports them.
4. **Part IV — Keeping the SLM on track.** Develop and measure evidence-backed
   Pi mechanisms for the failures that survive the earlier parts.

## The example workload

Throughout, the SLM builds the same small FastAPI application—the AgentClinic
complaints board—as a sequence of spec-driven phases. The app is deliberately
trivial; the point is the *steering*, not the app.

## Contributor setup

### Mandatory

- Python 3.14
- [`uv`](https://docs.astral.sh/uv/)
- [Pi](https://pi.dev)
- A local model server for live evaluation runs
- `pytest`

Install the repository environment and run the tests:

```bash
uv sync
just test
```

### Recommended

- [Ruff](https://docs.astral.sh/ruff/) for linting and formatting
- [Pyrefly](https://pyrefly.org) for type checking
- [RTK](https://github.com/rtk/rtk) for compact terminal output
- [Superpowers](https://github.com/obra/superpowers) for the SDD workflow

A Hugging Face account and token are optional, useful when downloading local
models.

Useful repository checks are collected in the [`Justfile`](Justfile):

```bash
just test
just quality
just docs
```

## Agents and models

If in doubt, use **Pi**. Pi is the default because its extension and eval
behavior are the subject of the project. Codex, Claude Code, OpenCode, and
other agents are supported alternatives for planning, coding, disposable
experiments, or review where they fit the workflow.

The material uses **Gemma 4 12B**. The material itself is developed with **K3,
GLM 5.2, DeepSeek Pro, and Flash**.

Do not use Anthropic, OpenAI, or other commercial models to generate the actual
training data or perform training; they may be used for planning, research,
coding, disposable experiments, or review.

## Fork and branch workflow

Fork the repository, then create a branch in your fork before making changes.
There is no required branch-naming convention. Keep the branch focused and open
the contribution from that branch.

## Spec-driven development

The repository is built with [Superpowers](https://github.com/obra/superpowers)
spec-driven development. Each feature cycle follows this loop:

```text
brainstorm → feature spec → implementation plan → implementation
→ verification → review/merge → evidence record
```

The roadmap tracks phases and current status. The backlog holds work that has
not yet met its evidence or recurrence bar. The archive keeps superseded
artifacts visible without making them look current.

| Artifact | Where | What it is |
|---|---|---|
| **Roadmap** | [`docs/superpowers/roadmap.md`](docs/superpowers/roadmap.md) | The cross-cycle index: sequence, status, next action, backlog, and archive. |
| **Specs** | [`docs/superpowers/specs/`](docs/superpowers/specs/) | What each cycle builds and why, settled before implementation. |
| **Plans** | [`docs/superpowers/plans/`](docs/superpowers/plans/) | The work decomposed into small, testable tasks. |
| **Research** | [`docs/superpowers/research/`](docs/superpowers/research/) and section research directories | Dated research, run reports, and supporting evidence. |
| **Policy** | [`docs/superpowers/policies/evidence.md`](docs/superpowers/policies/evidence.md) | The rules that decide what the course is allowed to assert. |

Start with [`KICKOFF.md`](KICKOFF.md), then read the roadmap's **Next action**
banner. The first HackMD note is background and project history; this README is
the canonical onboarding and setup source.

## Prompt recipes

Use these as starting points. Skills are optional: if a contributor has not
installed the named skill, they should use the equivalent research method.

### Research before design

```text
Use your Context7 skill to research the FastAPI package.
```

```text
Use your arXiv skill to research ideas about tool calling.
```

### Start the next work cycle

```text
Use Superpowers to brainstorm the next roadmap item.
```

To defer an idea without quietly committing to it:

```text
Use Superpowers to evaluate this idea and, if it does not yet meet the
evidence or recurrence bar, record it in the roadmap backlog with its trigger
for reconsideration.
```

Other useful prompt shapes are:

- Ask an agent to research the current behavior before proposing a design.
- Ask it to turn an approved brainstorm into a feature spec.
- Ask it to turn the spec into a task-by-task implementation plan.
- Ask it to implement the plan and run the executable verification.
- Ask an independent agent to review the code and evidence against the spec.
- Ask an agent to challenge assumptions and look for contamination or oracle
  weaknesses.

## Built the way it teaches

Because every cycle is on disk and in the commit history, you can work through
this repository as a worked example rather than just reading its output:

- **Start at [`KICKOFF.md`](KICKOFF.md).** It shows what a fresh agent session
  needs to know before implementation begins.
- **Follow the roadmap in order.** Each cycle's spec explains the reasoning,
  its plan shows the decomposition, and its evidence records what actually
  happened—including corrections and negative results.
- **Then fork the method, not the content.** The loop is useful for projects
  beyond small local models or Pi.

[`How This Was Built`](docs/how-this-was-built.md) covers the lineage, model
roles, and development environment.

## Reading the course

The chapters live under [`docs/`](docs/), one directory per section, and are
built with Sphinx + MyST. The [evidence policy](docs/superpowers/policies/evidence.md)
governs every measured claim in the course.

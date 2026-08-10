# Agent Engine

**A Pi extension plus an eval harness, for keeping small local models on
track during real Python development.** Working name of the effort: "AI
Our Way."

Small local models are not the "godbox" experience. You don't type a vague
prompt and let a huge model reason its way to a conclusion. Agentic coding
with a 12B model is small, routine, and much more like engineering — which
means the interesting question is *how do you know whether a technique
actually helped?*

This project's answer is to measure. **North star: evidence first** — a
trustworthy, convenient, repeatable way to collect it. Explicitly not
over-designed, over-engineered, or too large to absorb.

## Status

**Phases 1–5 are complete.** The engine runs a small local model against a
real task and decides hermetically whether it succeeded; it has survived
deliberate attacks on its own grading, generalizes to a second workload, and
can now express *"this run had something applied to it"* and measure it.

**Phase 5's headline is not the one it set out to prove, which is the point
of measuring.** Two sentences of prompt — *the workspace is empty* and *the
stack is FastAPI and Jinja2* — take the user-story suite from 0/16 to 15/16.
An orchestrator delegating to a specialist scored 13/16 on the same suite, so
its contribution is indistinguishable from zero here. The most transferable
finding is about what prompt text can do at all: across five interventions,
**the three that supplied a fact the model lacked worked, and the two that
supplied a rule of conduct did not** — including one true, checkable,
one-clause sentence that changed nothing.

Two published figures were retracted during that phase, both recorded with
banners rather than edited away. See [the roadmap](ROADMAP.md) for what's
planned, what's parked, and why.

**There is something installable.** The
[loop breaker](docs/loop-breaker.md) is a small Pi extension that refuses a
tool call the model has already made, unchanged, several times in a row. It
came out of a recorded run of 261 turns, 245 of them the identical `ls -R`
against an empty workspace. Live in a 16-run batch it refused 12 calls across
two runs, and both of those runs still passed. One file, copied into place —
and useful outside this project. (An earlier replay-based false-positive
figure is [withdrawn](docs/loop-breaker.md); the live result is what stands.)

## Start here

| If you want to… | Read |
|---|---|
| Understand why this project exists | [`BRIEF.md`](BRIEF.md) — the whole context, in one file |
| Use the Pi extension in your own work | [below](#using-the-extension-in-your-own-python-work), then [`docs/loop-breaker.md`](docs/loop-breaker.md) |
| Run an eval yourself | [below](#running-an-eval) |
| Get your machine set up | [`docs/setup.md`](docs/setup.md) |
| Understand how we work | [`docs/sdd.md`](docs/sdd.md) |
| See what's planned | [`ROADMAP.md`](ROADMAP.md) |
| Read the design record | [`docs/superpowers/index.md`](docs/superpowers/index.md) |

`BRIEF.md` is the single most valuable thing to read first. It is
deliberately short, it states the values this project is run by, and it
names the trap we are avoiding.

## Quick start

```bash
uv sync
uv run pytest
```

Most tests are hermetic and need nothing but Python. One live-model test is
explicitly opt-in, so a green run on a fresh machine is expected. Full setup,
including the model server, is in [`docs/setup.md`](docs/setup.md).

## Using the extension in your own Python work

**This half needs nothing from this repository except one file.** No harness,
no eval, no Python environment — the loop breaker is a Pi extension, and Pi
is what runs it.

Copy [`loop-breaker.ts`](.pi/extensions/loop-breaker.ts) into your user-scope
extensions directory:

```bash
mkdir -p ~/.pi/agent/extensions
cp .pi/extensions/loop-breaker.ts ~/.pi/agent/extensions/
```

That is the whole install. Pi loads user-scope extensions unconditionally,
so your next `pi` session in any project has it.

**This assumes Pi already has a model to talk to.** The extension is
provider-agnostic — it never names a model, an endpoint, or an API key — but
a genuinely unconfigured Pi fails before the extension ever gets a chance to
run, with `No API key found for the selected model`. That's Pi's own default
provider, nothing this project sets up. If `pi` isn't already working for you
outside this repository, get that working first — `/login` or
`~/.pi/agent/models.json`, per Pi's own docs — then the two commands above
are genuinely the whole install.

**Use the user-scope directory, not your project's `.pi/extensions/`, if you
delegate to subagents at all.** A delegated child does not load project
extensions — it loads user-scope ones — so a project-scope install guards the
parent and leaves the child unguarded, and on a small model the child is
usually where the runaway is. This project spent a whole cycle discovering
that.

What you get: when the model makes the same tool call, with the same
arguments, 5 times within a window of 20 calls, the next one is refused
before it executes and the model is told to do something else. It is not a
turn cap — a model doing varied work for a long time is untouched. Both
constants are at the top of the file.

Full page, including what to tune and the evidence behind it:
[`docs/loop-breaker.md`](docs/loop-breaker.md).

## Running one attempt against your own repository

The other installable piece. It runs a model once against your repo in a
throwaway git worktree, checks the result against a command *you* declare,
and leaves either a durable ref you can read or a receipt saying why not.
Your working tree is never written to, nothing is merged, and nothing is
promoted.

```bash
uv run python -m tools.deliver_candidate --repo . --task add-iter --prompt-file brief.md --validation "pytest -q" --writable "src/**" --model your-provider/your-model
```

Three things must be true first, and only the third announces itself:

1. **Pi is installed** — `pi --version` answers.
2. **`--model` names a model your Pi can resolve.** It reads *your*
   `~/.pi/agent`, not this repo's pinned one; pass `--agent-dir` to override.
3. **The server behind that model is up.** A dead server does not make Pi
   fail — it exits 0 having written nothing. The tool checks
   `--server` (default `http://127.0.0.1:8001`) before spending a call;
   `--skip-server-check` if your model is hosted elsewhere.

Exit codes are the answer, and three of them are distinct on purpose: **0**
a candidate exists, **1** a candidate was judged and discarded, **2** the
run was refused before it started (dirty repo, dead server), **3** nothing
was judged because the setup is broken. If you see 3, the problem is your
configuration, not the model.

Success prints the ref, and inspecting or discarding it is ordinary git:

```bash
git show refs/satyrn/candidates/add-iter
```

## Running an eval

This is the other half — measuring whether a technique actually helped,
rather than arguing about it. It needs the full setup: `uv sync`, Pi
0.83.0, and a local model server on `127.0.0.1:8001`. Work through
[`docs/setup.md`](docs/setup.md) first and confirm the liveness check
passes.

**One run**, to see the machinery work end to end:

```bash
uv run python -c "
from harness.runner import run_suite, AGENTCLINIC_PHASE_1_USER_STORY
result = run_suite(AGENTCLINIC_PHASE_1_USER_STORY)
print('accepted:', result.grade.accepted)
"
```

**A batch**, which is how every number this project publishes was produced.
`run_batch` appends one JSON record per completed run and **resumes by
counting valid lines**, so an interrupted batch continues where it stopped:

```bash
uv run python -c "
import pathlib
from harness.runner import run_batch, AGENTCLINIC_PHASE_1_USER_STORY
results = run_batch(
    pathlib.Path.home() / 'evidence' / 'my-first-batch.jsonl',
    suite=AGENTCLINIC_PHASE_1_USER_STORY,
    target=16,
)
print(f'{sum(r.accepted for r in results)}/{len(results)} accepted')
"
```

Three suites ship: `AGENTCLINIC_PHASE_1` (detailed roadmap — saturated, so
only cost moves), `AGENTCLINIC_PHASE_1_USER_STORY` (where benefit is
visible), and `DURATION`.

**To measure an improvement**, pass one. An `Improvement` is a named,
digested bundle of prompt, seeded files and extensions, and the harness
records which one a run used:

```python
from harness.runner import run_batch, AGENTCLINIC_PHASE_1_USER_STORY, tech_stack_only

run_batch(path, suite=AGENTCLINIC_PHASE_1_USER_STORY,
          target=16, improvement=tech_stack_only())
```

Then run the same suite *without* it for your baseline, and compare by hand.
Comparison is deliberately not automated.

### Three things that will bite you

**Batches are single-threaded and slow.** Measured on a 12B model, a 16-run
batch took 26 minutes without delegation and 49 minutes with it. Nothing
about this is interactive.

**A commit aborts a running batch.** `harness_revision` is part of
`RunConditions`, so committing mid-batch makes the next run's conditions
differ and `run_batch` raises `run conditions changed during batch`.
Completed runs are already in the checkpoint and are not lost — the batch
resumes once conditions match again, which in practice means finishing it
before you commit. **Editing files mid-batch is fine**; only committing
moves the revision.

**Wall-clock numbers are not currently trustworthy.** Arms run as contiguous
blocks, so any drift in machine load lands entirely on one arm and looks
like an arm effect — we withdrew a published finding over exactly this.
Counts (turns, `context_processed`, tool calls) are unaffected. Don't run
anything else heavy on the machine during a batch.

To read what a batch produced, see
[`docs/superpowers/research/`](docs/superpowers/research/) — each cycle's
record names its checkpoint and the script that recomputes its figures.

## How this project is built

Every feature goes through **spec-driven development**: brainstorm with the
owner, write a design spec, write an implementation plan, then implement it
test-first. The specs and plans are committed, not thrown away, so you can
read *why* code looks the way it does — see
[`docs/sdd.md`](docs/sdd.md).

Four disciplines are worth knowing before you contribute, because they
shape review:

**Concept budget.** Every piece of jargon is a cost against a volunteer's
ability to hold the design in mind. `ROADMAP.md` keeps a table of every term
the project spends, checked at the end of each cycle. If a doc needs a term
a 5-hour-a-week contributor can't absorb, the term goes — not the
contributor.

**No machinery ahead of the contract it serves.** Build the engine as needs
in the suites arise. Several genuinely good ideas sit in the Backlog
specifically because nothing needs them yet.

**Non-vacuity.** A test that passes without testing what it claims is this
project's recurring hazard, and most of the grading code exists to defeat
it. Ask of any new test: *what else could make this pass?*

**Verify, don't assert.** Claims get demonstrated, not argued. When a
review round claimed a security fix worked, we wrote the exploit and ran
it — it didn't, and the design changed. That norm has caught real bugs
more than once.

## Layout

```
BRIEF.md            the whole context — read this first
ROADMAP.md          phases, feature cycles, concept budget, backlog
harness/            the eval harness
tests/              its tests, mostly hermetic
examples/           AgentClinic fixtures and the task spec
docs/               setup, SDD explainer, and the design record
```

# Running evals

Every number this project publishes comes from the harness: a small local
model (Pi driving oMLX) is given a task, its workspace is graded against a
fixed acceptance contract, and the verdict is recorded. The one-liners are
in the [README](https://github.com/pauleveritt/local-ai-pi/blob/main/README.md); this page is the longer treatment.

## Before you start

An eval needs Pi and a model server up before anything runs. Getting both
is [the evals setup](setup.md): Pi (pinned 0.84.1) and oMLX serving
the reference model on `127.0.0.1:8001`. The fast check that everything is
in place is `uv run python -m harness.cli preflight` — it reports the
server and the Pi version, and says what to fix if either is wrong. A
single `one` run needs a working `pi` and the server; a `batch` also pins
the Pi version, so runs stay comparable between contributors. The model
string and the server underneath it — install, model acquisition, tuning —
are in [model-setup.md](../model-setup.md); the failures to expect along the
way are in [slm-struggles.md](slm-struggles.md).

## Why measure

Small models are stochastic. A single run tells you almost nothing — the
interesting question is whether a *technique* (a prompt structure, an
improvement) reliably helps. So the harness repeats a run until it has a
checkpoint full of attempts, and the acceptance rate across those attempts
is the number you can compare. The comparison itself stays manual and
deliberate: one improvement at a time, side by side, by hand.

The fuller argument — why this harness exists when benchmarks already do,
where it has collected signals nothing else could, and why the machinery
is the size it is — is in [why evals?](why-evals.md).

## The four concepts

**A run** is one model invocation against one suite. The harness checks the
model server, prepares an empty workspace, invokes Pi with the suite's task
spec, copies the model's allowlisted files into a fresh directory, and runs
the suite's acceptance tests there. A run is accepted only if Pi exited 0,
did not time out, and every acceptance test passed.

**A batch** is a sequence of runs that continues until the checkpoint holds
`--target` of them (default 16). A batch is *resumable*: it records each
run's conditions (model, Pi version, digests of the task spec, acceptance
file, and extensions) and refuses to resume a checkpoint whose conditions
have changed — so a batch and a checkpoint are locked together.

**An improvement** is a named, optional change to how a run is steered: a
seeded specialist, an extra extension, a system prompt. A run has exactly
one improvement or none. Improvements exist so two arms of a comparison
differ in one thing at a time.

**A checkpoint** is a JSONL file, one run per line, under `~/evidence/` by
default. It is the durable record of a batch — raw stdout, the diff, the
grade verdict, and the conditions the run happened under. `summarize`
reads it; nothing else in the CLI writes it.

## How to run each

```bash
uv run python -m harness.cli suites            # what can I run?
uv run python -m harness.cli improvements      # what can I apply?
uv run python -m harness.cli preflight         # is the server up? the right Pi?
uv run python -m harness.cli one --suite duration
uv run python -m harness.cli batch --suite duration --improvement tech-stack-only
uv run python -m harness.cli summarize ~/evidence/duration-2026-08-13.jsonl
```

The three suites you can run:

- `duration` — the cheapest eval: write one function (`parse_duration`) and
  have it pass a small contract. Start here.
- `agentclinic-phase-1` — the flagship: build a FastAPI + Jinja2 web app
  from a roadmap, graded against the full acceptance contract.
- `user-story` — the same application and contract as `agentclinic-phase-1`,
  but the task is described as user-facing outcomes rather than
  implementation steps. The two are a comparison pair: the description
  varies and nothing else.

**Planned: the `svcs` eval.** Phase 7 built the workload — `workloads/svcs/`
(a commit-replay cohort drawn from the `svcs` library: tasks with
manifests, hidden-oracle and preservation suites, cell pins). Bringing it
into `harness.cli` as a runnable suite is the intended next eval; it is
not runnable yet.

`--help` on any subcommand is the documentation. Exit codes follow the
project's convention: 0 the command completed its purpose, 2 refused before
starting (unknown name, dead server, wrong Pi version, checkpoint
mismatch), 1 an unexpected error.

## The three things that will bite you

1. **Batches are single-threaded.** The model server serializes children,
   so a batch of 16 is 16 sequential runs — plan for it to take a while,
   and never run two batches against the same server expecting speed.

2. **A commit aborts a running batch.** A batch records the harness
   revision as a run condition and refuses to resume a checkpoint whose
   conditions moved. If you commit mid-batch, the next attempt dies with a
   checkpoint-mismatch refusal and you must start that checkpoint fresh.

3. **There is no trustworthy wall-clock number.** Per-message durations are
   not recorded as start/end pairs, and this phase publishes no timing
   claim. If you see a wall-clock figure anywhere in this project's
   history, treat it as suspect.

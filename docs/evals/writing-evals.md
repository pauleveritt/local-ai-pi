# How to write an eval

An eval in this harness is one `Suite`: a task spec the model reads, an
acceptance contract it is graded against, and an allowlist of what it may
write. This page is how to author one; [the eval architecture](architecture.md)
is how a run flows through the machinery. The two existing suites —
`examples/duration` and `examples/agentclinic` — are the working
templates; everything below is what they demonstrate.

## The three pieces

**1. The task spec** — a markdown file the model reads as its
instructions. `examples/duration/spec.md` is the minimal shape ("write a
module `duration.py` with one public function"); `examples/agentclinic/
specs/roadmap.md` is the flagship shape (a phased roadmap for a web app).
The project's measured lessons say what a good spec must do:

- **Supply facts, not rules of conduct.** The five-intervention finding:
  the three prompts that supplied a fact worked; the two that supplied a
  rule did not. Name the framework, the module name, what is already
  installed, and what will be graded — because the model will otherwise
  choose for itself and choose wrong (see the allowlist trap below).
- **Say the workspace starts empty.** The orchestrated prompt had to be
  told explicitly: "listing the directory will keep returning nothing,
  because there is nothing there." Otherwise the model burns turns
  confirming the emptiness.

**2. The acceptance contract** — a pytest file, `examples/*/acceptance/
test_acceptance.py`. Its constraints come from the grading machinery:

- **Module-level `test_*` functions only** (async included). The expected
  count is read from the file's source (`harness/grading.py`'s
  `_test_count`), and class-grouped tests are deliberately unsupported.
- **It imports only what the allowlist carries** — `from duration import
  parse_duration`, `from app import app`. Grading copies the allowlisted
  files and the acceptance into a fresh directory, so any other import
  fails there even if it worked in the model's workspace.
- **The verdict never comes from pytest's exit code.** The grading plugin
  writes per-test outcomes and a `__DONE__` marker to a results file, and
  the harness reads that. Model-written config (pyproject.toml, pytest.ini,
  conftest.py, sitecustomize.py) is refused outright, because config is
  executable and earlier graders were defeated by `addopts = --collect-only`
  and an import-time `os._exit(0)`.

**3. The source allowlist** — a tuple of paths the model may write that
reach the grader: `("app.py", "templates")` for agentclinic, `("duration.py",)`
for duration. It is a **copy-only** gate: anything the model wrote that is
not on the allowlist never reaches the grading directory. The classic
trap: a solution under `app/main.py` never gets graded, because only
`app.py` is copied — the spec must name the exact module, which is why the
tech-stack prompt says "the graded module is `app.py` at the project
root."

## Registering it

Add a `Suite` to `harness/runner.py` with a stable short name — the CLI
addresses suites by `SUITES` key (`agentclinic-phase-1`, `user-story`,
`duration`), and the key is a CLI-facing shorthand that may differ from
`Suite.name`. Then it appears in `harness.cli suites` and `--suite`
choices automatically; nothing else needs wiring.

## The evidence floor

A suite is not done until it has been *proven* to discriminate. The
`Suite` deliberately carries no solutions, so the proof lives in tests
that name fixture paths directly (the `examples/*/reference` and
`examples/*/broken` trees):

- a known-good fixture **passes** the acceptance contract, and
- a known-broken fixture **fails** it,

each asserted by naming the fixture, not by routing through the harness.
The same discipline requires the suite's own files to exist and the
allowlist to be nonempty (a suite with a typo'd task spec fails at run
time, where the failure is expensive and reads like a model problem).

If the new suite shares a contract with an existing one, make it a
comparison pair the way `user-story` is: same acceptance, same allowlist,
a different task spec — "the description varies and nothing else." The
conditions machinery keeps the pair distinguishable by task-spec digest
even though they grade against one contract.

## Running and comparing

`uv run python -m harness.cli one --suite <name>` for a single run;
`batch --suite <name>` for the n=16 corpus; `summarize` to read it.
Comparison stays manual and deliberate: one improvement at a time, side by
side, by hand — the harness measures, it does not compare for you.

## Checklist

- Task spec and acceptance exist; the allowlist is nonempty.
- Acceptance: module-level tests only; the count is right; it imports only
  allowlisted names.
- Evidence floor: known-good accepted, known-broken rejected, asserted by
  fixture path.
- Registered in `SUITES` with a short CLI name; `suites` lists it.
- If it shares a contract, the task spec differs and nothing else does.

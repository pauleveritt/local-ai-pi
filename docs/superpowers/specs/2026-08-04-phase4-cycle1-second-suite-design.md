# Phase 4 cycle 1 — a second eval suite

*Design, 2026-08-04. Direction: prove the engine generalizes beyond one
workload.*

## Why this cycle

`BRIEF.md` names one thing as the cost of the previous project:

> **Seams, not hardcodes.** The one thing that actually cost the old
> project: the case was hardcoded (`_SOURCE_FILES = ("app.py",
> "models.py")`, and `examples/{acceptance,reference}/phase-N` baked into
> two functions) rather than parameterised with a single caller.

Three phases later the engine has exactly one workload, AgentClinic
Phase 1. Two of its three layers are already parameterised and have never
been called with anything but their default:

- `prepare_workspace(source_dir: Path | None = None)` — `harness/workspace.py`
- `grade(workspace, suite, timeout, source_allowlist=("app.py", "templates"))`
  — `harness/grading.py`

A seam with one caller and a workload-shaped default is indistinguishable
from a hardcode. The hardcode proper lives in `harness/runner.py`:
`PHASE_1`, `TASK_SPEC`, `run_agentclinic_phase1`, and `_conditions`
hashing a module-level constant rather than what it was handed.

A second suite is the only thing that tells the difference.

## What this cycle claims, and what it does not

**Claims:** the harness runs two suites through one code path, and each
suite's grader has accepted a known-good solution and rejected a
known-broken one.

**Does not claim:** that a suite author can add a third suite touching
only `examples/`. That is the goal, but it is not supportable at n=2, and
asserting it would be the same overreach this project keeps catching in
itself. Whatever `harness/` edits the second suite turns out to require
become a recorded finding — a list of what was not general enough is
worth more than a claim.

**Does not claim** a number. This cycle runs no batch. See "Verification".

**Scope of the generality claim:** the *task-spec* and *grading* seams.
The chosen workload starts from an empty workspace, so no *run* starts
from a seeded workspace and the seeding seam is untested in anger. Say
"the spec and grading seams", never "the seams".

*(Corrected: this paragraph previously said `prepare_workspace(source_dir=...)`
"keeps zero real callers". That was imprecise — the floor tests in
`tests/test_grading.py` and `tests/test_workspace.py` call it with a source
dir and always have. What is actually untried is a model run starting from
seeded code; the runner path calls `prepare_workspace()` bare.)*

## The evidence floor

From `BRIEF.md`:

> A grader's verdict isn't evidence until it has accepted a known-good
> solution and rejected a known-broken one.

This is non-negotiable and applies per suite. The pattern already exists
for AgentClinic at `tests/test_grading.py:239` and `:269`; the new suite
gets the same pair.

*(Corrected 2026-08-04, after implementation. This paragraph and
Deliverable 4 below both said the floor tests would be "parameterized over
the two suites". They are not: planning chose a separate
`tests/test_duration_suite.py`, leaving AgentClinic's pair standalone in
`tests/test_grading.py`. The evidence is equivalent — each suite's grader
accepts its known-good and rejects its known-broken solution — but this
spec is what a later cycle rereads as the authority, so it must describe
what exists.)*

## Design

### The `Suite` descriptor

*Line numbers in this document are anchored to the branch base,
`0643e5b` — it describes the state before the change. The research
record's citations are anchored to the merged result instead.*

Two constants at `harness/runner.py:13-14` (`PHASE_1`, `TASK_SPEC`) and
`grade()`'s `source_allowlist` default at `harness/grading.py:79` become
fields of one frozen dataclass:

```python
@dataclass(frozen=True)
class Suite:
    name: str
    task_spec: Path        # the prompt handed to the model
    acceptance: Path       # the harness-owned test file
    source_allowlist: tuple[str, ...]
```

The module declares two instances. `AGENTCLINIC_PHASE_1` keeps today's
values, including `source_allowlist=("app.py", "templates")`. `DURATION`
uses a single-file allowlist — a different arity *and* a different kind
(no directory), which is what demonstrates the parameter is a parameter
rather than decoration.

Four fields. Deliberately excluded:

- **`seed`** — `prepare_workspace` already accepts `source_dir`, but no
  suite uses it. Adding the field now is machinery ahead of its contract.
- **`grade_timeout` / `run_timeout`** — nothing needs to vary them.
  `run_batch` hardcodes 600 (`runner.py:213`) and `grade_timeout=30`
  (`runner.py:163`); a duration parser grades in well under either.
- **`reference` / `broken`** — the runner never needs them. Only the
  floor test does, and it names them directly the way
  `tests/test_grading.py:240` already does. `Suite` carries only what a
  *run* requires.

### `_conditions` takes the suite — an acceptance criterion, not an implication

This is load-bearing and is stated as a requirement rather than left to
fall out of the refactor.

`RunConditions` has eight fields. Between two suites, seven of them are
identical by construction: `model`, `pi_version`, `harness_revision`,
`run_timeout`, `grade_timeout`, `extension_digests`, and `pi_command` —
the last because the prompt is normalized away to `"<task-spec>"` at
`runner.py:159`. The **only** field that discriminates two suites is
`task_spec_sha256`, and that field is currently computed from the
module-level constant this cycle removes.

If the re-plumbing is missed, a duration batch records the AgentClinic
hash, the two suites' checkpoints become mutually resumable, and runs
graded against different contracts accumulate in one file looking like
data. That is the failure mode this cycle exists to prevent, so it gets
tests: `_conditions` for the two suites must differ, and `run_batch` must
refuse a checkpoint recorded under the other suite.

For the same reason `run_batch` takes `suite` as a **required**
keyword argument. A default would let a caller record a batch under a
suite they never named.

### `RunConditions` gains no `suite` field

A `suite` field would make records self-describing, which is genuinely
useful. It is declined because every field added to `RunConditions` makes
existing checkpoints non-matching — the problem the `("<pre-cycle1>",)`
sentinel at `runner.py:29-33` exists to soften — and the recorded
evidence checkpoints live outside version control in
`~/local-ai-pi-evidence/`. Rendering them unresumable in exchange for
readability alone is a bad trade.

**Recorded as a known gap, not fixed here:** discrimination *within* a
suite is not sound. Nothing in `RunConditions` records the acceptance
file's contents or the `source_allowlist`, and `harness_revision` is
`git rev-parse HEAD` (`runner.py:153-155`) — so an *uncommitted* edit to
an acceptance file, or a changed allowlist, leaves conditions
byte-identical and a batch resumes a checkpoint graded under a different
contract. This is the same bug class `extension_digests` was added to
close. It goes to the Backlog. If a digest field is ever added, the
`<pre-cycle1>` sentinel pattern means old checkpoints become
unresumable-but-readable, not lost.

### `grade()`'s parameter is renamed `suite` → `acceptance`

*suite* is already a budgeted term with a narrower meaning: the ROADMAP
concept-budget table defines it as "the acceptance test suite a solution
is graded against", and `grade(workspace, suite: Path)` is literally the
acceptance file (`grading.py:75-79`). The `Suite` dataclass means the
whole workload bundle.

Without the rename the code reads `grade(workspace, suite.acceptance,
...)` — a callee parameter named `suite` receiving `suite.acceptance`.

This is a **redefinition of a pinned term, not a free addition.** The
concept-budget entry is rewritten accordingly and the change recorded as
such. The earlier claim that this cycle spends no new jargon because
`BRIEF.md` already says "Suites group" was wrong.

## The workload

A duration parser. Pure library: no web framework, no templates, no HTTP;
acceptance imports a plain module and uses the standard library only.

Chosen to vary exactly the axes the hardcodes name — source file name,
allowlist arity and kind, no `templates/` directory — and hold everything
else constant: pytest acceptance, import-graded, empty starting
workspace. Holding the rest still is what makes the result readable: if
something breaks, it broke because of file-shape generality and not
because grading also changed.

`parse_duration(text: str) -> int`, returning seconds:

| input | result |
|---|---|
| `"30s"` | `30` |
| `"5m"` | `300` |
| `"1h"` | `3600` |
| `"1h30m"` | `5400` |
| `"2h15m30s"` | `8130` |
| unparseable | raises `ValueError` |

`spec.md` must name the file `duration.py` explicitly, because
`DURATION.source_allowlist` is `("duration.py",)` and the two must agree:
a solution written to any other filename is copied nowhere and fails
grading for a reason that looks like a model error. Acceptance imports
`from duration import parse_duration`.

The contract is a literal table, so nothing is invented by us and nothing
is left for the model to interpret — the same property that made
AgentClinic's tagline a contract literal. The broken variant has one *defect* — it stops at the first unit — which
fails the two multi-unit rows: `"1h30m"` → `3600` and `"2h15m30s"` →
`7200`. The four single-unit and unparseable rows still pass, so the
fixture proves the grader discriminates on behavior rather than rejecting
anything that merely looks different. *(Corrected 2026-08-04: this
paragraph previously said "one row wrong", which was wrong — one defect is
not one row.)*

### Rejected workloads

- **AgentClinic Phase 2** (the `/complaints` page): needs seeding, which
  this cycle defers, and its allowlist would be nearly identical to
  Phase 1's — almost no pressure on the seams.
- **A CLI task graded by subprocess:** maximum pressure, but the grader
  assumes acceptance imports the model's code. New grader machinery ahead
  of the contract it serves.
- **A config deep-merge:** we would be inventing list and `None`
  semantics rather than reading a contract.
- **A semver comparator:** attractive because its answer is *externally*
  known and trusted, the property that made AgentClinic Phase 1 the right
  first workload. Rejected because prerelease precedence would move
  difficulty off the ceiling in an uncontrolled way, adding a second
  variable to a cycle whose value depends on shape being the only one.

## Layout

```
examples/duration/
    spec.md                          # the prompt
    acceptance/test_acceptance.py    # harness-owned
    reference/duration.py            # known-good
    broken/duration.py               # known-bad: one defect, two rows fail
```

Flatter than AgentClinic's, which nests under `phase-1/` because
AgentClinic genuinely has phases and one roadmap file covers several of
them. A phase-less suite should not carry a fake `phase-1/`.

No `empty/`: `examples/agentclinic/phase-1/empty/` is a test fixture for
`prepare_workspace` (`tests/test_workspace.py:102`), not something the
runner consumes — `run_agentclinic_phase1` calls `prepare_workspace()`
bare.

`spec.md` carries an "Environment" section stating what is installed and
that nothing may be installed, parallel to
`examples/agentclinic/specs/roadmap.md`.

**Note on the BRIEF's phase-N hardcode.** `BRIEF.md` names
`examples/{acceptance,reference}/phase-N` as one of the original
hardcodes. It does not exist in this codebase: nothing in `harness/`
bakes `phase-N`. The literals live at `runner.py:13-14`, which `Suite`
dissolves, and in test-module constants. What is actually open is a
*convention* for where a phase-less suite lives, which this section
settles.

## The no-parametrize rule

`_test_count` counts module-level `def test_*` declarations
(`grading.py:159-178`); the grading plugin records one line per
*executed* nodeid. `@pytest.mark.parametrize` splits them — 1 declared, N
executed — so `tests_executed == tests_expected` fails and a **correct**
solution is rejected. That is the engine-looks-like-a-model-failure
confusion `_test_count`'s own docstring warns about, and a contract
shaped like a literal table is about the most parametrize-inviting thing
there is.

**Rule: acceptance suites use one test function per contract behaviour.
No `parametrize`.**

Extending `_test_count` to compute parametrize cardinality was
considered and rejected: it means deciding what pytest *would collect*
rather than reading what the file *declares*, and that refusal is the
whole design of the function. A documented constraint is cheaper than
re-implementing collection semantics for a suite nobody has written.

The rule is recorded in the acceptance file's own docstring, where an
author writing the next suite will meet it — the placement precedent set
by commit `80b2513`.

## Also recorded, not fixed

Every acceptance suite can only import what the harness's own venv
provides: `grading.py:204` sets the grading subprocess's `PYTHONPATH` to
the repo root. AgentClinic's suite imports `starlette` and `turbohtml`.
`Suite` does not capture this dependency, and the duration suite does not
force the question because it is stdlib-only. Naming the coupling is the
whole of the obligation here.

## Verification

The four gates: `uv run pytest`, `uv run ruff check .`,
`uv run pyrefly check`, and
`uv run sphinx-build -W -b html docs docs/_build/html`. The new spec and
plan must be added to the `Specs` and `Plans` toctrees in
`docs/superpowers/index.md`, whose entries are explicit — a document in
no toctree fails the strict build.

**Offline, and the real proof.** Both suites accept their reference and
reject their broken. No model required, so it runs under every gate
invocation.

**One live single run** of `run_suite(DURATION)`, `SATYRN_LIVE`-gated
like the existing live tests, with the model server verified alive first.
It proves the seam end-to-end through a real Pi invocation.

**No batch.** A batch produces a number, and this cycle claims no number
— it claims the harness runs two suites. Running n=16 on the duration
suite would also mean coordinating a commit freeze across concurrent
sessions for roughly 25 minutes to buy evidence for a claim not being
made.

**Model server.** Before any live run, verify the server returns real
model output. When it is down, `pi` exits 0 with empty stderr and the
harness records a fabricated result that looks like data.

## Phase placement

This closes Phase 3 and opens **Phase 4 — prove the engine generalizes
beyond one workload.** Phase 3's direction was "build the extension
half"; it delivered that in two cycles (an observable extension, then its
mechanics and gotchas documented), and its orchestration cycles are in
the Backlog by owner decision. A suite cycle is a different direction,
and slipping it into Phase 3 is the tangent-creep `BRIEF.md` warns
against.

## Deliverables

1. `Suite`, two instances, `run_suite`, re-plumbed `_conditions`, and
   `run_batch(suite=...)` in `harness/runner.py`.
2. `grade()`'s parameter renamed to `acceptance`.
3. `examples/duration/` — four files.
4. A floor test pair per suite (see the correction under "The evidence
   floor" — these shipped as a separate module, not parameterized), plus
   three new tests:
   `_conditions` differs between suites; `run_batch` refuses a
   cross-suite checkpoint; duration's reference/broken pair.
5. One `SATYRN_LIVE`-gated end-to-end run of the duration suite.
6. ROADMAP: Phase 3 closed, Phase 4 opened with this cycle; the *suite*
   concept-budget entry rewritten as a redefinition; a Backlog entry for
   the within-suite conditions gap.
7. A research record listing what `harness/` edits the second suite
   actually required — the finding this cycle's modest bar exists to
   produce.

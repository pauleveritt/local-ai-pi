# Phase 5 cycle 1 — improvement mechanism implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let the harness record that a run had a named improvement applied,
and observe one real delegation under this harness's flags.

**Architecture:** A frozen `Improvement` descriptor names a seed directory, extra
extensions, and a system prompt. `run_suite` seeds the workspace before git-init
(so improvement files stay out of the run diff), appends the extensions, and adds
`--append-system-prompt`. `RunConditions` gains four fields in one schema break;
older checkpoints load with sentinels and become unresumable-but-readable.

**Tech Stack:** Python 3.14, pytest, uv, ruff, pyrefly, Sphinx. No new dependencies.

## Global Constraints

- Spec: `docs/superpowers/specs/2026-08-04-phase5-cycle1-improvement-mechanism-design.md`
- **This cycle claims no number and runs no batch.** Task 5 is a single live
  invocation, not a batch.
- Every seam ships a mutation check: apply the break, watch a **named** test
  fail, revert. A green suite after a mutation means the seam is unproven.
- Implementer self-reports do not count. Re-run every claim independently.
- Gates before each commit: `uv run pytest -q`, `uv run ruff check .`,
  `uv run pyrefly check`, and for doc changes `uv run sphinx-build -W -q -b html docs docs/_build/html`.
- Work in `.worktrees/phase5-improvement-loop` on branch `phase5-improvement-loop`.
- Never `git stash` (the stash stack is shared across worktrees).
- Line-number citations get anchored to a revision: "verified at `<sha>` on 2026-08-04".

---

## File Structure

| File | Responsibility |
|---|---|
| `harness/runner.py` (modify) | `Improvement`, `_path_digest`, four new `RunConditions` fields, wiring in `run_suite`/`run_batch`/`_pi_command`/`_conditions` |
| `harness/checkpoint.py` (modify) | Sentinel-load the four new fields |
| `tests/conftest.py` (create) | `make_conditions(**overrides)` so a future field addition touches one place |
| `improvements/sdd-orchestrator/orchestrator.md` (create) | Parent system prompt, passed by flag — deliberately **not** under `.pi/agents/` |
| `improvements/sdd-orchestrator/seed/.pi/agents/implementer.md` (create) | The specialist, seeded into the workspace |
| `tests/test_improvement.py` (create) | Mechanism tests and mutation checks |
| `docs/superpowers/research/2026-08-04-phase5-cycle1-delegation-spike.md` (create) | What the live invocation actually showed |

---

### Task 1: `RunConditions` gains four fields, in one break

**Files:**
- Modify: `harness/runner.py:55-78` (`RunConditions`), `harness/runner.py:188-218` (`_conditions`)
- Modify: `harness/checkpoint.py:57-74`
- Create: `tests/conftest.py`
- Modify: `tests/test_runner.py`, `tests/test_checkpoint.py` (construction sites)
- Test: `tests/test_improvement.py`

**Interfaces:**
- Consumes: nothing from other tasks.
- Produces: `RunConditions` with `improvement_name: str`, `improvement_digest: str`,
  `acceptance_sha256: str`, `source_allowlist: tuple[str, ...]`;
  `_conditions(suite, model, command, timeout, extensions=EXTENSIONS, improvement=None)`;
  `make_conditions(**overrides) -> RunConditions` in `tests/conftest.py`.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_improvement.py`:

```python
import dataclasses
import hashlib
from types import SimpleNamespace

import pytest

import harness.runner as runner
from harness.runner import Suite


def _stub_subprocess(monkeypatch):
    monkeypatch.setattr(
        runner.subprocess,
        "run",
        lambda command, **kwargs: SimpleNamespace(stdout="stub\n"),
    )
    monkeypatch.setattr(runner, "_path_digest", lambda path: "digest")


def test_uncommitted_acceptance_edit_changes_conditions(tmp_path, monkeypatch):
    """`harness_revision` is `git rev-parse HEAD`, so an *uncommitted* edit
    to an acceptance file sails past it. Without `acceptance_sha256` a batch
    resumes a checkpoint graded under a different contract."""
    _stub_subprocess(monkeypatch)
    spec = tmp_path / "spec.md"
    spec.write_text("build a thing")
    acceptance = tmp_path / "test_acceptance.py"
    acceptance.write_text("def test_one(): assert True\n")
    suite = Suite("s", spec, acceptance, ("thing.py",))

    before = runner._conditions(suite, "model", ["pi", "prompt"], 600)
    acceptance.write_text("def test_one(): assert False\n")
    after = runner._conditions(suite, "model", ["pi", "prompt"], 600)

    assert before.acceptance_sha256 != after.acceptance_sha256
    assert before != after


def test_changing_the_allowlist_changes_conditions(tmp_path, monkeypatch):
    """Two suites differing only in which model-written paths get graded
    must not share conditions."""
    _stub_subprocess(monkeypatch)
    spec = tmp_path / "spec.md"
    spec.write_text("build a thing")
    acceptance = tmp_path / "test_acceptance.py"
    acceptance.write_text("def test_one(): assert True\n")

    narrow = runner._conditions(
        Suite("s", spec, acceptance, ("thing.py",)), "model", ["pi", "p"], 600
    )
    wide = runner._conditions(
        Suite("s", spec, acceptance, ("thing.py", "templates")),
        "model", ["pi", "p"], 600,
    )

    assert narrow.source_allowlist != wide.source_allowlist
    assert narrow != wide


def test_conditions_without_an_improvement_say_so(tmp_path, monkeypatch):
    """A run with no improvement records that explicitly, so a reader of a
    checkpoint line never has to infer it from an absent field."""
    _stub_subprocess(monkeypatch)
    spec = tmp_path / "spec.md"
    spec.write_text("build a thing")
    acceptance = tmp_path / "test_acceptance.py"
    acceptance.write_text("def test_one(): assert True\n")
    suite = Suite("s", spec, acceptance, ("thing.py",))

    conditions = runner._conditions(suite, "model", ["pi", "prompt"], 600)

    assert conditions.improvement_name == "none"
    assert conditions.improvement_digest == "<none>"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_improvement.py -q`
Expected: FAIL — `AttributeError: module 'harness.runner' has no attribute '_path_digest'`.

- [ ] **Step 3: Rename `_extension_digest` to `_path_digest`**

In `harness/runner.py`, rename the function and its call site in `_conditions`.
The name changes because Task 3 hashes a *seed directory* with it, and
`_extension_digest` applied to a seed directory would be a lie. Update the
`monkeypatch.setattr(runner, "_extension_digest", ...)` line in
`tests/test_runner.py` to match.

- [ ] **Step 4: Add the four fields**

In `harness/runner.py`, append to `RunConditions`:

```python
    improvement_name: str
    improvement_digest: str
    acceptance_sha256: str
    source_allowlist: tuple[str, ...]
```

Extend the class docstring:

```python
    """...existing text...

    Records written before phase 5 cycle 1 load with the sentinel
    `"<pre-phase5>"` (and `("<pre-phase5>",)` for the allowlist), following
    the `("<pre-cycle1>",)` precedent above. They stay readable and
    recomputable; no SHA-256, real allowlist, or improvement name can equal
    a sentinel, so `run_batch` refuses to resume them.

    `acceptance_sha256` and `source_allowlist` close a gap `harness_revision`
    cannot: it is `git rev-parse HEAD`, so an *uncommitted* acceptance edit
    or a changed allowlist would otherwise leave these conditions
    byte-identical. The allowlist is recorded verbatim rather than digested
    because it is a handful of short strings a reader should be able to see.
    """
```

- [ ] **Step 5: Populate them in `_conditions`**

Change the signature to
`_conditions(suite, model, command, timeout, extensions=EXTENSIONS, improvement=None)`
and the returned object to include:

```python
        improvement_name="none" if improvement is None else improvement.name,
        improvement_digest=_improvement_digest(improvement),
        acceptance_sha256=hashlib.sha256(suite.acceptance.read_bytes()).hexdigest(),
        source_allowlist=suite.source_allowlist,
```

Add, for now, a minimal digest helper (Task 3 gives it its real body):

```python
def _improvement_digest(improvement: "Improvement | None") -> str:
    if improvement is None:
        return "<none>"
    parts = [
        _path_digest(path)
        for path in (improvement.seed_dir, improvement.system_prompt)
        if path is not None
    ]
    return hashlib.sha256("\n".join(parts).encode()).hexdigest()
```

- [ ] **Step 6: Sentinel-load in `harness/checkpoint.py`**

Inside the `RunConditions(...)` construction in `load_checkpoint`, add:

```python
                        improvement_name=data["conditions"].get(
                            "improvement_name", "<pre-phase5>"
                        ),
                        improvement_digest=data["conditions"].get(
                            "improvement_digest", "<pre-phase5>"
                        ),
                        acceptance_sha256=data["conditions"].get(
                            "acceptance_sha256", "<pre-phase5>"
                        ),
                        source_allowlist=tuple(
                            data["conditions"].get(
                                "source_allowlist", ("<pre-phase5>",)
                            )
                        ),
```

- [ ] **Step 7: Add the shared test helper**

Create `tests/conftest.py`:

```python
"""Shared test construction for `RunConditions`.

Every field added to `RunConditions` otherwise means editing every
positional construction in the test suite. Phase 5 cycle 1 added four at
once; this exists so the next one edits one place.
"""

from harness.runner import RunConditions


def make_conditions(**overrides) -> RunConditions:
    defaults = dict(
        model="model",
        pi_command=("pi",),
        pi_version="0.83.0",
        task_spec_sha256="task-spec-sha",
        harness_revision="rev",
        run_timeout=600,
        grade_timeout=30,
        extension_digests=("digest",),
        improvement_name="none",
        improvement_digest="<none>",
        acceptance_sha256="acceptance-sha",
        source_allowlist=("app.py",),
    )
    return RunConditions(**{**defaults, **overrides})
```

Note: the repo-root `conftest.py` stays empty on purpose (it puts the repo
root on `sys.path`); this is a second, `tests/`-scoped one.

- [ ] **Step 8: Migrate existing construction sites**

In `tests/test_runner.py` and `tests/test_checkpoint.py`, replace every
positional `RunConditions(...)` construction with `make_conditions(...)`,
importing it with `from tests.conftest import make_conditions` — or, if
pytest's rootdir handling makes that import awkward, declare it as a
fixture-free module-level helper and import via `from conftest import
make_conditions`. Keep each call's *intent*: where a test previously varied
`task_spec_sha256` positionally, pass `task_spec_sha256=` explicitly.

Run: `uv run pytest -q` after this step. Expected: all previously passing
tests pass again, plus the three new ones.

- [ ] **Step 9: Mutation check — prove the two new digests are load-bearing**

Temporarily delete the `acceptance_sha256=` line from `_conditions`.

Run: `uv run pytest tests/test_improvement.py::test_uncommitted_acceptance_edit_changes_conditions -q`
Expected: FAIL — `TypeError: RunConditions.__init__() missing 1 required
positional argument`. That proves the field is required, but *not* that it
varies. So instead set it to a constant: `acceptance_sha256="constant"`.
Expected: FAIL with `assert 'constant' != 'constant'`.

Repeat for `source_allowlist=("app.py",)` as a constant against
`test_changing_the_allowlist_changes_conditions`. Expected: FAIL.

Revert both mutations. Re-run: `uv run pytest -q`. Expected: PASS.

- [ ] **Step 10: Commit**

```bash
git add harness/runner.py harness/checkpoint.py tests/
git commit -m "feat(phase5): record improvement, acceptance and allowlist in conditions"
```

---

### Task 2: `_path_digest` handles a directory tree

**Files:**
- Modify: `harness/runner.py` (`_path_digest`)
- Test: `tests/test_improvement.py`

**Interfaces:**
- Consumes: `_path_digest(path: Path) -> str` from Task 1 (currently raises on directories).
- Produces: `_path_digest` accepting a file **or** a directory tree.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_improvement.py`:

```python
def test_tree_digest_changes_on_any_nested_file(tmp_path):
    """A digest that only saw top-level files would let an edit deep in
    Pi's shipped subagent tree pass unnoticed."""
    tree = tmp_path / "ext"
    (tree / "agents").mkdir(parents=True)
    (tree / "index.ts").write_text("export const x = 1\n")
    (tree / "agents" / "implementer.md").write_text("name: implementer\n")

    before = runner._path_digest(tree)
    (tree / "agents" / "implementer.md").write_text("name: implementer!\n")
    after = runner._path_digest(tree)

    assert before != after


def test_tree_digest_ignores_the_trees_own_path(tmp_path):
    """Pi's shipped extension sits at a different absolute path on every
    contributor's machine and moves on every upgrade. A path-sensitive
    digest would report drift that is not there."""
    first = tmp_path / "a" / "ext"
    second = tmp_path / "b" / "ext"
    for tree in (first, second):
        (tree / "agents").mkdir(parents=True)
        (tree / "index.ts").write_text("export const x = 1\n")
        (tree / "agents" / "implementer.md").write_text("name: implementer\n")

    assert runner._path_digest(first) == runner._path_digest(second)


def test_tree_digest_is_order_independent(tmp_path):
    """Filesystem iteration order is not guaranteed. Two trees with the
    same contents must digest identically regardless of creation order."""
    first = tmp_path / "a"
    second = tmp_path / "b"
    first.mkdir()
    second.mkdir()
    (first / "one.ts").write_text("1\n")
    (first / "two.ts").write_text("2\n")
    (second / "two.ts").write_text("2\n")
    (second / "one.ts").write_text("1\n")

    assert runner._path_digest(first) == runner._path_digest(second)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_improvement.py -q -k tree_digest`
Expected: FAIL — `ValueError: extension is a directory, not a file`.

- [ ] **Step 3: Implement tree digesting**

Replace `_path_digest` in `harness/runner.py`:

```python
def _path_digest(path: Path) -> str:
    """SHA-256 of one file, or of a directory tree's contents.

    A tree is hashed as the sorted list of `<relative path> <file digest>`
    lines. Sorting makes it independent of filesystem iteration order;
    using paths *relative to the tree root* makes it independent of where
    the tree sits. Both matter for Pi's shipped subagent extension, which
    lives at a different absolute path on every machine and moves on every
    Pi upgrade -- an absolute-path-sensitive digest would report drift that
    is not there, and a top-level-only digest would miss drift that is.

    Phase 4 cycle 1 left this decision to "the cycle that needs it"; this
    is that cycle.
    """
    if path.is_dir():
        entries = sorted(
            f"{child.relative_to(path).as_posix()} "
            f"{hashlib.sha256(child.read_bytes()).hexdigest()}"
            for child in path.rglob("*")
            if child.is_file()
        )
        return hashlib.sha256("\n".join(entries).encode()).hexdigest()
    return hashlib.sha256(path.read_bytes()).hexdigest()
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_improvement.py -q`
Expected: PASS (6 tests).

- [ ] **Step 5: Mutation check**

Change `child.relative_to(path).as_posix()` to `str(child)`.
Run: `uv run pytest tests/test_improvement.py::test_tree_digest_ignores_the_trees_own_path -q`
Expected: FAIL.

Change `sorted(...)` to `list(...)`, and confirm
`test_tree_digest_is_order_independent` is at least *capable* of failing by
reversing the generator (`reversed(list(...))`).
Expected: FAIL.

Revert both. Run: `uv run pytest -q`. Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add harness/runner.py tests/test_improvement.py
git commit -m "feat(phase5): digest a directory tree by sorted relative-path contents"
```

---

### Task 3: `Improvement`, and the three seams that carry it

**Files:**
- Modify: `harness/runner.py` (`Improvement`, `_pi_command`, `run_suite`, `run_batch`)
- Test: `tests/test_improvement.py`

**Interfaces:**
- Consumes: `_path_digest`, `_improvement_digest`, `_conditions` from Tasks 1–2.
- Produces:
  - `Improvement(name: str, seed_dir: Path | None, extensions: tuple[Path, ...], system_prompt: Path | None)`
  - `run_suite(suite, *, model=DEFAULT_MODEL, timeout=600, improvement: Improvement | None = None)`
  - `run_batch(checkpoint_path, *, suite, target=16, model=DEFAULT_MODEL, improvement: Improvement | None = None)`
  - `_pi_command(model, prompt, extensions=EXTENSIONS, system_prompt: Path | None = None)`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_improvement.py`:

```python
def test_pi_command_appends_the_system_prompt_before_the_task_spec(tmp_path):
    """`_conditions` normalizes the *last* command element to
    "<task-spec>". The system prompt flag must not displace it."""
    prompt_file = tmp_path / "orchestrator.md"
    prompt_file.write_text("You orchestrate.\n")

    command = runner._pi_command("model", "build a thing", system_prompt=prompt_file)

    assert command[-1] == "build a thing"
    assert "--append-system-prompt" in command
    assert command[command.index("--append-system-prompt") + 1] == str(prompt_file)


def test_pi_command_omits_the_flag_without_a_system_prompt():
    command = runner._pi_command("model", "build a thing")
    assert "--append-system-prompt" not in command


def test_seeded_agent_file_is_present_in_the_workspace(tmp_path):
    """Pi discovers project-local specialists under `.pi/agents/` relative
    to its cwd, which is the disposable workspace. If seeding does not
    happen, no delegation is possible at all."""
    seed = tmp_path / "seed"
    (seed / ".pi" / "agents").mkdir(parents=True)
    (seed / ".pi" / "agents" / "implementer.md").write_text("---\nname: implementer\n---\n")

    from harness.workspace import prepare_workspace

    with prepare_workspace(seed) as workspace:
        assert (workspace / ".pi" / "agents" / "implementer.md").is_file()


def test_seeded_files_do_not_appear_in_the_run_diff(tmp_path):
    """`prepare_workspace` copies before git-init and commits, so seeded
    files are in the initial commit. If that order ever flips, every
    orchestrated run's diff would carry the improvement's own files and the
    record of what the *model* wrote would be polluted."""
    import subprocess

    from harness.workspace import prepare_workspace

    seed = tmp_path / "seed"
    (seed / ".pi" / "agents").mkdir(parents=True)
    (seed / ".pi" / "agents" / "implementer.md").write_text("---\nname: implementer\n---\n")

    with prepare_workspace(seed) as workspace:
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=workspace,
            check=True, capture_output=True, text=True,
        ).stdout.strip()
        subprocess.run(["git", "add", "-A"], cwd=workspace, check=True, capture_output=True)
        diff = subprocess.run(
            ["git", "diff", "--cached", head], cwd=workspace,
            check=True, capture_output=True, text=True,
        ).stdout

    assert "implementer.md" not in diff


def test_editing_a_seeded_file_changes_conditions(tmp_path, monkeypatch):
    """The improvement is data. Editing that data must change the
    conditions, or a batch resumes a checkpoint recorded under a different
    improvement -- the same bug `extension_digests` closed one layer up."""
    monkeypatch.setattr(
        runner.subprocess,
        "run",
        lambda command, **kwargs: SimpleNamespace(stdout="stub\n"),
    )
    spec = tmp_path / "spec.md"
    spec.write_text("build a thing")
    acceptance = tmp_path / "test_acceptance.py"
    acceptance.write_text("def test_one(): assert True\n")
    suite = Suite("s", spec, acceptance, ("thing.py",))

    seed = tmp_path / "seed"
    (seed / ".pi" / "agents").mkdir(parents=True)
    agent = seed / ".pi" / "agents" / "implementer.md"
    agent.write_text("---\nname: implementer\n---\nBuild exactly the packet.\n")
    improvement = runner.Improvement("sdd-orchestrator", seed, (), None)

    before = runner._conditions(
        suite, "model", ["pi", "p"], 600, runner.EXTENSIONS, improvement
    )
    agent.write_text("---\nname: implementer\n---\nBuild whatever you like.\n")
    after = runner._conditions(
        suite, "model", ["pi", "p"], 600, runner.EXTENSIONS, improvement
    )

    assert before.improvement_digest != after.improvement_digest
    assert before.improvement_name == after.improvement_name == "sdd-orchestrator"
    assert before != after


def test_run_batch_refuses_a_pre_phase5_checkpoint(tmp_path, monkeypatch):
    """Old evidence stays readable but must not be resumed: those runs had
    no improvement recorded, and no real value can equal the sentinel."""
    from conftest import make_conditions

    from harness.checkpoint import append_checkpoint
    from harness.runner import RunResult
    from harness.grading import GradeResult

    checkpoint = tmp_path / "runs.jsonl"
    stale = make_conditions(
        improvement_name="<pre-phase5>",
        improvement_digest="<pre-phase5>",
        acceptance_sha256="<pre-phase5>",
        source_allowlist=("<pre-phase5>",),
    )
    grade = GradeResult(
        accepted=True, tests_executed=4, tests_expected=4,
        returncode=0, stdout="4 passed\n", stderr="", refused_config=(),
    )
    append_checkpoint(
        checkpoint, RunResult("diff", grade, "", "", 0, conditions=stale)
    )

    monkeypatch.setattr(runner, "_conditions", lambda *args, **kwargs: make_conditions())
    monkeypatch.setattr(
        runner, "preflight_model", lambda model: pytest.fail("preflight called")
    )
    monkeypatch.setattr(
        runner, "run_suite", lambda suite, **kwargs: pytest.fail("run called")
    )

    with pytest.raises(ValueError, match="checkpoint conditions do not match"):
        runner.run_batch(checkpoint, suite=runner.AGENTCLINIC_PHASE_1, target=2)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_improvement.py -q`
Expected: FAIL — `AttributeError: module 'harness.runner' has no attribute 'Improvement'`.

- [ ] **Step 3: Add the `Improvement` descriptor**

In `harness/runner.py`, after `DURATION`:

```python
@dataclass(frozen=True)
class Improvement:
    """A named, optional change to how a run is steered.

    A descriptor rather than a manifest file, following `Suite`: a parser,
    a schema, and an error path have no present caller. If a contributor
    ever needs to add an improvement without editing Python, that is the
    cycle that adds the manifest.

    `seed_dir` is copied into the workspace *before* git-init, so the files
    it carries land in the initial commit and never appear in the run diff.
    That is what makes `.pi/agents/implementer.md` placeable without
    polluting the record of what the model wrote.

    `system_prompt` is passed by flag and must **not** live under
    `.pi/agents/`: any `.md` there carrying `name:`/`description:`
    frontmatter is discovered as a callable specialist, so an orchestrator
    kept there could delegate to itself with no depth cap.

    A run has exactly one improvement or none. Nothing composes two.
    """

    name: str
    seed_dir: Path | None
    extensions: tuple[Path, ...]
    system_prompt: Path | None
```

- [ ] **Step 4: Thread it through `_pi_command`**

```python
def _pi_command(
    model: str,
    prompt: str,
    extensions: tuple[Path, ...] = EXTENSIONS,
    system_prompt: Path | None = None,
) -> list[str]:
```

and immediately before the final `command += [...]` block that ends with
`prompt`, insert:

```python
    if system_prompt is not None:
        command += ["--append-system-prompt", str(system_prompt)]
```

The prompt must stay last: `_conditions` normalizes `command[-1]` to
`"<task-spec>"`, and a flag appended after it would be hashed as the prompt.

- [ ] **Step 5: Thread it through `run_suite`**

```python
def run_suite(
    suite: Suite,
    *,
    model: str = DEFAULT_MODEL,
    timeout: int = 600,
    improvement: Improvement | None = None,
) -> RunResult:
    check_model_server_alive()

    seed_dir = None if improvement is None else improvement.seed_dir
    with prepare_workspace(seed_dir) as workspace:
```

and replace the three lines starting at `extensions = EXTENSIONS`:

```python
        prompt = suite.task_spec.read_text()
        extensions = EXTENSIONS + (() if improvement is None else improvement.extensions)
        system_prompt = None if improvement is None else improvement.system_prompt
        command = _pi_command(model, prompt, extensions, system_prompt)
        conditions = _conditions(suite, model, command, timeout, extensions, improvement)
```

- [ ] **Step 6: Thread it through `run_batch`**

Add `improvement: Improvement | None = None` to the keyword-only parameters.
Inside, replace the command/conditions lines:

```python
    extensions = EXTENSIONS + (() if improvement is None else improvement.extensions)
    system_prompt = None if improvement is None else improvement.system_prompt
    command = _pi_command(model, suite.task_spec.read_text(), extensions, system_prompt)
    requested = _conditions(suite, model, command, 600, extensions, improvement)
```

and pass it to the run:

```python
        result = run_suite(suite, model=model, improvement=improvement)
```

- [ ] **Step 7: Run the tests to verify they pass**

Run: `uv run pytest tests/test_improvement.py -q`
Expected: PASS (12 tests).

Run: `uv run pytest -q`
Expected: PASS, no regressions.

- [ ] **Step 8: Mutation checks**

1. In `run_suite`, change `prepare_workspace(seed_dir)` to `prepare_workspace()`.
   Run: `uv run pytest tests/test_improvement.py -q`.
   Expected: the seeding test still passes, because it calls
   `prepare_workspace` directly — **this is the Phase 4 cycle 1 near-miss
   repeating.** Fix it by adding a test that goes through `run_suite` with a
   stubbed `run_process`, asserting the workspace contained the seeded file.
   Add it, watch it fail under the mutation, then revert the mutation.
2. In `_pi_command`, move the `--append-system-prompt` insertion to *after*
   the final `command += [...]`.
   Run: `uv run pytest tests/test_improvement.py::test_pi_command_appends_the_system_prompt_before_the_task_spec -q`
   Expected: FAIL. Revert.

Run: `uv run pytest -q`. Expected: PASS.

- [ ] **Step 9: Commit**

```bash
git add harness/runner.py tests/test_improvement.py
git commit -m "feat(phase5): Improvement descriptor, seeded and digested into conditions"
```

---

### Task 4: The `sdd-orchestrator` improvement

**Files:**
- Create: `improvements/sdd-orchestrator/orchestrator.md`
- Create: `improvements/sdd-orchestrator/seed/.pi/agents/implementer.md`
- Modify: `harness/runner.py` (`pi_package_root`, `SDD_ORCHESTRATOR`)
- Modify: `pyproject.toml` (`norecursedirs`, ruff `extend-exclude`)
- Test: `tests/test_improvement.py`

**Interfaces:**
- Consumes: `Improvement` from Task 3.
- Produces: `pi_package_root() -> Path`, `SDD_ORCHESTRATOR: Improvement`.

- [ ] **Step 1: Write the failing tests**

```python
def test_pi_package_root_contains_the_shipped_subagent_extension():
    """The mechanism this improvement rides on is Pi's, not ours."""
    subagent = runner.pi_package_root() / "examples" / "extensions" / "subagent"
    assert (subagent / "index.ts").is_file()
    assert (subagent / "agents").is_dir()


def test_sdd_orchestrator_points_at_files_that_exist():
    improvement = runner.SDD_ORCHESTRATOR
    assert improvement.seed_dir is not None and improvement.seed_dir.is_dir()
    assert (improvement.seed_dir / ".pi" / "agents" / "implementer.md").is_file()
    assert improvement.system_prompt is not None and improvement.system_prompt.is_file()
    assert improvement.extensions and all(p.exists() for p in improvement.extensions)


def test_the_orchestrator_prompt_is_not_a_discoverable_specialist():
    """Any `.md` under `.pi/agents/` with name/description frontmatter is
    discovered as a *callable* specialist. An orchestrator kept there could
    delegate to itself with no depth cap."""
    assert ".pi/agents" not in runner.SDD_ORCHESTRATOR.system_prompt.as_posix()
```

- [ ] **Step 2: Run to verify they fail**

Run: `uv run pytest tests/test_improvement.py -q -k "pi_package_root or sdd_orchestrator or orchestrator_prompt"`
Expected: FAIL — `AttributeError: ... has no attribute 'pi_package_root'`.

- [ ] **Step 3: Implement `pi_package_root`**

```python
def pi_package_root() -> Path:
    """Where Pi's installed package lives, so its shipped examples can be
    referenced by path rather than forked.

    **Not** resolved from `$(which pi)`. Under volta -- this project's
    setup -- `which pi` returns a shim (`~/.volta/bin/volta-shim`), so the
    binary's own location says nothing about the package. Verified on
    2026-08-04: `which pi` gave `/Users/…/.volta/bin/pi`, whose realpath is
    `volta-shim`. `npm root -g` is no better; it returns volta's *node*
    image directory, which does not contain the package.

    Checked in order: `$SATYRN_PI_PACKAGE`, then volta's package layout.
    """
    override = os.environ.get("SATYRN_PI_PACKAGE")
    if override:
        return Path(override)
    volta = (
        Path.home() / ".volta" / "tools" / "image" / "packages"
        / "@earendil-works" / "pi-coding-agent" / "lib" / "node_modules"
        / "@earendil-works" / "pi-coding-agent"
    )
    if volta.is_dir():
        return volta
    raise RuntimeError(
        "cannot locate Pi's installed package. Set SATYRN_PI_PACKAGE to the "
        "directory containing examples/extensions/subagent -- find it with "
        "`find ~ -maxdepth 8 -type d -name pi-coding-agent`. Resolving from "
        "`which pi` does not work under volta, and `npm root -g` points at "
        "the node image rather than the package."
    )


IMPROVEMENTS = REPO_ROOT / "improvements"

SDD_ORCHESTRATOR = Improvement(
    name="sdd-orchestrator",
    seed_dir=IMPROVEMENTS / "sdd-orchestrator" / "seed",
    extensions=(pi_package_root() / "examples" / "extensions" / "subagent",),
    system_prompt=IMPROVEMENTS / "sdd-orchestrator" / "orchestrator.md",
)
```

Add `import os` to the module imports.

**Note for the implementer:** `SDD_ORCHESTRATOR` calls `pi_package_root()` at
import time, so `import harness.runner` fails on a machine without Pi. If
`uv run pytest -q` shows collection errors elsewhere, make it a lazily-built
module function `sdd_orchestrator() -> Improvement` instead and update the
tests to call it. Choose whichever keeps the suite passing without Pi; the
existing suite already skips rather than fails when Pi is absent.

- [ ] **Step 4: Write the specialist**

Create `improvements/sdd-orchestrator/seed/.pi/agents/implementer.md`:

```markdown
---
name: implementer
description: Builds exactly what a handoff packet specifies, and nothing else.
tools: read,write,bash
model: omlx/gemma-4-12B-it-MLX-8bit
---

You are an implementer. You are given a handoff packet and you build
exactly what it specifies.

- Build only what the packet's Task section describes.
- Write only the files listed under Allowed Files. Do not create others.
- Any text under Acceptance Strings must appear verbatim in your output,
  character for character.
- Do not explore the repository, redesign the task, or propose
  alternatives. Do not read files that are not listed.
- Run the command under Validation before you report completion, and say
  what it printed.

Report what you built and what validation printed. Do not claim success
you have not observed.
```

- [ ] **Step 5: Write the orchestrator prompt**

Create `improvements/sdd-orchestrator/orchestrator.md`:

```markdown
You orchestrate. You do not write the solution yourself.

Read the task specification you were given. For each phase it describes,
construct a handoff packet and delegate it to the `implementer` specialist
using the `subagent` tool. Always pass `agentScope: "both"` -- the default
`"user"` scope never reads project-local specialists, and the delegation
will find no agent at all.

Delegate one packet at a time and wait for each result. The model server is
single-threaded; concurrent children contend for it.

A handoff packet has exactly these four sections:

## Task
<what to build, extracted from the specification>

## Allowed Files
<the exact files the implementer may write>

## Acceptance Strings
<any text that must appear verbatim in the output>

## Validation
<the command that checks the work>

After a delegation returns, check its report against the packet you sent.
Do not treat the implementer's claim of success as evidence; if validation
output was not shown, the work is unverified.
```

- [ ] **Step 6: Exclude the improvement tree from collection and linting**

In `pyproject.toml`, add `"improvements"` to pytest's `norecursedirs` and to
ruff's `extend-exclude`, mirroring the existing `examples` entries. The seed
tree contains no Python today, but the two existing suites are excluded for
the same structural reason and a future improvement may seed Python.

- [ ] **Step 7: Run the tests to verify they pass**

Run: `uv run pytest tests/test_improvement.py -q`
Expected: PASS.

Run: `uv run pytest -q && uv run ruff check . && uv run pyrefly check`
Expected: all clean.

- [ ] **Step 8: Commit**

```bash
git add improvements/ harness/runner.py pyproject.toml tests/test_improvement.py
git commit -m "feat(phase5): the sdd-orchestrator improvement, as data"
```

---

### Task 5: The live delegation spike

**Files:**
- Create: `docs/superpowers/research/2026-08-04-phase5-cycle1-delegation-spike.md`
- Modify: `docs/superpowers/index.md` (research list + toctree)
- Modify: `ROADMAP.md` (Phase 5 cycle 1 row → Done, plus what the spike found)

**Interfaces:**
- Consumes: `SDD_ORCHESTRATOR`, `run_suite` from Tasks 3–4.
- Produces: a research record. No code.

- [ ] **Step 1: Confirm the model server returns real output**

Run: `curl -s -m 10 http://127.0.0.1:8001/v1/models`
Expected: a JSON body naming `omlx/gemma-4-12B-it-MLX-8bit`.

If it does not respond, start it with `omlx start` and retry. Do **not**
proceed on a silent server: `pi` exits 0 with empty stderr and the harness
records a fabricated result that looks like data. (`omlx diagnose` without a
target argument is not a valid invocation.)

- [ ] **Step 2: Run one live invocation, in the foreground**

Run:

```bash
uv run python -c "
from harness.runner import AGENTCLINIC_PHASE_1, SDD_ORCHESTRATOR, run_suite
result = run_suite(AGENTCLINIC_PHASE_1, improvement=SDD_ORCHESTRATOR)
open('/tmp/spike-stdout.jsonl','w').write(result.pi_stdout)
print('accepted:', result.grade.accepted, 'rc:', result.pi_returncode, 'timed_out:', result.pi_timed_out)
"
```

**Foreground only.** A backgrounded live run was torn down mid-flight by its
controlling process during Phase 4 cycle 1, and a dead run leaves no trace in
the harness's records — the only evidence is a surviving temp workspace,
because `prepare_workspace` removes it in a `finally`.

Do not predict how long this takes; that expectation is what invited the
backgrounding last time.

- [ ] **Step 3: Check whether a delegation actually happened**

Run:

```bash
uv run python -c "
import json
names = []
for line in open('/tmp/spike-stdout.jsonl'):
    try: event = json.loads(line)
    except json.JSONDecodeError: continue
    if 'tool' in json.dumps(event)[:200].lower():
        names.append(event.get('type'))
print(sorted(set(names)))
"
grep -c subagent /tmp/spike-stdout.jsonl
```

Expected: at least one `subagent` occurrence, and tool-execution events.

- [ ] **Step 4: Record what happened, including if it failed**

Create `docs/superpowers/research/2026-08-04-phase5-cycle1-delegation-spike.md`
stating: whether a `subagent` tool call appeared; whether the child produced a
result; whether more than one child ran concurrently (the observation the
Backlog's own-tool gate depends on); the grade; and the exact command used.

If no delegation occurred, **that is the cycle's finding** and the record says
so plainly, with the three reading-derived claims from the spec re-checked
against what the run showed. Phase 3 cycle 1 retired a reading-justified claim
exactly this way. Do not tune prompts to force a success; that is cycle 2's
work, under pre-registration.

- [ ] **Step 5: Wire the record into the docs**

Add a bullet under `## Research` in `docs/superpowers/index.md` and a line to
the research `toctree`, mirroring the Phase 4 cycle 1 entry.

- [ ] **Step 6: Close the cycle in `ROADMAP.md`**

Set the Phase 5 cycle 1 row's State to `Done`, add the `[plan]` and
`[research]` links beside the existing `[spec]` link, and add a short
"Cycle 1 spent…" paragraph under the cycle table recording the concept-budget
check. After editing, run the pipe-table contiguity check — strict Sphinx does
not cover `ROADMAP.md`, and a row inserted mid-table has broken one before:

```bash
python3 -c "
lines = open('ROADMAP.md').read().split(chr(10))
runs, cur = [], []
for i, l in enumerate(lines, 1):
    if l.startswith('|'): cur.append(i)
    else:
        if cur: runs.append((cur[0], cur[-1], len(cur)))
        cur = []
if cur: runs.append((cur[0], cur[-1], len(cur)))
[print(a, b, n, lines[a-1][:40]) for a, b, n in runs]
"
```

- [ ] **Step 7: Full gates, then commit**

```bash
uv run pytest -q
uv run ruff check .
uv run pyrefly check
uv run sphinx-build -W -q -b html docs docs/_build/html
git add -A
git commit -m "docs(phase5): what one live delegation showed"
```

---

## Self-Review

**Spec coverage.** `Improvement` descriptor → Task 3. Three seams (seeding,
extensions, system prompt) → Task 3. Directory digest → Task 2. Four
`RunConditions` fields with sentinels → Task 1. `sdd-orchestrator` files →
Task 4. Gating spike → Task 5. Every mutation-check row in the spec's
verification table maps to a step: improvement digest (Task 3 step 1),
acceptance digest and allowlist (Task 1 step 9), both directory-digest rows
(Task 2 step 5), sentinel refusal (Task 3 step 1), seeding and diff (Task 3
steps 1 and 8).

**Type consistency.** `_path_digest` is named consistently from Task 1's
rename onward; Task 1 step 3 explicitly updates the existing monkeypatch of
the old name. `_conditions` gains its two new parameters in Task 1 and is
called with them positionally in Task 3's tests, matching the signature.
`Improvement`'s four fields are used with the same names in Tasks 3 and 4.

**Known risk, flagged rather than hidden.** Task 4 step 3 notes that
`SDD_ORCHESTRATOR` resolves Pi's package at import time and gives the
fallback if that breaks collection on a machine without Pi. Task 3 step 8
deliberately walks the implementer into the Phase 4 cycle 1 near-miss — a
mutation that leaves the suite green — and requires adding the test that
actually covers `run_suite` before reverting.

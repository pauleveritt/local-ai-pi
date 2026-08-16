# Phase 11 Handoff Contract File — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `/implement <contract-file>` drives the bounded implementer with a contract written in-session, and refuses — before spending a model call — when it cannot.

**Architecture:** A contract is a markdown file: YAML front-matter carries the structural bounds, the body is the task prose. `harness/contract_file.py` parses it into the existing `HandoffContract` wire format. `harness/contract_lint.py` refuses paths the packet names that can be neither read nor created. `tools/deliver_candidate.py` gains `--contract <path>` and loses `--prompt-file`. `packages/engine/orchestrator.ts` passes the path through. A Claude Code skill tells the main agent how to write one.

**Tech Stack:** Python 3.14, pytest, PyYAML (new direct dependency), TypeScript on Bun, Pi 0.84.1.

**Spec:** [`2026-08-16-phase11-rescope-design.md`](../specs/2026-08-16-phase11-rescope-design.md)

## Global Constraints

- **Python `>=3.14,<3.15`.** Match existing style: `from __future__` is not used; modern union syntax (`str | None`) throughout.
- **`--contract-task` is not touched.** It stays as the harness-only svcs bridge, marked for removal. Do not fold, rename, or refactor it.
- **No executor changes.** Do not modify `extensions/implementer/*`, `extensions/probe-cap.ts`, or any cell TOML. Those change the measured arm and need their own cell.
- **Exit codes are fixed by existing behaviour:** 0 candidate-created, 1 discarded, 2 refused, 3 infrastructure-failure. The only new code is **4 = instrument fault**.
- **`HandoffContract` is one wire format with two declarations** — `harness/typed_contract.py` and `isContract()` in `extensions/implementer/implementer.ts`. Do not change either. This plan only builds a *new producer* of that format.
- **No live model runs in Tasks 1–5.** Task 6 is the single smoke test and is explicitly not a measurement.
- Run `uv run ruff format` and `uv run ruff check --fix` before each commit.

---

### Task 1: Parse a contract file into a `HandoffContract`

**Files:**
- Create: `harness/contract_file.py`
- Create: `tests/test_contract_file.py`
- Modify: `pyproject.toml:7-11` (add the `pyyaml` dependency)

**Interfaces:**
- Consumes: `HandoffContract`, `WritableFile` from `harness/typed_contract.py` (existing `TypedDict`s).
- Produces:
  - `class ContractFileError(Exception)` — any malformed or incomplete file.
  - `def parse_contract_file(path: Path) -> HandoffContract`

**Context you need:** `HandoffContract` is a `TypedDict` with keys `task: str`, `writableFiles: list[WritableFile]`, `readableFiles: list[str]`, `acceptanceStrings: list[str]`, `preservedBehavior: list[str]`, `knownFacts: list[str]`, `validation: str`, and optional `removableSymbols: list[str]`. `WritableFile` is `{"path": str}`. The child validates this shape at `isContract()`, so every key except `removableSymbols` must be present even when empty.

Only `writableFiles` and `validation` are required *of the author*; the parser fills the rest with empty lists.

- [ ] **Step 1: Add the dependency**

PyYAML is currently present only transitively. Make it explicit in `pyproject.toml`:

```toml
dependencies = [
    "fastapi[standard]==0.115.10",
    "pytest==8.3.4",
    "pyyaml>=6.0",
    "turbohtml==1.5.0",
]
```

Then run:

```bash
uv sync
```

- [ ] **Step 2: Write the failing tests**

Create `tests/test_contract_file.py`:

```python
"""harness/contract_file.py: a markdown contract file -> HandoffContract.

Deterministic, no model calls. The file is what an agent writes in-session;
the TypedDict is the wire format implementer.ts already validates.
"""

import pytest

from harness.contract_file import ContractFileError, parse_contract_file

MINIMAL = """\
---
writableFiles: [src/svcs/_core.py]
validation: pytest -q
---
# Enter async context managers

Append `(name, svc)` to `self._on_close`, rebind `svc`.
"""


def _write(tmp_path, text, name="contract.md"):
    path = tmp_path / name
    path.write_text(text)
    return path


def test_body_becomes_the_task_and_front_matter_is_stripped(tmp_path):
    contract = parse_contract_file(_write(tmp_path, MINIMAL))
    assert contract["task"].startswith("# Enter async context managers")
    assert "writableFiles" not in contract["task"]


def test_writable_files_become_the_wire_format_dicts(tmp_path):
    contract = parse_contract_file(_write(tmp_path, MINIMAL))
    assert contract["writableFiles"] == [{"path": "src/svcs/_core.py"}]


def test_optional_lists_default_to_empty_so_the_child_accepts_the_shape(tmp_path):
    contract = parse_contract_file(_write(tmp_path, MINIMAL))
    assert contract["readableFiles"] == []
    assert contract["acceptanceStrings"] == []
    assert contract["preservedBehavior"] == []
    assert contract["knownFacts"] == []


def test_optional_fields_are_carried_through_when_present(tmp_path):
    text = """\
---
writableFiles: [src/svcs/_core.py]
readableFiles: [src/svcs/**, tests/**]
validation: pytest -q
knownFacts:
  - The app is ASGI, not WSGI.
acceptanceStrings:
  - aget returns the entered value
---
Body.
"""
    contract = parse_contract_file(_write(tmp_path, text))
    assert contract["readableFiles"] == ["src/svcs/**", "tests/**"]
    assert contract["knownFacts"] == ["The app is ASGI, not WSGI."]
    assert contract["acceptanceStrings"] == ["aget returns the entered value"]


def test_missing_file_is_a_contract_file_error(tmp_path):
    with pytest.raises(ContractFileError, match="no contract file"):
        parse_contract_file(tmp_path / "absent.md")


def test_missing_front_matter_names_the_delimiter(tmp_path):
    with pytest.raises(ContractFileError, match="front-matter"):
        parse_contract_file(_write(tmp_path, "# Just a body\n"))


def test_unparseable_yaml_is_reported_as_such(tmp_path):
    text = "---\nwritableFiles: [unclosed\n---\nBody.\n"
    with pytest.raises(ContractFileError, match="front-matter is not valid YAML"):
        parse_contract_file(_write(tmp_path, text))


def test_writable_files_is_required(tmp_path):
    text = "---\nvalidation: pytest -q\n---\nBody.\n"
    with pytest.raises(ContractFileError, match="writableFiles"):
        parse_contract_file(_write(tmp_path, text))


def test_empty_writable_files_is_refused_not_silently_accepted(tmp_path):
    text = "---\nwritableFiles: []\nvalidation: pytest -q\n---\nBody.\n"
    with pytest.raises(ContractFileError, match="writableFiles"):
        parse_contract_file(_write(tmp_path, text))


def test_validation_is_required(tmp_path):
    text = "---\nwritableFiles: [src/svcs/_core.py]\n---\nBody.\n"
    with pytest.raises(ContractFileError, match="validation"):
        parse_contract_file(_write(tmp_path, text))


def test_an_empty_body_is_refused(tmp_path):
    text = "---\nwritableFiles: [a/b.py]\nvalidation: pytest -q\n---\n\n"
    with pytest.raises(ContractFileError, match="body is empty"):
        parse_contract_file(_write(tmp_path, text))


def test_a_scalar_where_a_list_belongs_names_the_field(tmp_path):
    text = "---\nwritableFiles: src/svcs/_core.py\nvalidation: pytest -q\n---\nBody.\n"
    with pytest.raises(ContractFileError, match="writableFiles"):
        parse_contract_file(_write(tmp_path, text))
```

- [ ] **Step 3: Run the tests to verify they fail**

Run: `uv run pytest tests/test_contract_file.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'harness.contract_file'`

- [ ] **Step 4: Write the implementation**

Create `harness/contract_file.py`:

```python
"""A markdown contract file -> the `HandoffContract` wire format.

What an agent writes in-session, and the only producer of a contract in
the product path. YAML front-matter carries the bounds; the body is the
task prose.

The split matters: the bounds are *declared*, never inferred from the
prose. Inferring them is what the gate branch's nomination rule did, and
it was deleted on 2026-08-16 for firing on the shape of a line rather
than on what the line asked for -- three false positives and three false
negatives out of three tasks each.

Only `writableFiles` and `validation` are required of the author. The
remaining keys are filled with empty lists because `isContract()` in
`extensions/implementer/implementer.ts` validates the whole shape; an
author should not have to type fields to satisfy a schema.
"""

from pathlib import Path

import yaml

from harness.typed_contract import HandoffContract

_DELIMITER = "---"


class ContractFileError(Exception):
    """The file is missing, malformed, or incomplete.

    A bad packet, not a broken tool -- the caller maps this to exit 2.
    """


def _string_list(raw: object, field: str) -> list[str]:
    if raw is None:
        return []
    if not isinstance(raw, list) or not all(isinstance(item, str) for item in raw):
        raise ContractFileError(
            f"{field} must be a list of strings; got {type(raw).__name__}"
        )
    return list(raw)


def _split_front_matter(text: str, path: Path) -> tuple[str, str]:
    if not text.startswith(_DELIMITER):
        raise ContractFileError(
            f"{path}: no front-matter. A contract starts with a '---' line, "
            "then the bounds as YAML, then '---', then the task prose."
        )
    parts = text.split(f"\n{_DELIMITER}", 2)
    if len(parts) < 2:
        raise ContractFileError(
            f"{path}: the front-matter is never closed. Add a '---' line "
            "between the bounds and the task prose."
        )
    return parts[0][len(_DELIMITER) :], parts[1]


def parse_contract_file(path: Path) -> HandoffContract:
    """Read `path` and build the contract the implementer child consumes.

    Raises `ContractFileError` for anything an author can fix.
    """
    if not path.is_file():
        raise ContractFileError(f"no contract file at {path}")

    head, body = _split_front_matter(path.read_text(), path)

    try:
        loaded = yaml.safe_load(head) or {}
    except yaml.YAMLError as error:
        raise ContractFileError(
            f"{path}: the front-matter is not valid YAML -- {error}"
        ) from error
    if not isinstance(loaded, dict):
        raise ContractFileError(
            f"{path}: the front-matter must be a mapping of fields, "
            f"got {type(loaded).__name__}"
        )

    task = body.strip()
    if not task:
        raise ContractFileError(
            f"{path}: the body is empty. The body is the task -- it is what "
            "tells the implementer which operations to perform."
        )

    writable = _string_list(loaded.get("writableFiles"), "writableFiles")
    if not writable:
        raise ContractFileError(
            f"{path}: writableFiles is required and must name at least one "
            "path. It is the bound the implementer is held to, and the lint "
            "cannot tell a file the contract means to create from one it "
            "named by mistake without it."
        )

    validation = loaded.get("validation")
    if not isinstance(validation, str) or not validation.strip():
        raise ContractFileError(
            f"{path}: validation is required -- the command the parent runs "
            "to judge the candidate, e.g. 'pytest -q'."
        )

    contract: HandoffContract = {
        "task": task,
        "writableFiles": [{"path": p} for p in writable],
        "readableFiles": _string_list(loaded.get("readableFiles"), "readableFiles"),
        "acceptanceStrings": _string_list(
            loaded.get("acceptanceStrings"), "acceptanceStrings"
        ),
        "preservedBehavior": _string_list(
            loaded.get("preservedBehavior"), "preservedBehavior"
        ),
        "knownFacts": _string_list(loaded.get("knownFacts"), "knownFacts"),
        "validation": validation.strip(),
    }
    removable = _string_list(loaded.get("removableSymbols"), "removableSymbols")
    if removable:
        contract["removableSymbols"] = removable
    return contract
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `uv run pytest tests/test_contract_file.py -v`
Expected: PASS, 12 tests

- [ ] **Step 6: Commit**

```bash
uv run ruff format harness/contract_file.py tests/test_contract_file.py
uv run ruff check --fix harness/contract_file.py tests/test_contract_file.py
git add harness/contract_file.py tests/test_contract_file.py pyproject.toml uv.lock
git commit -m "feat(phase11): parse a markdown contract file into HandoffContract"
```

---

### Task 2: The path lint

**Files:**
- Create: `harness/contract_lint.py`
- Create: `tests/test_contract_lint.py`

**Interfaces:**
- Consumes: nothing from Task 1 — takes plain values so it can be tested and reused without a file.
- Produces:
  - `class ContractLintUnusable(Exception)` — the lint cannot judge; the caller maps this to exit 4.
  - `def impossible_paths(task: str, writable_files: Sequence[str], base_tree: Path) -> tuple[str, ...]` — returns the offending paths, empty when clean.

**Context you need:** This is the one surviving criterion of five, ported as a function rather than as the 380-line module it lives in on `phase11-inspect-contract`. The rule: a backticked token that looks like a repository path (it needs both a slash and a file extension) must either exist in the base tree or be listed in `writableFiles`. Anything else can be neither read nor created, so the contract asks for something impossible.

The `autowire` case is why `writableFiles` is consulted rather than tree-existence alone: that contract correctly names `src/svcs/_autowire.py`, a module that does not exist because adding it *is* the task.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_contract_lint.py`:

```python
"""harness/contract_lint.py: the one gate criterion that survived measurement.

Deterministic -- no model, no answer key, no network. The three cases
below are the ones the 2026-08-16 corpus sweep actually decided; the full
16-packet corpus stays on the `phase11-inspect-contract` branch.
"""

import pytest

from harness.contract_lint import ContractLintUnusable, impossible_paths


@pytest.fixture
def tree(tmp_path):
    (tmp_path / "src" / "svcs").mkdir(parents=True)
    (tmp_path / "src" / "svcs" / "_core.py").write_text("x = 1\n")
    (tmp_path / "src" / "svcs" / "flask.py").write_text("x = 1\n")
    return tmp_path


def test_a_path_in_the_tree_is_clean(tree):
    task = "Edit `src/svcs/_core.py` and rebind svc."
    assert impossible_paths(task, ["src/svcs/_core.py"], tree) == ()


def test_blocks_a_path_that_is_neither_in_the_tree_nor_writable(tree):
    # The real authored-draft defect: the tree has _core.py.
    task = "Add the guard to `src/svcs/container.py`."
    assert impossible_paths(task, ["src/svcs/_core.py"], tree) == (
        "src/svcs/container.py",
    )


def test_blocks_the_second_real_authored_defect(tree):
    # The tree has flask.py, not a flask/ package.
    task = "Register the extension in `src/svcs/flask/app.py`."
    assert impossible_paths(task, ["src/svcs/_core.py"], tree) == (
        "src/svcs/flask/app.py",
    )


def test_a_declared_new_file_is_allowed_because_creating_it_is_the_task(tree):
    # The committed `autowire` contract names a module that does not exist
    # yet. Judging absence alone would reject it.
    task = "Create `src/svcs/_autowire.py` with the autowire helpers."
    assert impossible_paths(task, ["src/svcs/_autowire.py"], tree) == ()


def test_reports_each_offending_path_once_in_order(tree):
    task = "Touch `src/svcs/a.py`, then `src/svcs/b.py`, then `src/svcs/a.py`."
    assert impossible_paths(task, ["src/svcs/_core.py"], tree) == (
        "src/svcs/a.py",
        "src/svcs/b.py",
    )


def test_bare_words_and_dotted_attributes_are_not_paths(tree):
    # Without the slash requirement this matches `aget`; without the
    # extension requirement it matches `app.router`.
    task = "Call `aget` and read `app.router.lifespan_context`."
    assert impossible_paths(task, ["src/svcs/_core.py"], tree) == ()


def test_refuses_to_judge_without_bounds(tree):
    with pytest.raises(ContractLintUnusable, match="writableFiles"):
        impossible_paths("Edit `src/svcs/x.py`.", [], tree)


def test_refuses_to_judge_without_a_tree(tmp_path):
    with pytest.raises(ContractLintUnusable, match="base tree"):
        impossible_paths("Body.", ["a/b.py"], tmp_path / "absent")
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_contract_lint.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'harness.contract_lint'`

- [ ] **Step 3: Write the implementation**

Create `harness/contract_lint.py`:

```python
"""Does the contract name a path that can be neither read nor created?

The one criterion of five that survived the 2026-08-16 measurement
(`phase11-inspect-contract`, "what survives"). Deterministic: no model,
no grader, no answer key, no network. That is what lets it run in the
product path, where there is no answer key to hold.

Deleted alongside it, and deliberately not reimplemented here:

- the *nomination* rule (which path the contract says to change), which
  tracked the shape of the line rather than what it asked for
- `mechanism_specificity` and `key_claims`, which compared the packet to
  one reference patch and so read a correct alternative solution as a
  defect

Symbol and line-number claims stay unjudged: contracts hedge them in
prose ("or the equivalent internal mechanism"), and a blocking layer that
fires on hedged prose rejects good packets.
"""

import re
from collections.abc import Sequence
from pathlib import Path

# A backticked token that looks like a repository path: a slash and a file
# extension, both required. Without the slash this matches bare words like
# `aget`; without the extension it matches `app.router`.
_PATH = re.compile(r"`([A-Za-z0-9_][A-Za-z0-9_./-]*/[A-Za-z0-9_.-]+\.[A-Za-z]{1,5})`")


class ContractLintUnusable(Exception):
    """The lint cannot judge -- a broken instrument, not a bad packet.

    Kept distinct because conflating the two is a bug this checker
    actually shipped once: its CLI leaked internal errors out as the exit
    code meaning "your packet is bad".
    """


def impossible_paths(
    task: str, writable_files: Sequence[str], base_tree: Path
) -> tuple[str, ...]:
    """Paths the contract names that can be neither read nor created.

    Empty when clean. A path absent from the tree but present in
    `writable_files` is a file the contract declares the implementer will
    create -- the whole shape of an add-a-module task, and judging
    absence alone rejected the committed `autowire` contract for naming
    the module that task exists to add.
    """
    if not writable_files:
        raise ContractLintUnusable(
            "cannot judge without writableFiles: the bounds are evidence, "
            "not decoration -- without them a declared new file is "
            "indistinguishable from a wrong one"
        )
    if not base_tree.is_dir():
        raise ContractLintUnusable(f"cannot judge without a base tree at {base_tree}")

    declared = set(writable_files)
    offending: list[str] = []
    for path in dict.fromkeys(_PATH.findall(task)):
        if (base_tree / path).is_file() or path in declared:
            continue
        offending.append(path)
    return tuple(offending)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_contract_lint.py -v`
Expected: PASS, 8 tests

- [ ] **Step 5: Commit**

```bash
uv run ruff format harness/contract_lint.py tests/test_contract_lint.py
uv run ruff check --fix harness/contract_lint.py tests/test_contract_lint.py
git add harness/contract_lint.py tests/test_contract_lint.py
git commit -m "feat(phase11): port the path lint, the one criterion that survived"
```

---

### Task 3: `--contract` in `deliver_candidate.py`, and `--prompt-file` removed

**Files:**
- Modify: `tools/deliver_candidate.py` (argument definitions ~104-182; validation ~192-223; prompt construction ~233-268; the `run_model` closure ~313-332; the final exit-code block ~380-386)
- Create: `tests/test_deliver_candidate_contract.py`

**Interfaces:**
- Consumes: `parse_contract_file`, `ContractFileError` (Task 1); `impossible_paths`, `ContractLintUnusable` (Task 2).
- Produces: `main(argv)` accepting `--contract <path>`; exit 4 for instrument fault.

**Context you need:** `main()` already builds `prompt`, `extensions`, and an optional `handoff` and passes them to `deliver()`. A `--contract-task` run sets `handoff` and serialises `handoff.contract` into `SATYRN_HANDOFF_CONTRACT` inside `run_model`. A `--contract` run needs the same env var and the same implementer extension, but has **no** `TypedHandoff` — no manifest, no baselines, no oracle command.

`BASELINES_ENV` is what the mutation engine uses for revision checking. Without a manifest there are no baselines, so pass `{}` — the engine treats an absent baseline as "this file is as found."

**This task carries AC-1: every refusal path must make zero model calls.** The tests assert that by patching `run_process` and asserting it was never called.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_deliver_candidate_contract.py`:

```python
"""tools/deliver_candidate.py --contract: the product path into the implementer.

AC-1 is the point of this file: every refusal happens before a model call.
Asserting only on the exit code would pass even if the call had already
happened, so each refusal test asserts `run_process` was never invoked.
"""

import pytest

import tools.deliver_candidate as deliver_candidate

CONTRACT = """\
---
writableFiles: [src/svcs/_core.py]
validation: pytest -q
---
# Enter async context managers

Append `(name, svc)` to `self._on_close`, rebind `svc`.
"""


@pytest.fixture
def repo(tmp_path):
    (tmp_path / "src" / "svcs").mkdir(parents=True)
    (tmp_path / "src" / "svcs" / "_core.py").write_text("x = 1\n")
    return tmp_path


@pytest.fixture
def no_model(monkeypatch):
    """Fail loudly if anything reaches the model. AC-1's instrument."""
    calls = []

    def explode(*args, **kwargs):
        calls.append(args)
        raise AssertionError("a model call was made on a refusal path")

    monkeypatch.setattr(deliver_candidate, "run_process", explode)
    monkeypatch.setattr(
        deliver_candidate, "check_model_server_alive", lambda *a, **k: None
    )
    return calls


def _run(repo, contract_path):
    return deliver_candidate.main(
        [
            "--repo", str(repo),
            "--task", "t",
            "--contract", str(contract_path),
            "--model", "omlx/test",
            "--skip-server-check",
        ]
    )


def test_missing_contract_file_refuses_without_calling_the_model(
    repo, tmp_path, no_model, capsys
):
    assert _run(repo, tmp_path / "absent.md") == 2
    assert no_model == []
    assert "no contract file" in capsys.readouterr().err


def test_invalid_contract_refuses_without_calling_the_model(
    repo, tmp_path, no_model, capsys
):
    bad = tmp_path / "bad.md"
    bad.write_text("---\nvalidation: pytest -q\n---\nBody.\n")
    assert _run(repo, bad) == 2
    assert no_model == []
    assert "writableFiles" in capsys.readouterr().err


def test_a_path_that_cannot_exist_refuses_without_calling_the_model(
    repo, tmp_path, no_model, capsys
):
    bad = tmp_path / "bad.md"
    bad.write_text(
        "---\nwritableFiles: [src/svcs/_core.py]\nvalidation: pytest -q\n---\n"
        "Add the guard to `src/svcs/container.py`.\n"
    )
    assert _run(repo, bad) == 2
    assert no_model == []
    err = capsys.readouterr().err
    assert "src/svcs/container.py" in err


def test_an_unusable_lint_exits_4_not_2(repo, tmp_path, no_model, monkeypatch, capsys):
    def unusable(*args, **kwargs):
        raise deliver_candidate.ContractLintUnusable("bounds vanished")

    monkeypatch.setattr(deliver_candidate, "impossible_paths", unusable)
    good = tmp_path / "good.md"
    good.write_text(CONTRACT)
    assert _run(repo, good) == 4
    assert no_model == []
    assert "instrument" in capsys.readouterr().err.lower()


def test_prompt_file_is_gone(repo, tmp_path):
    with pytest.raises(SystemExit):
        deliver_candidate.main(
            [
                "--repo", str(repo),
                "--task", "t",
                "--prompt-file", str(tmp_path / "p.md"),
                "--model", "omlx/test",
            ]
        )


def test_a_contract_run_sets_the_child_env_and_selects_the_implementer(
    repo, tmp_path, monkeypatch
):
    """The two seams that reach the child: the env var and the extension."""
    good = tmp_path / "good.md"
    good.write_text(CONTRACT)
    seen = {}

    def fake_deliver(repo_arg, task, prompt, run_model, validation, **kwargs):
        seen["prompt"] = prompt
        seen["validation"] = validation
        seen["writable"] = kwargs.get("writable")
        raise deliver_candidate.DeliveryRefused("stop here, the wiring is what we test")

    monkeypatch.setattr(deliver_candidate, "deliver", fake_deliver)
    monkeypatch.setattr(
        deliver_candidate, "check_model_server_alive", lambda *a, **k: None
    )
    assert _run(repo, good) == 2
    assert "Append `(name, svc)`" in seen["prompt"]
    assert seen["validation"] == ("pytest", "-q")
    assert seen["writable"] == ("src/svcs/_core.py",)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_deliver_candidate_contract.py -v`
Expected: FAIL — `--contract` is an unrecognised argument (`SystemExit: 2` from argparse) and `ContractLintUnusable` is not an attribute of the module.

- [ ] **Step 3: Add the imports and the argument**

In `tools/deliver_candidate.py`, add to the imports (after the `harness.candidate` import):

```python
from harness.contract_file import ContractFileError, parse_contract_file
from harness.contract_lint import ContractLintUnusable, impossible_paths
```

Replace the `--prompt-file` argument definition (currently at ~104-108) with:

```python
    parser.add_argument(
        "--contract",
        type=Path,
        default=None,
        help="a handoff contract file: YAML front-matter carrying the bounds "
        "(writableFiles, validation, and optionally readableFiles, knownFacts, "
        "acceptanceStrings), then the task prose as the body. This is the "
        "product path -- see the write-handoff-contract skill.",
    )
```

- [ ] **Step 4: Replace the argument validation**

The existing block validates `--prompt-file` against `--contract-task`. Replace those checks (the `if args.contract_task is None and not args.prompt_file:` and `if args.contract_task is not None and args.prompt_file:` clauses) with:

```python
    if args.contract_task is None and args.contract is None:
        parser.error("--contract is required (or --contract-task, harness-only)")
    if args.contract_task is not None and args.contract is not None:
        parser.error("--contract-task builds its own contract; do not also pass --contract")
```

Leave every `--contract-task` clause below it untouched.

- [ ] **Step 5: Build the contract, lint it, and refuse before the model**

Replace the `else:` branch that read the prompt file (currently `prompt = args.prompt_file.read_text() if args.prompt_file else ""`) with a full `elif`. The whole block now reads:

```python
    handoff: TypedHandoff | None = None
    file_contract: HandoffContract | None = None
    if args.contract_task is not None:
        ...  # unchanged --contract-task branch
    else:
        # Refuse before the worktree and before the first call. A contract
        # the implementer cannot satisfy is a bad packet, not a bad model,
        # and spending a call to discover that is what this phase exists to
        # stop: with no contract at all the child's whole system prompt is
        # "Do not call tools; report this configuration failure", so the
        # run burns its budget and reports "changed nothing".
        try:
            file_contract = parse_contract_file(args.contract)
        except ContractFileError as error:
            print(f"refused: {error}", file=sys.stderr)
            return 2

        declared = [f["path"] for f in file_contract["writableFiles"]]
        try:
            offending = impossible_paths(file_contract["task"], declared, args.repo)
        except ContractLintUnusable as fault:
            # Exit 4, not 2: "the tool cannot judge" must never read as
            # "your packet is bad".
            print(f"instrument fault: {fault}", file=sys.stderr)
            return 4
        if offending:
            print(
                "refused: the contract names "
                + ", ".join(offending)
                + " -- neither in the base tree nor in writableFiles, so it can "
                "be neither read nor created",
                file=sys.stderr,
            )
            return 2

        prompt = _render_contract_prompt(file_contract)
        if args.validation is None:
            args.validation = file_contract["validation"]
        if args.writable is None:
            args.writable = declared
```

- [ ] **Step 6: Select the implementer extension and set the child env**

The `extensions` and `digest_extensions` assignments currently branch on `args.contract_task is not None`. A file contract needs the same child. Change both conditions to:

```python
    contract_run = args.contract_task is not None or file_contract is not None
    extensions = (IMPLEMENTER_EXTENSION,) if contract_run else (PROBE_EXTENSION,)
    digest_extensions = (
        IMPLEMENTER_EXTENSION_CLOSURE if contract_run else (PROBE_EXTENSION,)
    )
```

Inside `run_model`, extend the env seam. The existing `if handoff is not None:` block stays; add:

```python
        elif file_contract is not None:
            # No manifest, so no baselines: the engine treats an absent
            # baseline as "this file is as found".
            env[CONTRACT_ENV] = json.dumps(file_contract)
            env[BASELINES_ENV] = json.dumps({})
```

- [ ] **Step 7: Run the tests to verify they pass**

Run: `uv run pytest tests/test_deliver_candidate_contract.py -v`
Expected: PASS, 6 tests

- [ ] **Step 8: Run the whole Python suite for regressions**

Run: `uv run pytest -q`
Expected: PASS. `--contract-task` behaviour is unchanged, so `tests/test_typed_contract.py` and the batch-driver tests must still pass. If any test invokes `--prompt-file`, update it to `--contract` with a fixture contract file — do not restore the flag.

- [ ] **Step 9: Commit**

```bash
uv run ruff format tools/deliver_candidate.py tests/test_deliver_candidate_contract.py
uv run ruff check --fix tools/deliver_candidate.py tests/test_deliver_candidate_contract.py
git add tools/deliver_candidate.py tests/test_deliver_candidate_contract.py
git commit -m "feat(phase11): --contract drives the implementer, and refuses before the call"
```

---

### Task 4: `/implement <contract-file>`

**Files:**
- Modify: `packages/engine/orchestrator.ts:7-56`
- Create: `packages/engine/orchestrator.test.ts`
- Modify: `package.json:6` (widen the test glob)
- Modify: `tests/test_orchestrator_command.py:26-48` (the existing Python test drives the TS builder under `bun -e` and asserts `--prompt-file`)

**Interfaces:**
- Consumes: the `--contract` flag from Task 3.
- Produces: `buildDeliverCandidateArgv({repo, task, contractPath, model}) -> string[]` — note `promptFile` and `validation` are **gone**; validation now comes from the contract file.

**Context you need:** The command currently writes the user's text to a temp file and passes `--prompt-file`, with `validation` hardcoded to `pytest -q`. Both go away. The argument is now a path to a contract file the agent has already written.

- [ ] **Step 1: Write the failing test**

Create `packages/engine/orchestrator.test.ts`:

```typescript
import { expect, test } from "bun:test";
import { buildDeliverCandidateArgv } from "./orchestrator";

test("passes the contract path through and no longer hardcodes validation", () => {
	const argv = buildDeliverCandidateArgv({
		repo: "/repo",
		task: "enter-async-cms",
		contractPath: "/tmp/contract.md",
		model: "omlx/gemma-4-12B-it-MLX-8bit",
	});
	expect(argv).toEqual([
		"run", "python", "-m", "tools.deliver_candidate",
		"--repo", "/repo",
		"--task", "enter-async-cms",
		"--contract", "/tmp/contract.md",
		"--model", "omlx/gemma-4-12B-it-MLX-8bit",
	]);
	expect(argv).not.toContain("--prompt-file");
	expect(argv).not.toContain("--validation");
});
```

- [ ] **Step 2: Widen the test glob and run the test to verify it fails**

In `package.json`, change the test script:

```json
"test": "bun test extensions/ packages/"
```

Run: `bun test packages/engine/orchestrator.test.ts`
Expected: FAIL — the argv contains `--prompt-file` and `--validation`.

- [ ] **Step 3: Rewrite the command**

Replace the whole body of `packages/engine/orchestrator.ts` with:

```typescript
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { spawn } from "node:child_process";

export function buildDeliverCandidateArgv(opts: {
	repo: string;
	task: string;
	contractPath: string;
	model: string;
}): string[] {
	return [
		"run", "python", "-m", "tools.deliver_candidate",
		"--repo", opts.repo,
		"--task", opts.task,
		"--contract", opts.contractPath,
		"--model", opts.model,
	];
}

function slugify(text: string): string {
	return text.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 40) || "task";
}

const USAGE =
	"Usage: /implement <contract-file> — a handoff contract, not a prompt. " +
	"Ask me to write one first (see the write-handoff-contract skill).";

export default function (pi: ExtensionAPI) {
	pi.registerCommand("implement", {
		description: "Drive the bounded implementer with a handoff contract file.",
		handler: async (args, ctx) => {
			const contractPath = args.trim();
			if (!contractPath) {
				ctx.ui.notify(USAGE, "warning");
				return;
			}
			const argv = buildDeliverCandidateArgv({
				repo: ctx.cwd,
				task: slugify(contractPath.split("/").pop() ?? "task"),
				contractPath,
				model: ctx.model
					? `${ctx.model.provider}/${ctx.model.id}`
					: "omlx/gemma-4-12B-it-MLX-8bit",
			});
			ctx.ui.notify(`Orchestrating: ${argv.join(" ")}`, "info");
			const child = spawn("uv", argv, { cwd: ctx.cwd });
			child.stdout.on("data", (d) => ctx.ui.notify(String(d).trim(), "info"));
			child.stderr.on("data", (d) => ctx.ui.notify(String(d).trim(), "warning"));
			child.on("error", (e) => ctx.ui.notify(`Could not start uv: ${e.message}`, "warning"));
		},
	});
}
```

- [ ] **Step 4: Update the existing Python test of the argv builder**

`tests/test_orchestrator_command.py` drives the TS builder under `bun -e`
with the old keyword arguments. Replace the body of
`test_the_argv_builder_maps_the_inputs` (lines 26-48) with:

```python
def test_the_argv_builder_maps_the_inputs():
    # Run the TS builder under bun and check the argv it prints.
    out = subprocess.run(
        [
            "bun",
            "-e",
            f"import {{ buildDeliverCandidateArgv }} from '{ORCHESTRATOR}';"
            "console.log(buildDeliverCandidateArgv({"
            "repo: '/repo', task: 'add-health', contractPath: '/tmp/c.md',"
            "model: 'omlx/gemma-4-12B-it-MLX-8bit'"
            "}).join(' '))",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    argv = out.stdout.strip()
    assert "tools.deliver_candidate" in argv
    assert "--repo /repo" in argv
    assert "--task add-health" in argv
    assert "--contract /tmp/c.md" in argv
    # Validation now comes from the contract file, not the command line.
    assert "--prompt-file" not in argv
    assert "--validation" not in argv
    assert "--model omlx/gemma-4-12B-it-MLX-8bit" in argv
```

- [ ] **Step 5: Run both suites to verify they pass**

Run: `bun test`
Expected: PASS — the new test plus the existing `extensions/` suites.

Run: `uv run pytest tests/test_orchestrator_command.py -v`
Expected: PASS, 3 tests.

- [ ] **Step 6: Commit**

```bash
git add packages/engine/orchestrator.ts packages/engine/orchestrator.test.ts package.json tests/test_orchestrator_command.py
git commit -m "feat(phase11): /implement takes a contract file, not a prompt"
```

---

### Task 5: The authoring skill

**Files:**
- Create: `.claude/skills/write-handoff-contract/SKILL.md`

**Interfaces:**
- Consumes: the file format from Task 1.
- Produces: nothing executable — instructions only.

**Context you need:** This is the deliverable that makes the phase usable, and it is prose. The two things it must get right are the two the measurements identified: bounds are *declared*, and the body names **concrete operations**. The contract that scores 8/8 says *"append `(name, svc)` to `self._on_close`, rebind `svc`"*; the draft that scores 0/8 with every run collapsing into no-op edits says *"register the resulting cleanup mechanism"*.

- [ ] **Step 1: Write the skill**

Create `.claude/skills/write-handoff-contract/SKILL.md`:

```markdown
---
name: write-handoff-contract
description: Use when the user wants to hand a coding task to the local bounded implementer via /implement — writes the handoff contract file that /implement consumes. Trigger on "write a contract", "hand this to the implementer", or before running /implement.
---

# Writing a handoff contract

`/implement <file>` runs a small local model against one task, confined to
the files you declare. It cannot plan and it cannot derive a change: handed
a concrete recipe it applies it near-perfectly, and handed a description of
a desired outcome it stalls or edits nothing. **You are the planner. The
contract is the recipe.**

## Before you write

Read the code. The contract's value is entirely in naming real
operations on real files, and every path you name is checked against the
tree before any model call.

## The file

````markdown
---
writableFiles: [src/svcs/_core.py]
readableFiles: [src/svcs/**, tests/**]
validation: pytest -q
knownFacts:
  - The app is ASGI, not WSGI.
---
# Enter async context managers in aget()

`Container.aget()` resolves a factory and returns the value. When the
factory returns an async context manager it must be entered.

In `aget()`, after `_lookup` returns `(cached, svc, rs)` and before the
`isawaitable(svc)` branch: if `svc` is an `AbstractAsyncContextManager`
and `rs.enter` is true, `await svc.__aenter__()`, append `(name, svc)` to
`self._on_close`, and rebind `svc` to the entered value.

Follow the pattern already in `get()`, which does the synchronous form.

Leave the `isawaitable` branch and all caching behaviour unchanged.
````

`writableFiles` and `validation` are required. Everything else is optional.

## The rule that decides whether this works

**Name the operation, not the intention.**

| Works (measured 8/8) | Fails (measured 0/8) |
|---|---|
| ``append `(name, svc)` to `self._on_close` `` | "register the resulting cleanup mechanism" |
| ``insert before the `isawaitable(svc)` branch`` | "place the guard appropriately" |
| ``follow the pattern in `get()` `` | "handle the async case similarly" |

The second column reads like a specification and produces runs where the
model emits the same no-op edit nine times and writes nothing at all.

## The rest

- **Bounds are declared, never implied.** A file the implementer must
  change goes in `writableFiles` even if the body names it. A file that
  does not exist yet is fine there — that is how you say "create this".
- **Every backticked path must exist in the tree or be in
  `writableFiles`.** Otherwise `/implement` refuses before spending a
  model call, naming the path.
- **`knownFacts` is for what the tree cannot reveal** — a deployment
  detail, a runtime constraint. One sentence measured as well as a whole
  stack description; do not pad it.
- **Name what must not change.** The implementer is confined but not
  careful.
- **`validation` is what the parent runs to judge the result.** The
  implementer never runs it.

## Then

Save it (a scratch path is fine) and run `/implement <path>`. On refusal,
fix the contract — a refusal costs no model call and names its cause.
```

- [ ] **Step 2: Verify the front-matter parses and the fenced example is well-formed**

Run:

```bash
uv run python -c "
import pathlib, yaml
text = pathlib.Path('.claude/skills/write-handoff-contract/SKILL.md').read_text()
head = text.split('---')[1]
meta = yaml.safe_load(head)
assert meta['name'] == 'write-handoff-contract', meta
assert len(meta['description']) > 40, 'description must say when to trigger'
print('skill front-matter ok:', meta['name'])
"
```

Expected: `skill front-matter ok: write-handoff-contract`

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/write-handoff-contract/SKILL.md
git commit -m "feat(phase11): the write-handoff-contract skill"
```

---

### Task 6: The smoke test

**Files:**
- Create: `docs/superpowers/research/2026-08-16-phase11-contract-file-smoke.md`

**Interfaces:**
- Consumes: everything above.
- Produces: a one-page record. No code.

**Context you need:** This is **one live run and it is not a measurement.** The pre-registration discipline this project runs under means an n=1 result must never be quoted as a rate. The question is only: does the path work end to end?

Preconditions: the model server is up at `127.0.0.1:8001` (verify with a real completion — `/v1/models` advertises models it cannot serve), and no other live batch is running (there is one server; two batches corrupt each other's timings).

- [ ] **Step 1: Write the contract using the skill**

In a session with the repository open, use the `write-handoff-contract` skill to write a contract for `async-cm-enter` against a clean `svcs` checkout at the task's `base_sha`. Save it to `/tmp/smoke-async-cm-enter.md`.

Do **not** copy `workloads/svcs/contracts/locating/async-cm-enter.md`. The point is whether the skill produces a working contract.

- [ ] **Step 2: Run it**

```bash
uv run python -m tools.deliver_candidate --repo <svcs-checkout> --task smoke-async-cm --contract /tmp/smoke-async-cm-enter.md --model omlx/gemma-4-12B-it-MLX-8bit --receipt /tmp/smoke-receipt.json
```

Expected: exit 0 and a candidate ref, or exit 1 with a reason. Either outcome completes the task — a wiring check passes when the machinery behaves, not when the model succeeds.

- [ ] **Step 3: Check a refusal path against the real CLI**

```bash
printf -- '---\nwritableFiles: [src/svcs/_core.py]\nvalidation: pytest -q\n---\nEdit `src/svcs/container.py`.\n' > /tmp/bad-contract.md
uv run python -m tools.deliver_candidate --repo <svcs-checkout> --task smoke-refusal --contract /tmp/bad-contract.md --model omlx/gemma-4-12B-it-MLX-8bit
echo "exit: $?"
```

Expected: `exit: 2`, a message naming `src/svcs/container.py`, and — the point of AC-1 — it returns in well under a second, because no model call is made.

- [ ] **Step 4: Write the record**

Create `docs/superpowers/research/2026-08-16-phase11-contract-file-smoke.md` with: the contract used (inline), the receipt's `outcome`, wall-clock, `pi --version`, the model string, and the refusal check's exit code and duration.

State in the first line: **n=1, a wiring check, not a rate.**

- [ ] **Step 5: Commit**

```bash
git add docs/superpowers/research/2026-08-16-phase11-contract-file-smoke.md
git commit -m "docs(phase11): contract-file smoke test -- n=1, a wiring check"
```

---

## Self-review

**Spec coverage:**

| Spec requirement | Task |
|---|---|
| AC-1: refuse with zero model calls | 3 (tests assert `run_process` never called) |
| Authoring affordance (decided: a skill) | 5 |
| `/implement <contract-file>` | 4 |
| `--prompt-file` removed | 3, 4 |
| `--contract-task` untouched | Global constraints; 3 step 4 |
| Path lint as a rule, not the framework | 2 |
| Refuse-without-bounds guard | 1 (schema) and 2 (lint guard) |
| Distinct exits for bad packet vs instrument fault | 3 (2 vs 4) |
| Only `writableFiles` + `validation` required | 1 |
| Corpus lessons as fixtures | 2 (container.py, flask/app.py, autowire) |
| One smoke test, marked as such | 6 |

**Deferred by the spec, absent here on purpose:** the fixture export and its round-trip pin; F5; `MAX_PROPOSAL_BYTES`; any content criterion; any authoring measurement.

**Type consistency:** `parse_contract_file(path) -> HandoffContract` (Task 1) feeds `impossible_paths(task, writable_files, base_tree) -> tuple[str, ...]` (Task 2) via `[f["path"] for f in contract["writableFiles"]]` (Task 3). `ContractFileError` → exit 2; `ContractLintUnusable` → exit 4. `buildDeliverCandidateArgv` takes `contractPath` in both Task 4's test and its implementation.

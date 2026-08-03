# Pi version pin implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `run_batch` refuse to produce evidence against any Pi version other than the one this repository pins, so batches stay comparable between contributors and an upgrade becomes a deliberate commit.

**Architecture:** One module constant and one comparison in `harness/runner.py`. `_conditions()` already shells `pi --version` to populate `RunConditions.pi_version`, and `run_batch` already calls it — so the check reads a value already in hand and adds no subprocess, no module, and no exception class.

**Tech Stack:** Python 3.14, pytest, ruff, pyrefly, Sphinx (MyST).

**Design:** `docs/superpowers/specs/2026-08-03-pi-version-pin-design.md`

## Global Constraints

- Python `>=3.14,<3.15`. No new runtime dependencies.
- Gates, all four before any commit: `uv run pytest`, `uv run ruff check .`, `uv run pyrefly check`, `uv run sphinx-build -W -b html docs docs/_build/html`.
- Ruff lint selects `E,F,I,UP,B,SIM`; `E501` ignored. Import sorting enforced.
- **Batch scope only.** The check goes in `run_batch` and nowhere else. `run_agentclinic_phase1()` and the test suite must stay runnable on any Pi version — a contributor exploring the harness is never blocked, only evidence production is.
- **No override.** No environment variable, no flag, no parameter to skip the check. A contributor who wants a batch on a newer Pi bumps the constant.
- Do not add a new module, a named exception class, a second `pi --version` subprocess, or handling for a missing `pi` binary. All four were deliberately removed from the design; `subprocess.run(..., check=True)` inside `_conditions` already raises `FileNotFoundError` and `CalledProcessError` earlier and with better messages.
- Work happens on branch `pi-pin` in the worktree at `.worktrees/pi-pin`.
- The installed Pi is **0.83.0**. Confirm with `pi --version` rather than trusting this line.

---

## File Structure

| File | Responsibility | Change |
|---|---|---|
| `harness/runner.py` | Pi invocation, run conditions, batch contract | Modify — constant + check |
| `tests/test_runner.py` | Runner unit tests | Modify — three tests |
| `docs/setup.md` | Contributor setup | Modify — state the pin |
| `ROADMAP.md` | Backlog | Modify — retire the entry that asked for this |

---

## Task 1: The pin

**Files:**
- Modify: `harness/runner.py` (constant beside `DEFAULT_MODEL`; check inside `run_batch`)
- Modify: `tests/test_runner.py`

**Interfaces:**
- Consumes: `RunConditions.pi_version`, already populated by `_conditions()`.
- Produces: `harness.runner.EXPECTED_PI_VERSION: str`. Task 2's documentation names it.

- [ ] **Step 1: Confirm the installed version**

Run: `pi --version`
Expected: `0.83.0`. If it prints something else, use *that* value as the constant throughout this task and say so in your report — the pin records what this repository actually runs against, not what a plan written earlier assumed.

- [ ] **Step 2: Write the failing tests**

Append to `tests/test_runner.py`:

```python
def test_run_batch_refuses_a_pi_version_other_than_the_pinned_one(
    tmp_path, monkeypatch
):
    # Two contributors on different Pi versions would each produce an
    # internally valid batch, and those batches would be compared as
    # though they were comparable. They are not.
    conditions = RunConditions(
        "model", ("pi",), "0.1.0-not-pinned", "sha", "rev", 600, 30,
        ("digest",), "agentsha",
    )
    monkeypatch.setattr(runner, "_conditions", lambda *args: conditions)

    with pytest.raises(RuntimeError, match="0.1.0-not-pinned"):
        runner.run_batch(tmp_path / "checkpoint.jsonl", target=1, model="model")


def test_the_refusal_names_the_version_it_expected(tmp_path, monkeypatch):
    conditions = RunConditions(
        "model", ("pi",), "0.1.0-not-pinned", "sha", "rev", 600, 30,
        ("digest",), "agentsha",
    )
    monkeypatch.setattr(runner, "_conditions", lambda *args: conditions)

    with pytest.raises(RuntimeError, match=runner.EXPECTED_PI_VERSION):
        runner.run_batch(tmp_path / "checkpoint.jsonl", target=1, model="model")


def test_run_batch_proceeds_on_the_pinned_version(tmp_path, monkeypatch):
    # Without this the check could be refusing every batch and the two
    # tests above would still pass.
    conditions = RunConditions(
        "model", ("pi",), runner.EXPECTED_PI_VERSION, "sha", "rev", 600, 30,
        ("digest",), "agentsha",
    )
    monkeypatch.setattr(runner, "_conditions", lambda *args: conditions)

    records = runner.run_batch(tmp_path / "checkpoint.jsonl", target=0)

    assert records == []


def test_the_pinned_version_is_the_installed_version():
    # The one test designed to fail on the next upgrade. That is the
    # point: it turns a silent drift into a red suite. Pi moved 0.82.0 ->
    # 0.83.0 during a working session and nothing caught it; eight
    # file:line citations in a published chapter went stale.
    installed = subprocess.run(
        ["pi", "--version"], check=True, capture_output=True, text=True
    ).stdout.strip()

    assert installed == runner.EXPECTED_PI_VERSION
```

`subprocess` is not currently imported in `tests/test_runner.py` — check the import block and add `import subprocess` if absent. Ruff enforces import sorting.

Note `target=0` in the third test: `run_batch` returns early once `len(records) >= target`, so it exercises the version check and then returns without running a model. Read `run_batch` to confirm the ordering before relying on it.

- [ ] **Step 3: Run the tests to verify they fail**

Run: `uv run pytest tests/test_runner.py -k "pinned or pi_version" -v`
Expected: `test_the_pinned_version_is_the_installed_version` FAILS with `AttributeError: module 'harness.runner' has no attribute 'EXPECTED_PI_VERSION'`, and the refusal tests FAIL because no exception is raised.

- [ ] **Step 4: Add the constant**

In `harness/runner.py`, beside `DEFAULT_MODEL`:

```python
EXPECTED_PI_VERSION = "0.83.0"
```

- [ ] **Step 5: Add the check**

In `run_batch`, immediately after `requested = _conditions(model, command, 600, extensions)` and before the loop over `records`:

```python
    if requested.pi_version != EXPECTED_PI_VERSION:
        raise RuntimeError(
            f"this harness pins Pi {EXPECTED_PI_VERSION}, but {requested.pi_version} "
            f"is installed. Batches are pinned so that runs stay comparable "
            f"between contributors. Either install Pi {EXPECTED_PI_VERSION}, or "
            f"bump EXPECTED_PI_VERSION in harness/runner.py -- and if you bump it, "
            f"re-check the documentation that cites Pi by file and line, because "
            f"those citations do not survive upgrades and no test catches them."
        )
```

Placing it here means it fires before `preflight_model` spends a model call, and before the checkpoint comparison — a contributor with a mismatched Pi learns *why* rather than seeing a conditions mismatch.

- [ ] **Step 6: Run the tests to verify they pass**

Run: `uv run pytest tests/test_runner.py -v`
Expected: all PASS.

- [ ] **Step 7: Run the full gates**

Run: `uv run pytest && uv run ruff check . && uv run pyrefly check`
Expected: all pass.

- [ ] **Step 8: Commit**

```bash
git add harness/runner.py tests/test_runner.py
git commit -m "feat(pi-pin): refuse a batch on any Pi but the pinned version

_conditions already shells \`pi --version\`, so this reads a value already
in hand: one constant and one comparison, no new module and no second
subprocess.

Batch-scoped -- run_batch is the only caller, so exploring the harness and
running the suite stay unblocked. No override: bumping the constant is a
one-line commit that leaves a record, which is the decision we want an
upgrade to be.

One test asserts the constant matches the installed version, and is meant
to fail on the next upgrade.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Task 2: Say so where a contributor will look

**Files:**
- Modify: `docs/setup.md` (the `### Pi` section, around lines 74-90)
- Modify: `ROADMAP.md` (the Backlog entry that requested this work)

**Interfaces:**
- Consumes: `EXPECTED_PI_VERSION` from Task 1.
- Produces: documentation only.

- [ ] **Step 1: Update `docs/setup.md`**

The `### Pi` section currently says a mismatch breaks nothing and points at an open Backlog decision. That decision is now made. Replace that paragraph so it states:

- the harness pins the version, and where the constant lives (`EXPECTED_PI_VERSION` in `harness/runner.py`)
- that **batches** refuse to run on any other version, and that single runs and the test suite do not — so exploring is unaffected
- what to do when yours differs: install the pinned version, or bump the constant and re-check the docs that cite Pi by file and line
- why the pin exists, in one sentence: so two contributors' batches are comparable

Keep the existing `pi --version` example, updated if Task 1 found a different installed version.

- [ ] **Step 2: Retire the Backlog entry**

In `ROADMAP.md`, the Backlog entry beginning **"Pin the Pi version the harness runs against"** asked for exactly this work. Replace it with a short record that it was done, keeping the reasoning that motivated it — follow the format the Backlog already uses for completed entries (search it for "gate satisfied" and "promoted to" to see how a done entry is written).

The record should keep: that Pi moved 0.82.0 → 0.83.0 mid-session, that mechanisms survived but eight citations did not, and that no test could catch a stale citation. It should note what the pin does *not* solve — documentation drift is still uncaught; the pin only makes the upgrade a moment someone decides on.

- [ ] **Step 3: Check nothing else still calls this an open question**

Run: `grep -rn "Pin the Pi version" docs/ ROADMAP.md BRIEF.md | grep -v _build`

Every hit should now read as settled rather than pending. Fix any that still describe it as an open decision.

- [ ] **Step 4: Verify the docs build**

Run: `rm -rf docs/_build && uv run sphinx-build -W -b html docs docs/_build/html`
Expected: `build succeeded.`

- [ ] **Step 5: Run the full gates**

Run: `uv run pytest && uv run ruff check . && uv run pyrefly check`
Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add docs/setup.md ROADMAP.md
git commit -m "docs(pi-pin): record the pin where a contributor will meet it

setup.md said a version mismatch broke nothing and pointed at an open
Backlog decision. The decision is made: batches refuse, single runs and the
suite do not.

The Backlog entry becomes a record of what was done and what it does not
solve -- documentation drift is still uncaught, and the pin only makes the
upgrade a moment someone decides on.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Done when

- `run_batch` raises on any `pi_version` other than `EXPECTED_PI_VERSION`, with a message naming both versions and both remedies
- A single run and the test suite still work on any Pi version
- A test asserts the constant matches the installed version, and will fail on the next upgrade
- A test proves a matching version still proceeds, so the check cannot be refusing everything
- `docs/setup.md` states the pin, its scope, and what to do about a mismatch
- The Backlog entry is a record rather than a request, and says what the pin does not solve
- All four gates pass

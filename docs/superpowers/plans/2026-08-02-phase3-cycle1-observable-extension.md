# Phase 3, Cycle 1 — Observable extension implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make one custom entry travel from `.pi/extensions/hello-world.ts` through captured stdout into `read_telemetry`, and leave behind the extension seam and run-conditions digest that Phase 3 cycle 2 needs.

**Architecture:** The extension's `appendEntry` call moves from `session_start` (emitted before print mode subscribes, therefore dropped) to `agent_start` (emitted after). `read_telemetry` gains a `custom_entries` field reading `entry_appended` events. `harness/runner.py`'s single hardcoded extension path becomes a tuple with one caller, and `RunConditions` gains a SHA-256 per extension file so editing an extension invalidates a checkpoint the way editing the task spec already does.

**Tech Stack:** Python 3.14, pytest, ruff, pyrefly, Sphinx (MyST), TypeScript extension against `@earendil-works/pi-coding-agent` 0.82.0.

**Design:** `docs/superpowers/specs/2026-08-02-phase3-cycle1-observable-extension-design.md`

> **One figure below is stale, and is left stale deliberately.** This plan says
> "48 inert runs" in two places. The true census is **80** — cycle 3's clean
> baseline had already added 32 runs when this plan was written, and nobody
> noticed. The corrected figure and how it was verified are in
> [the event vocabulary note](../research/2026-08-02-phase3-cycle1-event-vocabulary.md).
> A plan records the instructions an implementer was actually given; editing it
> after the fact would make the record of the error disappear along with the
> error.

## Global Constraints

- Python `>=3.14,<3.15`. No new runtime dependencies.
- Gates, all four must pass before any commit: `uv run pytest`, `uv run ruff check .`, `uv run pyrefly check`, and `uv run sphinx-build -W -b html docs docs/_build/html`.
- Ruff lint selects `E,F,I,UP,B,SIM`; `E501` (line length) is ignored. Import sorting is enforced.
- **Never `git commit` while a `run_batch()` is in flight.** A concurrent commit changes `harness_revision` and aborts the batch.
- Runs are sequential, never concurrent — one shared local model has no isolation.
- The live model server must be verified alive before any live run, via `harness.liveness.check_model_server_alive()`. When it is down, `pi` exits 0 with empty stderr and the harness records a fabricated result that looks like data.
- Work happens on branch `phase3` in the worktree at `.worktrees/phase3`.
- Every new doc must be added to a toctree in `docs/superpowers/index.md`, or the strict Sphinx gate fails.

---

## File Structure

| File | Responsibility | Change |
|---|---|---|
| `.pi/extensions/hello-world.ts` | The extension under study; lifecycle tour plus one evidence entry | Modify |
| `harness/telemetry.py` | Derived measurements from one run's stdout | Modify — add `custom_entries` |
| `harness/runner.py` | Pi invocation, run conditions, batch contract | Modify — extension seam + digests |
| `harness/checkpoint.py` | Round-trips `RunResult` to JSONL | Modify — deserialize the new field |
| `tests/test_telemetry.py` | Telemetry unit tests | Modify |
| `tests/test_runner.py` | Runner unit tests + the live test | Modify |
| `tests/test_checkpoint.py` | Checkpoint round-trip tests | Modify |
| `tests/fixtures/pi-run-0.82.0-entry-appended.jsonl` | Captured stdout of a real run carrying an `entry_appended` | Create (Task 1) |
| `docs/superpowers/research/2026-08-02-phase3-cycle1-event-vocabulary.md` | What an extension can emit under our flags | Create (Task 5) |
| `ROADMAP.md` | Phase 3 entry and cycle 1 row | Modify (Task 5) |
| `docs/superpowers/index.md` | Toctrees | Modify (Tasks 5, 6) |
| `docs/superpowers/chapters/hello-agent.md` | The teaching artifact | Create (Task 6) |

---

## Task 1: The gating spike — prove `entry_appended` reaches stdout

This task is a falsification test for the design's central hypothesis. **If its live run shows no `entry_appended`, stop and report — do not proceed to Task 2.** The remaining tasks all assume the path works.

**Files:**
- Modify: `.pi/extensions/hello-world.ts:5-11` and `:14-16`
- Modify: `tests/test_runner.py` (append a new live test)
- Create: `tests/fixtures/pi-run-0.82.0-entry-appended.jsonl`

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces: the fixture file `tests/fixtures/pi-run-0.82.0-entry-appended.jsonl`, a captured Pi stdout stream containing at least one line whose parsed JSON has `type == "entry_appended"` and `entry.customType == "evidence"`. Tasks 2 and 4 read this file.

- [ ] **Step 1: Move the evidence entry past the subscribe boundary**

Edit `.pi/extensions/hello-world.ts`. Replace the `session_start` handler (lines 5-11) and the `agent_start` handler (lines 14-16) with:

```ts
  // ── session_start: the session comes to life ──────────────────────
  pi.on("session_start", async (_event, ctx) => {
    ctx.ui.notify("Session started!", "info");
  });

  // ── agent_start: the LLM wakes up ─────────────────────────────────
  pi.on("agent_start", async (_event, ctx) => {
    ctx.ui.notify("Agent started — LLM turn beginning", "info");

    // Write an evidence entry into the session.
    // pi.appendEntry(customType, data?) — first arg is a string type ID.
    //
    // This must happen *after* print mode subscribes to session events.
    // `bindExtensions` awaits the `session_start` emission, and the
    // json-mode subscriber is attached only once it returns — so an
    // entry appended during `session_start` is emitted with no
    // subscriber and dropped. That, not `--no-session`, is why 48
    // recorded runs produced nothing. `agent_start` fires during
    // `session.prompt()`, at least once per run and before any
    // model-dependent behaviour. Not exactly once: Pi retries after
    // some agent errors, and a retry fires it again.
    //
    // No timestamp in the payload: the session entry already carries
    // its own, and a second wall-clock value makes every captured
    // stdout differ from the last for no gain.
    pi.appendEntry("evidence", { event: "agent_start" });
  });
```

- [ ] **Step 2: Write the failing live test**

`tests/test_runner.py` imports `os` and `pytest` but **not** `json`. Add to the standard-library import block at the top of the file:

```python
import json
```

Then append the test:

```python
@pytest.mark.skipif(
    os.environ.get("SATYRN_LIVE") != "1",
    reason="set SATYRN_LIVE=1 to require an actual Pi/model run",
)
def test_the_extension_emits_an_evidence_entry_into_captured_stdout():
    # The cycle's whole claim: one entry travels extension -> stdout.
    #
    # Parsed tolerantly rather than substring-filtered: an assistant
    # message quoting "entry_appended", or a truncated final line, would
    # otherwise crash this test instead of failing it -- and a crash
    # reads as a broken test rather than a falsified hypothesis.
    appended = []
    for line in run_agentclinic_phase1().pi_stdout.split("\n"):
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(event, dict) and event.get("type") == "entry_appended":
            appended.append(event)

    assert appended, "no entry_appended event reached stdout"
    assert any(
        event.get("entry", {}).get("customType") == "evidence"
        for event in appended
    )
```

- [ ] **Step 3: Verify the model server is alive**

Run: `uv run python -c "from harness.liveness import check_model_server_alive; check_model_server_alive(); print('alive')"`
Expected: prints `alive`. If it raises, run `/Users/pauleveritt/.omlx/bin/omlx start` and re-check.

**Do not proceed on a dead server** — `pi` exits 0 with empty output when the server is down, and the spike would look like a clean falsification of the hypothesis when it is only a dead server. That is the single most expensive way this task can go wrong.

(`omlx diagnose` is not the check: the installed CLI requires a target argument, `omlx diagnose menubar`, which reports on the menubar app rather than the served model.)

- [ ] **Step 4: Run the live test**

Run: `SATYRN_LIVE=1 uv run pytest tests/test_runner.py::test_the_extension_emits_an_evidence_entry_into_captured_stdout -v`
Expected: PASS.

If it FAILS with "no entry_appended event reached stdout", the hypothesis is falsified. **Stop here.** Record what the stdout actually contained and report back; the cycle re-plans rather than proceeding.

- [ ] **Step 5: Capture the fixture**

Run:

```bash
uv run python -c "
from pathlib import Path
from harness.runner import run_agentclinic_phase1
result = run_agentclinic_phase1()
Path('tests/fixtures/pi-run-0.82.0-entry-appended.jsonl').write_text(result.pi_stdout)
print('captured', len(result.pi_stdout.split(chr(10))), 'lines')
"
```

Expected: prints a line count well above 50.

- [ ] **Step 6: Verify the fixture carries the evidence**

Run: `grep -c entry_appended tests/fixtures/pi-run-0.82.0-entry-appended.jsonl`
Expected: `1` or greater.

- [ ] **Step 7: Record the fixture's provenance**

`tests/fixtures/README.md` records SHA-256, provenance, and known-good values for every committed fixture, and tests cite it as the record. Add a section for the new fixture following the existing `pi-run-0.82.0.jsonl` section's shape:

```bash
shasum -a 256 tests/fixtures/pi-run-0.82.0-entry-appended.jsonl
wc -l -c tests/fixtures/pi-run-0.82.0-entry-appended.jsonl
grep -c entry_appended tests/fixtures/pi-run-0.82.0-entry-appended.jsonl
```

The section must state: the SHA-256, the line and byte counts, that it is `pi_stdout` from a live `run_agentclinic_phase1()` against `omlx/gemma-4-12B-it-MLX-8bit` under Pi 0.82.0, the count of `entry_appended` events, and that it is the first fixture captured with the extension appending from `agent_start`.

- [ ] **Step 8: Run the full gates**

Run: `uv run pytest && uv run ruff check . && uv run pyrefly check`
Expected: all pass, **two skipped** — the pre-existing `test_run_agentclinic_phase1_produces_live_model_evidence` and the new one, both gated on `SATYRN_LIVE=1`.

- [ ] **Step 9: Commit**

```bash
git add .pi/extensions/hello-world.ts tests/test_runner.py tests/fixtures/pi-run-0.82.0-entry-appended.jsonl tests/fixtures/README.md
git commit -m "feat(phase3-cycle1): make the extension observable in print mode

Moving appendEntry from session_start to agent_start puts it after the
point where print mode subscribes to session events. The entry now
reaches captured stdout as entry_appended. Fixture captured from a live
run against omlx/gemma-4-12B-it-MLX-8bit.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Task 2: `read_telemetry` reads custom entries

**Files:**
- Modify: `harness/telemetry.py:30-56` (the `RunTelemetry` dataclass) and `:58-120` (`read_telemetry`)
- Modify: `tests/test_telemetry.py`

**Interfaces:**
- Consumes: `tests/fixtures/pi-run-0.82.0-entry-appended.jsonl` from Task 1.
- Produces: `RunTelemetry.custom_entries: tuple[str, ...]` — the `customType` of each `entry_appended` event whose `entry.type` is `"custom"`, in stdout order. Declared as the **last** field of the dataclass, after `complete`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_telemetry.py`:

```python
ENTRY_FIXTURE = Path(__file__).parent / "fixtures" / "pi-run-0.82.0-entry-appended.jsonl"


def test_reads_custom_entry_types_from_a_real_run():
    assert "evidence" in read_telemetry(ENTRY_FIXTURE.read_text()).custom_entries


def test_the_pre_cycle1_fixture_has_no_custom_entries():
    # Regression guard on the inert behaviour: 48 runs produced none,
    # because the entry was appended before print mode subscribed.
    assert read_telemetry(_real_run()).custom_entries == ()


def test_reads_custom_entry_types_in_stdout_order():
    stream = "\n".join(
        json.dumps({"type": "entry_appended", "entry": {"type": "custom", "customType": name}})
        for name in ("first", "second")
    )

    assert read_telemetry(stream).custom_entries == ("first", "second")


def test_skips_an_appended_entry_that_is_not_a_custom_entry():
    # appendEntry is not the only thing that appends an entry. A label
    # change is not evidence.
    stream = json.dumps(
        {"type": "entry_appended", "entry": {"type": "label_change", "label": "x"}}
    )

    assert read_telemetry(stream).custom_entries == ()


def test_skips_a_custom_entry_whose_type_is_not_a_string():
    stream = json.dumps(
        {"type": "entry_appended", "entry": {"type": "custom", "customType": 7}}
    )

    assert read_telemetry(stream).custom_entries == ()


def test_a_missing_custom_entry_does_not_make_a_run_incomplete():
    # The extension observes. It must never fail a run the model
    # actually completed.
    assert read_telemetry(_real_run()).complete is True
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_telemetry.py -v`
Expected: the new tests FAIL with `AttributeError: 'RunTelemetry' object has no attribute 'custom_entries'`.

- [ ] **Step 3: Add the field**

In `harness/telemetry.py`, add to `RunTelemetry` as the last field, immediately after `complete`:

```python
    complete: bool  # the run finished normally; counts are lower bounds if False
    custom_entries: tuple[str, ...]  # customType of each entry_appended, in order
```

- [ ] **Step 4: Parse the events**

In `read_telemetry`, add an accumulator beside the others:

```python
    custom_entries: list[str] = []
```

Add a case to the `match` block, after the `tool_execution_end` case:

```python
            case "entry_appended":
                entry = event.get("entry")
                if not isinstance(entry, dict) or entry.get("type") != "custom":
                    continue
                custom_type = entry.get("customType")
                if isinstance(custom_type, str):
                    custom_entries.append(custom_type)
```

And pass it in the return:

```python
        complete=agent_ended and started.keys() <= ended.keys(),
        custom_entries=tuple(custom_entries),
```

- [ ] **Step 5: Update the module docstring**

Add this paragraph to `harness/telemetry.py`'s module docstring, after the paragraph beginning "**When `complete` is `False`**":

```
**Custom entries never affect a run's verdict.** `custom_entries` records
what the extension emitted; it has no bearing on `complete`, on
`RunResult.accepted`, or on grading. The extension observes. Letting it
fail a run the model actually completed would make the instrument a
participant in what it measures.
```

- [ ] **Step 6: Run the tests to verify they pass**

Run: `uv run pytest tests/test_telemetry.py -v`
Expected: all PASS.

- [ ] **Step 7: Check for positional constructions**

Run: `grep -rn "RunTelemetry(" harness/ tests/`
Expected: only the single `return RunTelemetry(` in `harness/telemetry.py`, which uses keywords. If any positional construction exists elsewhere, add `custom_entries=()` to it.

- [ ] **Step 8: Run the full gates**

Run: `uv run pytest && uv run ruff check . && uv run pyrefly check`
Expected: all pass.

- [ ] **Step 9: Commit**

```bash
git add harness/telemetry.py tests/test_telemetry.py
git commit -m "feat(phase3-cycle1): read custom entries from captured stdout

RunTelemetry.custom_entries records the customType of each
entry_appended event, in stdout order. Types only, not payloads --
proving the path needs the name to arrive.

Parsing is tolerant, never inventive: a non-custom entry or a
non-string customType is skipped rather than guessed at.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Task 3: The extension seam

**Files:**
- Modify: `harness/runner.py:15` and `:96-102`
- Modify: `tests/test_runner.py`

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces: `harness.runner.EXTENSIONS: tuple[Path, ...]` (replacing `EXTENSION: Path`), and `_pi_command(model: str, prompt: str, extensions: tuple[Path, ...] = EXTENSIONS) -> list[str]`. Task 4 reads `EXTENSIONS`.

- [ ] **Step 1: Write the failing tests**

`tests/test_runner.py` imports `harness.runner as runner` but **not** `Path`. Add to the standard-library import block at the top of the file:

```python
from pathlib import Path
```

Then append:

```python
def test_pi_command_emits_one_extension_flag_per_path_in_order():
    command = _pi_command(
        "model-name", "task text", extensions=(Path("/a/one.ts"), Path("/b/two.ts"))
    )

    flagged = [
        command[i + 1] for i, item in enumerate(command) if item == "--extension"
    ]
    assert flagged == ["/a/one.ts", "/b/two.ts"]


def test_pi_command_defaults_to_the_projects_extensions():
    command = _pi_command("model-name", "task text")

    assert command.count("--extension") == len(runner.EXTENSIONS)
    for extension in runner.EXTENSIONS:
        assert str(extension) in command
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_runner.py -k extension -v`
Expected: two FAILs — `TypeError: _pi_command() got an unexpected keyword argument 'extensions'` for the first, and `AttributeError: module 'harness.runner' has no attribute 'EXTENSIONS'` for the second.

- [ ] **Step 3: Replace the constant**

In `harness/runner.py`, replace line 15:

```python
EXTENSIONS: tuple[Path, ...] = (REPO_ROOT / ".pi" / "extensions" / "hello-world.ts",)
```

- [ ] **Step 4: Build the flags from the tuple**

Replace `_pi_command` entirely:

```python
def _pi_command(
    model: str, prompt: str, extensions: tuple[Path, ...] = EXTENSIONS
) -> list[str]:
    command = [
        "pi", "--print", "--mode", "json", "--no-session", "--model", model,
        "--no-extensions",
    ]
    for extension in extensions:
        command += ["--extension", str(extension)]
    command += [
        "--no-skills", "--no-prompt-templates", "--no-themes",
        "--no-context-files", "--approve", prompt,
    ]
    return command
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `uv run pytest tests/test_runner.py -v`
Expected: all PASS, including the pre-existing `test_pi_command_contains_trusted_session_and_isolation_flags`. That test asserts the isolation flags are present, not their order — if it fails, read it before changing it; the flags must not have been dropped.

- [ ] **Step 6: Confirm no stale references**

Run: `grep -rn "EXTENSION\b" harness/ tests/`
Expected: no hits for the singular `EXTENSION`. Update any that appear.

Do **not** widen this to `docs/`. Two documents quote the old constant and must keep quoting it: `docs/superpowers/plans/2026-07-31-phase1-cycle8-first-real-run.md` is a historical record of what cycle 8 did, and this cycle's own spec quotes `EXTENSION: Path` as the thing being replaced. Editing either would falsify the record. `docs/_build` is generated output and is never edited by hand.

- [ ] **Step 7: Run the full gates**

Run: `uv run pytest && uv run ruff check . && uv run pyrefly check`
Expected: all pass.

- [ ] **Step 8: Commit**

```bash
git add harness/runner.py tests/test_runner.py
git commit -m "feat(phase3-cycle1): parameterize extension loading

EXTENSION becomes EXTENSIONS, a tuple, and _pi_command emits one
--extension per entry. Cycle 2 loads Pi's shipped subagent extension
alongside ours; a single hardcoded constant is the shape BRIEF.md's
'seams, not hardcodes' lesson is about.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Task 4: Extension digests in run conditions

**Files:**
- Modify: `harness/runner.py:19-27` (`RunConditions`) and `:105-117` (`_conditions`)
- Modify: `harness/checkpoint.py:57-69`
- Modify: `tests/test_runner.py:203, 224, 251, 262, 279, 294`
- Modify: `tests/test_checkpoint.py:205-220`

**Interfaces:**
- Consumes: `harness.runner.EXTENSIONS` from Task 3.
- Produces: `RunConditions.extension_digests: tuple[str, ...]` — declared as the **last** field, after `grade_timeout`. And `harness.runner._extension_digest(path: Path) -> str`, which raises `ValueError` on a directory and `FileNotFoundError` on a missing path.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_runner.py`:

```python
def test_extension_digest_changes_with_file_content(tmp_path):
    extension = tmp_path / "ext.ts"
    extension.write_text("one")
    first = runner._extension_digest(extension)
    extension.write_text("two")

    assert runner._extension_digest(extension) != first


def test_extension_digest_raises_on_a_directory(tmp_path):
    # Pi's shipped subagent extension is a directory. Cycle 2 must
    # decide how a tree is hashed, not inherit a plausible wrong answer.
    with pytest.raises(ValueError, match="directory"):
        runner._extension_digest(tmp_path)


def test_extension_digest_raises_on_a_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        runner._extension_digest(tmp_path / "absent.ts")


def test_conditions_record_a_digest_per_extension(monkeypatch, tmp_path):
    # _conditions shells out to `git rev-parse` and `pi --version`.
    # Every other unit test in this file monkeypatches _conditions
    # away for that reason; this one needs the real thing, so it stubs
    # the subprocesses instead. The suite stays fixture-only -- no test
    # here may depend on the `pi` binary being installed.
    extension = tmp_path / "ext.ts"
    extension.write_text("contents")
    monkeypatch.setattr(runner, "EXTENSIONS", (extension,))
    monkeypatch.setattr(
        runner.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(stdout="stubbed\n"),
    )

    conditions = runner._conditions("model", ["pi"], 600)

    assert len(conditions.extension_digests) == 1
    assert len(conditions.extension_digests[0]) == 64


def test_run_batch_refuses_a_record_recorded_under_a_different_extension(
    tmp_path, monkeypatch
):
    from harness.checkpoint import append_checkpoint

    checkpoint = tmp_path / "checkpoint.jsonl"
    recorded = RunConditions(
        "model", ("pi",), "0.82.0", "sha", "rev", 600, 30, ("old-digest",)
    )
    append_checkpoint(
        checkpoint,
        RunResult("d", _grade_result(), "out", "", 0, conditions=recorded),
    )
    monkeypatch.setattr(
        runner,
        "_conditions",
        lambda *args: RunConditions(
            "model", ("pi",), "0.82.0", "sha", "rev", 600, 30, ("new-digest",)
        ),
    )

    with pytest.raises(ValueError, match="checkpoint conditions do not match"):
        runner.run_batch(checkpoint, target=1, model="model")
```

Append to `tests/test_checkpoint.py`:

```python
def test_a_checkpoint_predating_extension_digests_still_loads(tmp_path):
    # Four real evidence checkpoints predate this field. A record that
    # cannot be *read* cannot be recomputed -- and telemetry.py's
    # docstring makes recomputability the reason raw stdout is retained
    # at all. The sentinel keeps them readable while guaranteeing
    # run_batch refuses to resume them: no SHA-256 equals it.
    path = tmp_path / "checkpoint.jsonl"
    record = json.loads(json.dumps(asdict(replace(
        _sample_result(),
        conditions=RunConditions(
            model="model",
            pi_command=("pi",),
            pi_version="0.82.0",
            task_spec_sha256="abc",
            harness_revision="def",
            run_timeout=600,
            grade_timeout=30,
            extension_digests=("unused",),
        ),
    ))))
    del record["conditions"]["extension_digests"]
    path.write_text(json.dumps(record) + "\n")

    loaded = load_checkpoint(path)

    assert loaded[0].conditions.extension_digests == ("<pre-cycle1>",)
```

`_grade_result` is an existing helper in `tests/test_runner.py`; `_sample_result`, `replace`, and `load_checkpoint` are existing names in `tests/test_checkpoint.py`. Read each before use to confirm its signature, and add `import json` and `from dataclasses import asdict` to `tests/test_checkpoint.py` if absent.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_runner.py tests/test_checkpoint.py -k "digest or extension" -v`
Expected: several FAILs — `AttributeError: module 'harness.runner' has no attribute '_extension_digest'` for the digest helper tests, and `TypeError: RunConditions.__init__() takes 8 positional arguments but 9 were given` for the tests passing the new field.

- [ ] **Step 3: Add the field**

In `harness/runner.py`, add to `RunConditions` as the last field, after `grade_timeout`:

```python
    extension_digests: tuple[str, ...]
```

- [ ] **Step 4: Add the digest helper**

Add above `_conditions`:

```python
def _extension_digest(path: Path) -> str:
    """SHA-256 of one extension file.

    Raises on a directory rather than hashing something plausible: Pi's
    shipped subagent extension is a directory tree, and how a tree is
    hashed is a decision for the cycle that needs it.
    """
    if path.is_dir():
        raise ValueError(f"extension is a directory, not a file: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()
```

- [ ] **Step 5: Record the digests**

In `_conditions`, add to the `RunConditions(...)` construction:

```python
        extension_digests=tuple(_extension_digest(path) for path in EXTENSIONS),
```

- [ ] **Step 6: Document why the field exists**

Add this docstring to `RunConditions`, directly under the `class` line:

```python
    """The conditions a run happened under, compared for equality by
    `run_batch` before resuming a checkpoint.

    `pi_command` records extension *paths*. `extension_digests` records
    their *contents*, and exists because without it, editing an
    extension leaves these conditions byte-identical — so a batch would
    silently resume a checkpoint whose earlier runs used different code.

    Records written before this field load with the sentinel
    `("<pre-cycle1>",)`. They stay readable and recomputable; no
    SHA-256 can equal the sentinel, so `run_batch` refuses to resume
    them. Unreadable is a different, worse failure than unresumable.
    """
```

- [ ] **Step 7: Deserialize the field**

In `harness/checkpoint.py`, add to the `RunConditions(...)` construction inside `load_checkpoint`:

```python
                        extension_digests=tuple(
                            data["conditions"].get(
                                "extension_digests", ("<pre-cycle1>",)
                            )
                        ),
```

Use `.get(...)` with the sentinel, **not** `data[...]`. Requiring the key would make the four real evidence checkpoints at `~/local-ai-pi-evidence/` (cycle 14's n=16, cycle 2's n=32, cycle 3's clean parts 1 and 2) raise `KeyError` on *any* read, not only on resume — destroying the ability to recompute every number ever published from them. `harness/telemetry.py`'s docstring states the principle directly: raw stdout is retained precisely so past numbers stay reproducible.

The sentinel is a string no SHA-256 hexdigest can equal, so `run_batch`'s existing conditions comparison still refuses to resume such a checkpoint, with its existing message. Unresumable is the intended consequence; unreadable is not.

- [ ] **Step 8: Update the existing positional constructions**

Six in `tests/test_runner.py` (lines 203, 224, 251, 262, 279, 294) read:

```python
RunConditions("model", ("pi",), "0.82.0", "sha", "rev", 600, 30)
```

Append an eighth argument to each:

```python
RunConditions("model", ("pi",), "0.82.0", "sha", "rev", 600, 30, ("digest",))
```

One in `tests/test_checkpoint.py` (lines 205-220) uses keywords; add:

```python
        extension_digests=("abc123",),
```

- [ ] **Step 9: Run the tests to verify they pass**

Run: `uv run pytest -v`
Expected: all PASS, **two skipped** — both `SATYRN_LIVE`-gated live tests.

- [ ] **Step 10: Run the full gates**

Run: `uv run pytest && uv run ruff check . && uv run pyrefly check`
Expected: all pass.

- [ ] **Step 11: Commit**

```bash
git add harness/runner.py harness/checkpoint.py tests/test_runner.py tests/test_checkpoint.py
git commit -m "feat(phase3-cycle1): record extension contents in run conditions

pi_command records extension paths, never contents, so editing an
extension left RunConditions byte-identical and run_batch would resume
a mismatched checkpoint silently. extension_digests closes that.

The digest helper raises on a directory: Pi's subagent extension is a
tree, and cycle 2 should decide how a tree is hashed rather than
inherit a plausible wrong answer.

This invalidates every existing checkpoint. Phase 2 cycle 3's clean
baseline has not run yet, so the cost is zero now and would not be
later.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Task 5: The event vocabulary, and correcting the record

**Files:**
- Create: `docs/superpowers/research/2026-08-02-phase3-cycle1-event-vocabulary.md`
- Modify: `ROADMAP.md:165-210` (the Phase 3 section)
- Modify: `docs/superpowers/index.md` (Research toctree)

**Interfaces:**
- Consumes: the live evidence from Task 1 and the fixture it produced.
- Produces: documentation only. No code depends on this task.

- [ ] **Step 1: Write the research note**

Create `docs/superpowers/research/2026-08-02-phase3-cycle1-event-vocabulary.md`. It must contain, with the source citations already established in the design doc:

- **The contract, stated once:** everything the session emits *after* `session.subscribe` reaches stdout in `--mode json`. It is not a per-event allowlist — `modes/print-mode.js:80-84` serializes every event the subscriber receives.
- **The subscribe boundary:** `bindExtensions()` awaits the `session_start` emission (`core/agent-session.js:1766`), and print mode calls `session.subscribe` only after `bindExtensions` returns (`modes/print-mode.js:50, 80`). Anything an extension emits during `session_start` has no subscriber and is dropped. **This is the real cause of 48 inert runs, and it is not `--no-session`.**
- **`appendEntry` works, and where:** `pi.appendEntry(customType, data?)` appends an entry and emits `entry_appended` (`core/agent-session.js:1869-1874`); `appendCustomEntry` stores it in an in-memory map (`core/session-manager.js:820`), independent of disk persistence. Called from `agent_start` or later, it reaches stdout. Verified live in Task 1; fixture at `tests/fixtures/pi-run-0.82.0-entry-appended.jsonl`.
- **`ctx.ui.notify` is not an evidence channel:** it has no destination under `--no-themes`.
- **`pi.sendMessage` is barred:** it reaches stdout, but custom *messages* can enter LLM context — Pi's own `registerEntryRenderer` documentation contrasts custom entries, which "do not participate in LLM context". Injecting anything into the model's context to prove observability would corrupt the runs the harness measures.
- **What cycle 3 inherits:** a delegated child is spawned as `pi --mode json -p --no-session`, so a delegation is a tool call in the parent's stream. This note establishes that the parent's own extension activity is visible on the same stream.

- [ ] **Step 2: Correct the ROADMAP**

In `ROADMAP.md`, in the "A finding of our own, and the reason cycle 1 is not a file copy" paragraph, replace the stated cause. The paragraph currently attributes inertness to `--no-session` leaving `appendEntry` nowhere to write. Replace that clause with the subscribe-ordering cause, and add a sentence recording that the original claim was justified by reading rather than by a run, and was retired when a run disagreed.

In the cycle 1 table row, replace the sentence "Note this changes the extension, and `RunConditions` records its path — so it changes run conditions" with a statement of what was actually true: `RunConditions` recorded only the path, never the contents, so changing the extension did **not** change run conditions until this cycle added `extension_digests`.

Leave the cycle 1 row's **State** column as `Planned`. The cycle is not done until Task 6's chapter exists; flipping it here would make the roadmap claim something untrue for the length of one task, which is the exact failure mode this task is correcting.

- [ ] **Step 3: Add the note to the toctree**

In `docs/superpowers/index.md`, in the `:caption: Research` toctree, add after `research/2026-08-02-phase2-remaining-plan`:

```
research/2026-08-02-phase3-cycle1-event-vocabulary
```

- [ ] **Step 4: Verify the docs build**

Run: `rm -rf docs/_build && uv run sphinx-build -W -b html docs docs/_build/html`
Expected: `build succeeded.`

- [ ] **Step 5: Commit**

```bash
git add docs/superpowers/research/2026-08-02-phase3-cycle1-event-vocabulary.md docs/superpowers/index.md ROADMAP.md
git commit -m "docs(phase3-cycle1): the event vocabulary, and the corrected record

What an extension can and cannot emit under --print --mode json
--no-session --no-themes, so cycle 3 does not start from a guess about
where a delegation becomes visible.

Corrects two ROADMAP claims that a run disagreed with: the cause of the
inert extension was subscribe ordering, not --no-session; and changing
the extension did not change run conditions until this cycle.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Task 6: The teaching artifact

**Files:**
- Read: `.worktrees/pre-restructure/docs/section-1-hello-agent/` (spec 170 lines, plan 486, chapter 222)
- Create: `docs/superpowers/chapters/hello-agent.md`
- Modify: `docs/superpowers/index.md`

**Interfaces:**
- Consumes: the finished extension from Task 1, the event vocabulary from Task 5.
- Produces: documentation only.

- [ ] **Step 1: Read the prior chapter**

Run: `ls .worktrees/pre-restructure/docs/section-1-hello-agent/` then read the chapter file in full, and the spec alongside it.

- [ ] **Step 2: Audit it for drift**

Check every API call and flag the prior chapter names against installed 0.82.0 at `/Users/pauleveritt/.volta/tools/image/packages/@earendil-works/pi-coding-agent/lib/node_modules/@earendil-works/pi-coding-agent/dist/core/extensions/types.d.ts`.

At least one drift is known: the prior spec uses `appendEntry({type, data})`; the installed signature is `appendEntry<T>(customType: string, data?: T): void` (types.d.ts:915). Write down every other divergence you find — the audit's output is part of the deliverable, not scaffolding.

- [ ] **Step 3: Write the chapter**

Create `docs/superpowers/chapters/hello-agent.md`. It teaches the extension we actually have:

- What an extension is in Pi (a default-exported function receiving `ExtensionAPI`), and that this is an extension, not a fork
- The event lifecycle the seven handlers tour
- That `ctx.ui.notify` shows nothing under `--no-themes`, and why that is a property of the invocation mode rather than a defect
- The subscribe-ordering finding, in plain language: *where* you emit decides whether anyone hears it
- The one entry that travels, end to end, with the actual line from `tests/fixtures/pi-run-0.82.0-entry-appended.jsonl`

Honour `BRIEF.md`'s concept budget: a 5-h/wk contributor must be able to absorb it. Where the prior chapter is wrong against 0.82.0, rewrite rather than copy — this is gardening, not transplant.

- [ ] **Step 4: Record the audit**

Append a short "Drift found against 0.82.0" section to `docs/superpowers/research/2026-08-02-phase3-cycle1-event-vocabulary.md` listing each divergence from Step 2, so the next transplant from the pre-restructure worktree starts from a known state.

- [ ] **Step 5: Mark the cycle done in ROADMAP.md**

Now that every deliverable exists, change the Phase 3 cycle 1 row's **State** column from `Planned` to `Done`.

- [ ] **Step 6: Add to the toctree**

In `docs/superpowers/index.md`, add `chapters/hello-agent` to an appropriate toctree. If no `Chapters` caption exists, create one following the pattern of the existing `Specs`, `Plans`, and `Research` toctrees:

````text
```{toctree}
:hidden:
:maxdepth: 1
:caption: Chapters

chapters/hello-agent
```
````

- [ ] **Step 7: Verify the docs build**

Run: `rm -rf docs/_build && uv run sphinx-build -W -b html docs docs/_build/html`
Expected: `build succeeded.`

- [ ] **Step 8: Run the full gates**

Run: `uv run pytest && uv run ruff check . && uv run pyrefly check`
Expected: all pass, two skipped.

- [ ] **Step 9: Commit**

```bash
git add ROADMAP.md docs/superpowers/chapters/hello-agent.md docs/superpowers/index.md docs/superpowers/research/2026-08-02-phase3-cycle1-event-vocabulary.md
git commit -m "docs(phase3-cycle1): the hello-agent chapter, gardened not copied

Transplanted from the pre-restructure worktree with a drift audit
against installed 0.82.0. The prior spec's appendEntry({type, data})
was already stale against appendEntry(customType, data?); the audit's
full findings are recorded alongside the event vocabulary.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Done when

- One `entry_appended` carrying `customType: "evidence"` is visible in a real run's captured stdout, and `read_telemetry` reports it in `custom_entries`
- `EXTENSIONS` is a tuple with one caller, and `_pi_command` emits one flag per entry
- Editing an extension file changes `RunConditions`, and `run_batch` refuses a checkpoint recorded under different extension contents
- The event vocabulary is written, and both incorrect `ROADMAP.md` claims are corrected
- The chapter exists, audited against 0.82.0
- `uv run pytest && uv run ruff check . && uv run pyrefly check` pass, and strict Sphinx builds clean

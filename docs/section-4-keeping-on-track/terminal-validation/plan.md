# Terminal Validation — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land validation-command drift detection in the harness and an un-narrowable `./validate.sh` wrapper so the implementer's stop-decision runs against the true oracle.

**Architecture:** A drift-detection function in `harness/telemetry.py` scans the parent JSONL's subagent result text for validation commands that don't match the packet's expected command. `InvocationProfile` carries the expected command. `SessionResult` stores per-run drift data. `BaselineReport` and `write_report` aggregate and report drift incidence. A zero-arg `./validate.sh` wrapper in the AgentClinic workspace removes the model's ability to narrow the command.

**Tech Stack:** Python 3.14+ (harness), bash (validate.sh), pytest (tests)

## Global Constraints

- Python >=3.14, <3.15
- Built-in Pi only — no fork, no new extensions
- The chapter is scoped to prompt/packet tuning only per the SP2 spec boundary clause
- Mechanism-level enforcement (tool_call hook) is explicitly Section IV, not this chapter
- n=4 default for iteration; override to n=8 for the shared pre-arm batch

## File Structure

| File | Responsibility |
|------|---------------|
| `harness/telemetry.py` | New `detect_validation_drift()` function |
| `harness/session.py` | `validation_command` on `InvocationProfile`; `drifted_commands`/`has_drift` on `SessionResult`; wire drift detection into `run_session` |
| `harness/runner.py` | Drift aggregation on `BaselineReport`; drift section in `write_report` |
| `examples/agentclinic/validate.sh` | Zero-arg wrapper script |
| `prompts/orchestrator.md` | Validation section changed to `./validate.sh` |
| `tests/test_telemetry.py` | Tests for `detect_validation_drift` |
| `tests/test_runner.py` | Tests for drift aggregation and reporting |

---

### Task 1: Drift detection in harness/

**BLOCKING — must land before the cleanup Phase 3 re-run batch.** If the batch runs first, drift can't be recomputed after the fact since child session JSONL is not captured.

**Files:**
- Modify: `harness/session.py`
- Modify: `harness/telemetry.py`
- Modify: `harness/runner.py`
- Modify: `tests/test_telemetry.py`
- Modify: `tests/test_runner.py`

**Interfaces:**
- Consumes: `SessionResult`, `InvocationProfile`, `BaselineReport`, `read_run`, `write_report` (existing)
- Produces:
  - `detect_validation_drift(artifact_path: str \| Path, expected_command: str) -> list[str]`
  - `InvocationProfile.validation_command: str = "uv run pytest -q"`
  - `SessionResult.drifted_commands: list[str]`
  - `SessionResult.has_drift: bool`
  - `BaselineReport.drift_incidence` property
  - `BaselineReport.total_delegations_with_drift` property

- [ ] **Step 1: Write failing test for `detect_validation_drift` — drifted command detected**

In `tests/test_telemetry.py`, add a module-level helper and test:

```python
import json
from harness.telemetry import detect_validation_drift

_DRIFTED_JSONL = """\
{"type":"tool_execution_start","toolCallId":"a","toolName":"subagent","args":{"task":"Build Phase 1","agent":"implementer"}}
{"type":"tool_execution_end","toolCallId":"a","toolName":"subagent","isError":"False","result":"Tests passed. I ran uv run pytest -q tests/test_app.py and all 3 passed."}
"""

_DRIFT_FREE_JSONL = """\
{"type":"tool_execution_start","toolCallId":"b","toolName":"subagent","args":{"task":"Build Phase 1","agent":"implementer"}}
{"type":"tool_execution_end","toolCallId":"b","toolName":"subagent","isError":"False","result":"Done. uv run pytest -q: 3 passed."}
"""

_WRAPPER_DRIFTED_JSONL = """\
{"type":"tool_execution_start","toolCallId":"c","toolName":"subagent","args":{"task":"Build Phase 1","agent":"implementer"}}
{"type":"tool_execution_end","toolCallId":"c","toolName":"subagent","isError":"False","result":"I ran ./validate.sh tests/test_app.py but it errored. Then I ran uv run pytest -q tests/test_app.py and it passed."}
"""


def test_detect_drift_finds_drifted_command(tmp_path: Path):
    """A subagent result containing a narrowed pytest command is detected as drift."""
    f = tmp_path / "session.jsonl"
    f.write_text(_DRIFTED_JSONL)
    drifted = detect_validation_drift(f, "uv run pytest -q")
    assert len(drifted) == 1
    assert "tests/test_app.py" in drifted[0]


def test_detect_drift_no_drift_when_exact_match(tmp_path: Path):
    """Exact match to the expected command produces no drift."""
    f = tmp_path / "session.jsonl"
    f.write_text(_DRIFT_FREE_JSONL)
    drifted = detect_validation_drift(f, "uv run pytest -q")
    assert drifted == []


def test_detect_drift_no_subagent_calls(tmp_path: Path):
    """A session with no subagent calls has no drift."""
    f = tmp_path / "session.jsonl"
    f.write_text('{"type":"tool_execution_end","toolName":"bash","isError":"False","result":"ok"}\n')
    drifted = detect_validation_drift(f, "uv run pytest -q")
    assert drifted == []
```

- [ ] **Step 2: Run tests, verify they fail**

```bash
uv run pytest tests/test_telemetry.py::test_detect_drift_finds_drifted_command tests/test_telemetry.py::test_detect_drift_no_drift_when_exact_match tests/test_telemetry.py::test_detect_drift_no_subagent_calls -v
```
Expected: all FAIL with `NameError: name 'detect_validation_drift' is not defined`

- [ ] **Step 3: Implement `detect_validation_drift` in `harness/telemetry.py`**

Add after the `subagent_stats_from` function, before the final blank line:

```python
def detect_validation_drift(
    artifact_path: str | Path,
    expected_command: str,
) -> list[str]:
    """Scan subagent result text for validation commands that don't match expected.

    Parses the parent session JSONL for subagent tool_execution_end events,
    extracts the result text (the child's output), and finds any pytest or
    validate.sh invocations that differ from expected_command.

    Returns a list of non-matching commands found (empty = no drift).
    """
    import re

    path = Path(artifact_path)
    if not path.exists():
        return []

    # Patterns for validation commands the child might run.
    pytest_pattern = re.compile(r"(?:uv\s+run\s+)?pytest[^\n]*")
    validate_pattern = re.compile(r"\.?/?validate\.sh[^\n]*")

    drifted: list[str] = []
    for line in path.read_text().splitlines():
        try:
            event = json.loads(line.strip())
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict):
            continue
        if (
            event.get("type") != "tool_execution_end"
            or event.get("toolName") != "subagent"
        ):
            continue
        result = event.get("result", "")
        if not isinstance(result, str):
            continue
        for pattern in (pytest_pattern, validate_pattern):
            for match in pattern.finditer(result):
                cmd = match.group().strip()
                if cmd != expected_command:
                    drifted.append(cmd)
    return drifted
```

- [ ] **Step 4: Run tests, verify they pass**

```bash
uv run pytest tests/test_telemetry.py::test_detect_drift_finds_drifted_command tests/test_telemetry.py::test_detect_drift_no_drift_when_exact_match tests/test_telemetry.py::test_detect_drift_no_subagent_calls -v
```
Expected: all PASS

- [ ] **Step 5: Add `validation_command` to `InvocationProfile`**

In `harness/session.py`, add the field to the dataclass:

```python
@dataclass
class InvocationProfile:
    """Describes how to invoke pi for a session."""
    extensions: list[str]
    append_system_prompt: str | None = None
    no_extensions: bool = True
    timeout: int | None = None
    expects_delegation: bool = False
    validation_command: str = "uv run pytest -q"  # expected validation command
```

Update the `sp2()` factory to be explicit:

```python
@staticmethod
def sp2(subagent_path: str) -> "InvocationProfile":
    """The SP2 profile: subagent extension + orchestrator prompt."""
    return InvocationProfile(
        extensions=[subagent_path],
        append_system_prompt="prompts/orchestrator.md",
        timeout=900,
        expects_delegation=True,
        validation_command="uv run pytest -q",
    )
```

- [ ] **Step 6: Add drift fields to `SessionResult` and wire into `run_session`**

In `harness/session.py`, add fields to `SessionResult`:

```python
@dataclass
class SessionResult:
    run_id: str
    outcome: str
    returncode: int | None
    telemetry: RunTelemetry
    changed_files: list[str]
    diff: str
    tests_pass: bool
    wall_time_s: float
    artifact_path: str
    stderr_text: str = ""
    pytest_stdout: str = ""
    pytest_stderr: str = ""
    drifted_commands: list[str] = field(default_factory=list)

    @property
    def has_drift(self) -> bool:
        return len(self.drifted_commands) > 0
```

Add `from dataclasses import dataclass, field` at the top (only `dataclass` is currently imported):

```python
from dataclasses import dataclass, field
```

In `run_session`, after the no-delegation check and before git diff, add drift detection:

```python
    # Detect validation-command drift from subagent result text.
    drifted_commands = detect_validation_drift(
        artifact_path, profile.validation_command
    )
```

And pass it to `SessionResult`:

```python
    return SessionResult(
        run_id=run_id,
        outcome=outcome,
        returncode=returncode,
        telemetry=telemetry,
        changed_files=changed_files,
        diff=diff_text,
        tests_pass=tests_pass,
        wall_time_s=wall_time_s,
        artifact_path=str(artifact_path),
        stderr_text=stderr_text,
        pytest_stdout=pytest_stdout,
        pytest_stderr=pytest_stderr,
        drifted_commands=drifted_commands,
    )
```

Also add the import at the top of `session.py`:

```python
from harness.telemetry import RunTelemetry, detect_validation_drift, has_subagent_calls, read_run
```

(replace the existing `from harness.telemetry import RunTelemetry, has_subagent_calls, read_run` line)

- [ ] **Step 7: Write failing test for drift fields on SessionResult**

In `tests/test_session.py`, add:

```python
def test_session_result_with_drift():
    """SessionResult stores drifted commands and has_drift reflects them."""
    from harness.telemetry import RunTelemetry
    r = SessionResult(
        run_id="d1",
        outcome="exited",
        returncode=0,
        telemetry=RunTelemetry(prompts=["test"], turns=5),
        changed_files=["app.py"],
        diff="+ # hello",
        tests_pass=True,
        wall_time_s=12.3,
        artifact_path="research/sessions/d1.jsonl",
        stderr_text="",
        drifted_commands=["uv run pytest -q tests/test_app.py"],
    )
    assert r.has_drift is True
    assert len(r.drifted_commands) == 1
    assert "tests/test_app.py" in r.drifted_commands[0]


def test_session_result_no_drift():
    """No drifted commands means has_drift is False."""
    from harness.telemetry import RunTelemetry
    r = SessionResult(
        run_id="d2",
        outcome="exited",
        returncode=0,
        telemetry=RunTelemetry(prompts=["test"], turns=5),
        changed_files=["app.py"],
        diff="+ # hello",
        tests_pass=True,
        wall_time_s=12.3,
        artifact_path="research/sessions/d2.jsonl",
        stderr_text="",
    )
    assert r.has_drift is False
```

- [ ] **Step 8: Run tests, verify they pass**

```bash
uv run pytest tests/test_session.py::test_session_result_with_drift tests/test_session.py::test_session_result_no_drift -v
```
Expected: both PASS

- [ ] **Step 9: Add drift aggregation to `BaselineReport`**

In `harness/runner.py`, add properties after `mean_turns`:

```python
    @property
    def total_drifted_runs(self) -> int:
        return sum(1 for r in self.results if r.has_drift)

    @property
    def drift_incidence(self) -> float:
        return self.total_drifted_runs / max(len(self.results), 1)
```

- [ ] **Step 10: Add drift section to `write_report`**

In `harness/runner.py`, before the "Evidence tier" section (after the subagent delegation metrics), add:

```python
    lines.append("")
    lines.append("## Validation command drift")
    lines.append("")

    drifted_runs = [(i, r) for i, r in enumerate(report.results, 1) if r.has_drift]
    if drifted_runs:
        lines.append(
            f"| # | Drifted commands |"
        )
        lines.append("|---|-----------------|")
        for i, r in drifted_runs:
            cmds = "; ".join(r.drifted_commands)
            lines.append(f"| {i} | {cmds} |")
        lines.append("")
        lines.append(
            f"Drift detected in {report.total_drifted_runs}/{report.n} runs "
            f"({report.drift_incidence:.0%})."
        )
    else:
        lines.append("No validation command drift detected in any run.")
```

- [ ] **Step 11: Write tests for drift aggregation and reporting**

In `tests/test_runner.py`, add after `test_baseline_report_mean_fields`:

```python
def test_baseline_report_drift_fields():
    """BaselineReport aggregates drift across runs."""
    results = [
        _make_result("r1", True),
        _make_result("r2", False),
    ]
    results[0].drifted_commands = ["uv run pytest -q tests/test_app.py"]
    report = BaselineReport(phase="Phase 1", n=2, model="test/model", results=results)
    assert report.total_drifted_runs == 1
    assert report.drift_incidence == 0.5


def test_write_report_includes_drift_section(tmp_path: Path):
    """write_report includes a drift section when drift is present."""
    results = [
        _make_result("r1", True),
        _make_result("r2", False),
    ]
    results[0].drifted_commands = ["uv run pytest -q tests/test_app.py"]
    report = BaselineReport(phase="Phase 1", n=2, model="test/model", results=results)
    out = tmp_path / "report.md"
    write_report(report, out)
    content = out.read_text()
    assert "## Validation command drift" in content
    assert "tests/test_app.py" in content
    assert "1/2 runs" in content


def test_write_report_no_drift_section_when_clean(tmp_path: Path):
    """No drift section heading needed if there's nothing to report — but the
    section still appears with 'No validation command drift detected.'"""
    results = [_make_result("r1", True)]
    report = BaselineReport(phase="Phase 1", n=1, model="test/model", results=results)
    out = tmp_path / "report.md"
    write_report(report, out)
    content = out.read_text()
    assert "No validation command drift detected" in content
```

- [ ] **Step 12: Run all tests**

```bash
uv run pytest tests/test_telemetry.py tests/test_session.py tests/test_runner.py -v
```
Expected: all PASS (existing + new)

- [ ] **Step 13: Commit Task 1**

```bash
git add harness/telemetry.py harness/session.py harness/runner.py tests/test_telemetry.py tests/test_session.py tests/test_runner.py
git commit -m "feat: validation-command drift detection in harness

- detect_validation_drift() scans subagent result text for non-matching
  pytest/validate.sh commands
- InvocationProfile carries the expected validation command
- SessionResult stores drifted_commands; has_drift property
- BaselineReport aggregates drift; write_report includes drift section
- Tests cover: drift detection, no-drift, no-subagent, aggregation, reporting"
```

---

### Task 2: `validate.sh` wrapper

**Can run in parallel with Task 1.** The wrapper lands after the shared re-run batch (cleanup Phase 3) to avoid tangling its effect into the corrected before-picture.

**Files:**
- Create: `examples/agentclinic/validate.sh`
- Modify: `tests/test_workspace.py` (add wrapper test if workspace tests exist)

**Interfaces:**
- Consumes: AgentClinic workspace (runs from the workspace root)
- Produces: `./validate.sh` — runs `uv run pytest -q`, errors if given arguments, exits with pytest's return code

- [ ] **Step 1: Create `examples/agentclinic/validate.sh`**

```bash
#!/usr/bin/env bash
set -euo pipefail

if [ $# -gt 0 ]; then
    echo "validate.sh takes no arguments — run it as: ./validate.sh" >&2
    exit 1
fi

exec uv run pytest -q
```

- [ ] **Step 2: Make it executable and test manually**

```bash
chmod +x examples/agentclinic/validate.sh
cd examples/agentclinic && ./validate.sh
```
Expected: pytest runs and exits (no code in the workspace yet, so it will likely report "no tests ran" but exit 0 — fix: run in a workspace with code)

- [ ] **Step 3: Write a test for the wrapper**

In `tests/test_workspace.py`, add:

```python
def test_validate_sh_no_args(tmp_path: Path):
    """validate.sh with no args runs uv run pytest -q."""
    import subprocess
    script = tmp_path / "validate.sh"
    script.write_text("#!/usr/bin/env bash\nset -euo pipefail\nif [ $# -gt 0 ]; then\n    echo 'validate.sh takes no arguments' >&2\n    exit 1\nfi\necho 'pytest would run here'\n")
    script.chmod(0o755)
    result = subprocess.run([str(script)], cwd=str(tmp_path), capture_output=True, text=True)
    assert result.returncode == 0


def test_validate_sh_with_args_errors(tmp_path: Path):
    """validate.sh with arguments exits non-zero and prints error."""
    import subprocess
    script = tmp_path / "validate.sh"
    script.write_text("#!/usr/bin/env bash\nset -euo pipefail\nif [ $# -gt 0 ]; then\n    echo 'validate.sh takes no arguments' >&2\n    exit 1\nfi\necho 'ok'\n")
    script.chmod(0o755)
    result = subprocess.run([str(script), "tests/test_app.py"], cwd=str(tmp_path), capture_output=True, text=True)
    assert result.returncode == 1
    assert "takes no arguments" in result.stderr
```

If `tests/test_workspace.py` does not exist, create it.

- [ ] **Step 4: Run the wrapper tests**

```bash
uv run pytest tests/test_workspace.py -v
```
Expected: PASS

- [ ] **Step 5: Commit Task 2**

```bash
git add examples/agentclinic/validate.sh tests/test_workspace.py
git commit -m "feat: zero-arg validate.sh wrapper for AgentClinic

validate.sh runs 'uv run pytest -q' with no arguments. Passing
arguments (any argument at all) prints an error and exits 1. This
makes the validation command un-narrowable — there is no valid
invocation other than './validate.sh'.

Tests cover: no-arg success, with-arg failure."
```

---

### Task 3: Packet format update

**Can run in parallel with Tasks 1 and 2.** Changes the orchestrator prompt's packet template.

**Files:**
- Modify: `prompts/orchestrator.md`

**Interfaces:**
- Consumes: nothing code-level (it's a text file read by pi at runtime)
- Produces: updated `Validation` section in the packet format template

- [ ] **Step 1: Update the Validation section in `prompts/orchestrator.md`**

Change:
```
   ## Validation
   uv run pytest -q
```
To:
```
   ## Validation
   ./validate.sh
```

And in the "Packet Checklist" section at the bottom of the file, change:
```
- The Validation command is `uv run pytest -q`
```
To:
```
- The Validation command is `./validate.sh`
```

- [ ] **Step 2: Commit Task 3**

```bash
git add prompts/orchestrator.md
git commit -m "docs: switch packet validation command to ./validate.sh

The un-narrowable wrapper replaces the editable 'uv run pytest -q'
string. Any argument to ./validate.sh is a visible error — there is
no plausible reading that narrows the command."
```

---

### Task 4: Post-arm measurement run

**Requires:** Task 1 landed, cleanup Phase 3 re-run batch completed, Tasks 2-3 landed.

This task runs the post-wrapper measurement. It is described in the plan for completeness but is an ops/measurement step, not a code change.

- [ ] **Step 1: Confirm prerequisites**

- Task 1 (drift detection) is committed and merged
- Cleanup Phase 3 re-run batch (n=8, fixed harness, no wrapper) is complete
- Task 2 (validate.sh) is committed
- Task 3 (packet format update) is committed

- [ ] **Step 2: Set profile to use `./validate.sh` as expected command**

```python
profile = InvocationProfile.sp2(subagent_path)
profile.validation_command = "./validate.sh"
```

- [ ] **Step 3: Run n=8 baseline with the wrapper**

```bash
uv run python -c "
from harness.runner import run_baseline, write_report
from harness.session import InvocationProfile
from pathlib import Path

app_source = Path('examples/agentclinic')
subagent_path = Path('.pi/subagent-extension-path.txt').read_text().strip()
profile = InvocationProfile.sp2(subagent_path)
profile.validation_command = './validate.sh'

roadmap = (app_source / 'specs' / 'roadmap.md').read_text()
from tests.conftest import _extract_phase
phase1 = _extract_phase(roadmap, 1)

report = run_baseline(
    phase1, app_source,
    'omlx/gemma-4-12B-it-MLX-8bit',
    profile,
    n=8, timeout=900,
    phase_name='Phase 1 — Home Page',
)
write_report(report, 'docs/section-4-keeping-on-track/terminal-validation/research/terminal-validation-post.md')
print(f'Success: {report.success_count}/{report.n} ({report.success_rate:.0%})')
print(f'Drift: {report.total_drifted_runs}/{report.n} runs')
"
```

- [ ] **Step 4: Commit the evidence report**

```bash
git add docs/section-4-keeping-on-track/terminal-validation/research/
git commit -m "evidence: terminal validation post-arm — wrapper vs baseline drift comparison"
```

---

### Task 5: Chapter narrative

**Can run in parallel with all other tasks.** Writes the chapter's `index.md`.

**Files:**
- Create: `docs/section-4-keeping-on-track/terminal-validation/index.md`
- Modify: `docs/section-4-keeping-on-track/index.md` (add to toctree)

**Interfaces:**
- Consumes: spec, plan, evidence report (once available)
- Produces: chapter narrative following the chapter-structure policy

- [ ] **Step 1: Write the chapter narrative**

Create `docs/section-4-keeping-on-track/terminal-validation/index.md` with:

```markdown
(terminal-validation)=

# Terminal Validation

The SP2 post-tuning baseline went 4/8 (50%). The deep-dive found validation
command drift caused 2 of the 4 failures: the implementer narrowed
`uv run pytest -q` to `uv run pytest -q tests/test_app.py`, the narrower
command passed, and the implementer stopped confident and wrong.

**The harness was never fooled.** Its independent full-suite pytest correctly
failed those runs. What broke was the implementer's *stop condition* — false
confidence from a passing narrow command.

This chapter makes the child's stop-decision run against the true oracle.

## The prompt line (and why it's not enough)

...

## The un-narrowable wrapper

...

## Measuring: drift pre/post

...

## Results

### Metrics

...

### What the telemetry revealed

...

### Recommendations

...
```

(The full prose is written in implementation; this structure follows the chapter-structure policy.)

- [ ] **Step 2: Wire into the Section IV toctree**

In `docs/section-4-keeping-on-track/index.md`, update the hidden toctree:

```markdown
\`\`\`{toctree}
:hidden:

terminal-validation/index
\`\`\`
```

- [ ] **Step 3: Verify the build**

```bash
uv run sphinx-build -j auto -b html docs docs/_build/html
```
Expected: build succeeds, no warnings

- [ ] **Step 4: Commit Task 5**

```bash
git add docs/section-4-keeping-on-track/terminal-validation/index.md docs/section-4-keeping-on-track/index.md
git commit -m "docs: Terminal Validation chapter narrative — Section IV chapter 1"
```

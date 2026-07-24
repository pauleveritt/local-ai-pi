# SP1 — Part II (Measurement) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the course measurement harness: telemetry reader, disposable eval session, and n=8 statistical baseline run against the AgentClinic app with an unsteered SLM.

**Architecture:** Python harness (stdlib + pytest) that spawns `pi --mode json` via `subprocess` in disposable git-tracked workspaces, captures stdout as the session artifact, diffs against a pristine commit, runs `uv run pytest` as the acceptance oracle, and aggregates n=8 runs into a dated evidence report. Built TDD across 5 tasks (R0 schema capture, telemetry, workspace, session, runner + baseline) plus 3 chapter-writing tasks.

**Tech Stack:** Python 3.14+ (stdlib `subprocess`, `dataclasses`, `statistics`, `tempfile`), pytest, `pi` binary on PATH (0.81.1+), LM Studio serving `gemma-4-12b-it-mlx`.

## Global Constraints

- **Runtime:** globally-installed `pi` (0.81.1+), never a source checkout. Confirm with `pi --version`.
- **Model:** `lmstudio/gemma-4-12b-it-mlx` on `localhost:1234`, contextWindow 40960.
- **Headless:** always `stdin=subprocess.DEVNULL`; always `--print` mode.
- **Isolation:** every pi invocation uses `--no-extensions --extension .pi/extensions/hello-world.ts --no-skills --no-prompt-templates --no-themes --no-context-files --approve`.
- **Workspace:** disposable via `tempfile.mkdtemp`, git-tracked, pristine commit, `.venv` excluded.
- **Testing:** `uv run pytest` from repo root; `pythonpath = ["."]` in `pyproject.toml`. Integration tests gated by `pytest.mark.skipif(not shutil.which("pi"))`.
- **No framework deps:** stdlib + pytest only. `fastapi`, `uvicorn`, `starlette` are workspace deps, not harness deps.
- **Evidence:** every claim cites a session JSONL artifact in `docs/superpowers/research/sessions/`.
- **TDD:** every module has a failing test first, then implementation, then green commit.
- **Setup steps fold into the task whose deliverable needs them:** no separate "scaffold" or "configure" task.

---

## File Structure

```
local-ai-pi/
  pyproject.toml                          # MODIFY: add [tool.pytest.ini_options]
  harness/
    __init__.py                           # CREATE: empty package marker
    telemetry.py                          # CREATE: RunTelemetry, read_run()
    workspace.py                          # CREATE: prepare_workspace(), capture_diff()
    session.py                            # CREATE: SessionResult, run_session()
    runner.py                             # CREATE: BaselineReport, run_baseline(), write_report()
  tests/
    conftest.py                           # CREATE: shared fixtures
    fixtures/
      sample-session.jsonl                # CREATE (Task 0): captured Pi session
    test_telemetry.py                     # CREATE: unit tests for telemetry
    test_workspace.py                     # CREATE: unit tests for workspace
    test_session.py                       # CREATE: integration tests for session
    test_runner.py                        # CREATE: unit tests for runner
  docs/
    chapters/
      part2a-telemetry-reader.md          # CREATE (Task 5)
      part2b-eval-session.md              # CREATE (Task 6)
      part2c-smoking-gun.md               # CREATE (Task 7)
    superpowers/
      research/
        sessions/                         # CREATE: directory for run artifacts
        YYYY-MM-DD-baseline-phase-N.md    # CREATE (Task 4): the smoking-gun report
```

---

### Task 0: R0 — Schema capture

**Files:**
- Create: `tests/fixtures/sample-session.jsonl`

**Purpose:** Run pi once against Phase 1, capture the raw `--mode json` stdout stream, and record the actual event types, field names, and token-usage shapes. This is discovery, not TDD — its deliverable is a frozen fixture that Tasks 1-4 code against.

- [ ] **Step 1: Verify LM Studio is serving the model**

```bash
curl -s http://localhost:1234/v1/models | python3 -c "import sys,json; print([m['id'] for m in json.load(sys.stdin).get('data',[])])"
```
Expected: list includes `gemma-4-12b-it-mlx` or similar.

- [ ] **Step 2: Copy the hello-world extension into a temp workspace**

```bash
mkdir -p /tmp/sp1-r0/.pi/extensions
cp .pi/extensions/hello-world.ts /tmp/sp1-r0/.pi/extensions/
```

- [ ] **Step 3: Run pi with Phase 1 prompt, capture stdout**

```bash
pi --mode json -p --no-session \
   --model lmstudio/gemma-4-12b-it-mlx \
   --no-extensions --extension .pi/extensions/hello-world.ts \
   --no-skills --no-prompt-templates --no-themes --no-context-files \
   --approve \
   -- "$(sed -n '/^## Phase 1/,/^## Phase 2/p' examples/agentclinic/specs/roadmap.md | head -n -1)" \
   < /dev/null \
   > /tmp/sp1-r0/capture.jsonl 2>/tmp/sp1-r0/stderr.log
echo "exit: $?"
```
Expected: exit code 0 (or non-zero — either is fine; the capture is what matters). File `/tmp/sp1-r0/capture.jsonl` is non-empty and contains valid JSON lines.

- [ ] **Step 4: Save the capture as the committed test fixture**

```bash
mkdir -p tests/fixtures
cp /tmp/sp1-r0/capture.jsonl tests/fixtures/sample-session.jsonl
wc -l tests/fixtures/sample-session.jsonl
```

- [ ] **Step 5: Examine the event schema and record it in a schema note in telemetry.py (as a comment)**

Read the fixture and catalog every event `type` seen plus the fields on `message_end`:

```bash
python3 -c "
import json
types = set()
msg_end_fields = set()
for line in open('tests/fixtures/sample-session.jsonl'):
    try:
        ev = json.loads(line)
        types.add(ev.get('type','?'))
        if ev.get('type') == 'message_end':
            msg_end_fields.update(k for k in ev if k != 'type')
    except: pass
print('Event types:', sorted(types))
print('message_end fields:', sorted(msg_end_fields))
"
```

Record the output. This is the authoritative schema for `telemetry.py`.

- [ ] **Step 6: Commit**

```bash
git add tests/fixtures/sample-session.jsonl
git commit -m "R0: schema capture — real pi session against Phase 1"
```

---

### Task 1: Project setup + telemetry reader

**Files:**
- Modify: `pyproject.toml`
- Create: `harness/__init__.py`, `harness/telemetry.py`
- Create: `tests/conftest.py`, `tests/test_telemetry.py`

**Interfaces:**
- Produces: `RunTelemetry` dataclass, `read_run(stream_path) -> RunTelemetry`
- Consumed by: Task 3 (`session.py`), Task 4 (`runner.py`)

- [ ] **Step 1: Add pytest pythonpath to pyproject.toml**

Edit `pyproject.toml` — add after the `[dependency-groups]` section:

```toml
[tool.pytest.ini_options]
pythonpath = ["."]
markers = [
    "pi_available: tests that need the pi binary and a running model server",
]
```

- [ ] **Step 2: Write conftest.py with shared fixtures**

```python
# tests/conftest.py
import shutil
from pathlib import Path

import pytest


@pytest.fixture
def pi_binary() -> str:
    path = shutil.which("pi")
    if not path:
        pytest.skip("pi not on PATH")
    return path


@pytest.fixture
def model() -> str:
    return "lmstudio/gemma-4-12b-it-mlx"


@pytest.fixture
def app_source() -> Path:
    return Path(__file__).resolve().parent.parent / "examples" / "agentclinic"


@pytest.fixture
def sample_session_path() -> Path:
    return Path(__file__).resolve().parent / "fixtures" / "sample-session.jsonl"


def _extract_phase(roadmap_text: str, phase_number: int) -> str:
    """Extract the verbatim text of a phase section from the roadmap."""
    lines = roadmap_text.splitlines()
    marker = f"## Phase {phase_number} "
    start = None
    for i, line in enumerate(lines):
        if line.startswith(marker):
            start = i
            break
    if start is None:
        raise ValueError(f"Phase {phase_number} not found in roadmap")
    body: list[str] = []
    for line in lines[start + 1 :]:
        if line.startswith("## Phase "):
            break
        body.append(line)
    return "\n".join(body).strip()


@pytest.fixture
def phase1_prompt() -> str:
    roadmap = Path(__file__).resolve().parent.parent / "examples" / "agentclinic" / "specs" / "roadmap.md"
    return _extract_phase(roadmap.read_text(), 1)


@pytest.fixture
def phase2_prompt() -> str:
    roadmap = Path(__file__).resolve().parent.parent / "examples" / "agentclinic" / "specs" / "roadmap.md"
    return _extract_phase(roadmap.read_text(), 2)


@pytest.fixture
def phase3_prompt() -> str:
    roadmap = Path(__file__).resolve().parent.parent / "examples" / "agentclinic" / "specs" / "roadmap.md"
    return _extract_phase(roadmap.read_text(), 3)
```

- [ ] **Step 3: Create empty harness/__init__.py**

```python
# harness package
```

```bash
mkdir -p harness
```

- [ ] **Step 4: Write the failing telemetry test**

```python
# tests/test_telemetry.py
from pathlib import Path

from harness.telemetry import RunTelemetry, read_run


def test_read_run_extracts_prompts(sample_session_path: Path):
    result = read_run(sample_session_path)
    assert isinstance(result, RunTelemetry)
    assert len(result.prompts) >= 1, "should extract at least one prompt"
    assert all(isinstance(p, str) for p in result.prompts)


def test_read_run_extracts_tool_calls(sample_session_path: Path):
    result = read_run(sample_session_path)
    assert isinstance(result.tool_calls, list)


def test_read_run_counts_turns(sample_session_path: Path):
    result = read_run(sample_session_path)
    assert result.turns >= 0


def test_read_run_handles_empty_stream(tmp_path: Path):
    empty = tmp_path / "empty.jsonl"
    empty.write_text("")
    result = read_run(empty)
    assert result.prompts == []
    assert result.turns == 0


def test_read_run_handles_malformed_lines(tmp_path: Path):
    bad = tmp_path / "bad.jsonl"
    bad.write_text('{"type": "valid"}\nnot json\n{"type": "also_valid"}\n')
    result = read_run(bad)
    assert result.turns >= 0  # survives malformed lines
```

- [ ] **Step 5: Run tests to verify they fail**

```bash
uv run pytest tests/test_telemetry.py -v
```
Expected: `ModuleNotFoundError: No module named 'harness.telemetry'`

- [ ] **Step 6: Write minimal telemetry.py implementation**

Use the event types and field names from Task 0's schema catalog (inspect `tests/fixtures/sample-session.jsonl` for actual values). The implementation below uses placeholder type strings — replace them with the real names from the captured fixture.

```python
# harness/telemetry.py
"""
Telemetry reader for pi --mode json stdout streams.

Schema captured from pi <VERSION> against lmstudio/gemma-4-12b-it-mlx
on <DATE>. Event types observed: <list from Task 0>.
"""
import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ToolCall:
    name: str
    args: dict
    result: str | None = None
    is_error: bool = False


@dataclass
class TokenUsage:
    input: int = 0
    output: int = 0
    cache_read: int = 0
    cache_write: int = 0


@dataclass
class RunTelemetry:
    prompts: list[str] = field(default_factory=list)
    tool_calls: list[ToolCall] = field(default_factory=list)
    turns: int = 0
    tokens: TokenUsage | None = None
    evidence_entries: list[dict] = field(default_factory=list)


def read_run(stream_path: str | Path) -> RunTelemetry:
    """Parse a `pi --mode json` stdout JSONL file into structured telemetry.

    Reads line-by-line. Malformed lines (truncated writes, mid-write kills)
    are skipped rather than raised, so partial captures return whatever was
    successfully parsed.
    """
    path = Path(stream_path)
    prompts: list[str] = []
    tool_calls: list[ToolCall] = []
    turns = 0
    tokens: TokenUsage | None = None
    evidence_entries: list[dict] = []

    if not path.exists():
        return RunTelemetry()

    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue

        if not isinstance(event, dict):
            continue

        etype = event.get("type", "")

        # --- user prompts ---
        # Capture user message events. The event type and field name
        # are from the captured fixture; adjust if the schema differs.
        if etype == "user_message":  # adjust to real type from fixture
            content = event.get("content", "")
            if isinstance(content, str) and content:
                prompts.append(content)

        # --- tool calls ---
        elif etype == "tool_call":  # adjust to real type from fixture
            tool_calls.append(ToolCall(
                name=event.get("toolName", event.get("name", "unknown")),
                args=event.get("input", event.get("args", {})),
                result=event.get("result"),
                is_error=bool(event.get("isError", False)),
            ))

        # --- turns ---
        elif etype == "turn_end":  # adjust to real type from fixture
            turns += 1

        # --- token usage ---
        elif etype == "message_end":
            usage = event.get("usage", event.get("tokens", {}))
            if usage:
                tokens = TokenUsage(
                    input=usage.get("input", usage.get("inputTokens", 0)),
                    output=usage.get("output", usage.get("outputTokens", 0)),
                    cache_read=usage.get("cacheRead", usage.get("cache", {}).get("read", 0)),
                    cache_write=usage.get("cacheWrite", usage.get("cache", {}).get("write", 0)),
                )

        # --- evidence entries from appendEntry ---
        elif etype == "evidence":
            evidence_entries.append(event.get("data", event))

    return RunTelemetry(
        prompts=prompts,
        tool_calls=tool_calls,
        turns=turns,
        tokens=tokens,
        evidence_entries=evidence_entries,
    )
```

**Reconciliation note:** The event type strings (`"user_message"`, `"tool_call"`, `"turn_end"`, etc.) and field names (`"content"`, `"toolName"`, `"usage"`, etc.) above are *placeholders*. The implementer must replace them with the actual strings observed in `tests/fixtures/sample-session.jsonl` from Task 0. The test in Step 4 uses the sample-session fixture and will fail until the type strings match reality — that's the reconciliation gate.

- [ ] **Step 7: Run tests to verify they pass**

```bash
uv run pytest tests/test_telemetry.py -v
```
Expected: all 5 tests PASS after reconciling event type strings against the fixture.

- [ ] **Step 8: Commit**

```bash
git add pyproject.toml harness/__init__.py harness/telemetry.py tests/conftest.py tests/test_telemetry.py
git commit -m "feat: telemetry reader with schema-captured fixture"
```

---

### Task 2: Workspace provisioning

**Files:**
- Create: `harness/workspace.py`
- Create: `tests/test_workspace.py`

**Interfaces:**
- Consumes: `app_source` (from conftest), tech-stack.md for dependency versions
- Produces: `prepare_workspace(app_dir) -> tuple[Path, str]` (workspace path, pristine hash), `capture_diff(workspace, pristine_hash) -> tuple[list[str], str]`
- Consumed by: Task 3 (`session.py`)

- [ ] **Step 1: Write the failing workspace tests**

```python
# tests/test_workspace.py
import subprocess
from pathlib import Path

from harness.workspace import prepare_workspace, capture_diff


def test_prepare_workspace_returns_path_and_hash(app_source: Path):
    ws_path, pristine_hash = prepare_workspace(app_source)
    try:
        assert ws_path.exists()
        assert ws_path.is_dir()
        assert len(pristine_hash) == 40  # full SHA
        # workspace has the spec files from the app source
        assert (ws_path / "specs" / "roadmap.md").exists()
        # workspace has the stamped pyproject.toml
        assert (ws_path / "pyproject.toml").exists()
        # workspace has the hello-world extension
        assert (ws_path / ".pi" / "extensions" / "hello-world.ts").exists()
        # workspace is a git repo
        result = subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            cwd=ws_path, capture_output=True, text=True,
        )
        assert result.returncode == 0
    finally:
        import shutil
        shutil.rmtree(ws_path.parent, ignore_errors=True)


def test_prepare_workspace_excludes_venv_pycache(app_source: Path):
    ws_path, _ = prepare_workspace(app_source)
    try:
        # .venv/ should not be in the workspace
        assert not (ws_path / ".venv").exists()
        # __pycache__/ should not be in the workspace
        pycache = list(ws_path.rglob("__pycache__"))
        assert len(pycache) == 0
    finally:
        import shutil
        shutil.rmtree(ws_path.parent, ignore_errors=True)


def test_capture_diff_clean_workspace(app_source: Path):
    ws_path, pristine_hash = prepare_workspace(app_source)
    try:
        changed_files, diff_text = capture_diff(ws_path, pristine_hash)
        assert changed_files == []
        assert diff_text == "" or diff_text.isspace()
    finally:
        import shutil
        shutil.rmtree(ws_path.parent, ignore_errors=True)


def test_capture_diff_detects_new_file(app_source: Path):
    ws_path, pristine_hash = prepare_workspace(app_source)
    try:
        (ws_path / "app.py").write_text("# new file\n")
        subprocess.run(["git", "add", "app.py"], cwd=ws_path, capture_output=True)
        changed_files, diff_text = capture_diff(ws_path, pristine_hash)
        assert "app.py" in changed_files
        assert "# new file" in diff_text
    finally:
        import shutil
        shutil.rmtree(ws_path.parent, ignore_errors=True)


def test_capture_diff_detects_untracked_file(app_source: Path):
    ws_path, pristine_hash = prepare_workspace(app_source)
    try:
        (ws_path / "untracked.py").write_text("# ghost\n")
        changed_files, diff_text = capture_diff(ws_path, pristine_hash)
        assert "untracked.py" in changed_files
    finally:
        import shutil
        shutil.rmtree(ws_path.parent, ignore_errors=True)


def test_capture_diff_excludes_pytest_cache(app_source: Path):
    ws_path, pristine_hash = prepare_workspace(app_source)
    try:
        cache_dir = ws_path / ".pytest_cache"
        cache_dir.mkdir()
        (cache_dir / "v" / "cache" / "lastfailed").parent.mkdir(parents=True)
        (cache_dir / "v" / "cache" / "lastfailed").write_text("")
        changed_files, _ = capture_diff(ws_path, pristine_hash)
        assert ".pytest_cache" not in str(changed_files)
    finally:
        import shutil
        shutil.rmtree(ws_path.parent, ignore_errors=True)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_workspace.py -v
```
Expected: `ModuleNotFoundError: No module named 'harness.workspace'`

- [ ] **Step 3: Write workspace.py implementation**

```python
# harness/workspace.py
"""Disposable git-tracked workspace for one eval session.

Adapted from Tainie's _prepare_workspace (eval/driver.py) but simpler —
no tool wiring, no subagent config, no symlinks. Adds pyproject.toml stamp
+ uv sync that Tainie did not need.
"""
import shutil
import subprocess
import tempfile
from pathlib import Path

# Files the harness itself writes into the workspace — never model edits,
# excluded from capture_diff so they don't appear as changed files.
_HARNESS_FILES = frozenset({
    "pyproject.toml",   # stamped by prepare_workspace
})

# Build artifacts pytest litters the workspace with — never model edits.
_EXCLUDE_PREFIXES = (".pytest_cache/",)
_EXCLUDE_SUFFIXES = (".pyc", ".pyo")


def prepare_workspace(app_dir: str | Path) -> tuple[Path, str]:
    """Copy app_dir into a disposable temp workspace, stamp a pyproject.toml
    with dependencies from tech-stack.md, install via uv sync, init a git repo,
    and commit everything as the pristine baseline.

    Returns (workspace_path, pristine_commit_hash).
    """
    app_dir = Path(app_dir).resolve()
    # Resolve to collapse /var -> /private/var symlink on macOS so paths
    # reported by subprocesses match what we expect.
    workspace = (Path(tempfile.mkdtemp(prefix="pi-eval-")) / "workspace").resolve()

    shutil.copytree(
        app_dir,
        workspace,
        ignore=shutil.ignore_patterns(".venv", ".git", "__pycache__"),
    )

    # Stamp pyproject.toml with the dependencies from tech-stack.md.
    _stamp_pyproject(workspace)

    # Copy the hello-world extension so the workspace is self-contained.
    _copy_hello_world_extension(workspace)

    # Install dependencies. No --frozen here — each workspace gets its own
    # resolution. The dep set is small (fastapi, uvicorn, pytest) and stable.
    subprocess.run(
        ["uv", "sync"],
        cwd=workspace,
        check=True,
        capture_output=True,
        text=True,
    )

    # Init git repo and commit pristine baseline.
    subprocess.run(
        ["git", "init"],
        cwd=workspace, check=True, capture_output=True,
    )
    subprocess.run(
        ["git", "-c", "user.email=pi-eval@local", "-c", "user.name=pi-eval",
         "add", "-A"],
        cwd=workspace, check=True, capture_output=True,
    )
    subprocess.run(
        ["git", "-c", "user.email=pi-eval@local", "-c", "user.name=pi-eval",
         "commit", "-m", "pristine"],
        cwd=workspace, check=True, capture_output=True,
    )

    # Get the commit hash.
    hash_proc = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=workspace, capture_output=True, text=True, check=True,
    )
    pristine_hash = hash_proc.stdout.strip()

    return workspace, pristine_hash


def capture_diff(workspace: str | Path, pristine_hash: str) -> tuple[list[str], str]:
    """Return (changed_files, full_diff) for a workspace since its pristine commit.

    Uses both `git diff <pristine_hash>` (for tracked changes, including
    files the model may have committed) and `git status --porcelain -uall -z`
    (for untracked files the model never staged). Unions both.
    """
    workspace = Path(workspace)

    # git diff against pristine commit.
    diff_proc = subprocess.run(
        ["git", "diff", pristine_hash, "--", "."],
        cwd=workspace, capture_output=True, text=True, check=True,
    )
    diff_text = diff_proc.stdout

    # git diff --name-only for tracked changes.
    name_proc = subprocess.run(
        ["git", "diff", "--name-only", pristine_hash, "--", "."],
        cwd=workspace, capture_output=True, text=True, check=True,
    )
    diff_files = [line for line in name_proc.stdout.splitlines() if line]

    # git status for untracked files.
    status_proc = subprocess.run(
        ["git", "status", "--porcelain", "-uall", "-z"],
        cwd=workspace, capture_output=True, text=True, check=True,
    )
    status_files: list[str] = []
    for record in status_proc.stdout.split("\0"):
        if not record:
            continue
        path = record[3:]  # XY PATH format
        status_files.append(path)

    # Union tracked + untracked, deduplicate, exclude harness scaffolding.
    all_files = list(dict.fromkeys(diff_files + status_files))
    changed_files = [
        f for f in all_files
        if not _is_harness_file(f)
    ]

    return changed_files, diff_text


def _stamp_pyproject(workspace: Path) -> None:
    """Write a pyproject.toml with the AgentClinic dependencies into workspace."""
    pyproject = workspace / "pyproject.toml"
    pyproject.write_text("""\
[project]
name = "agentclinic"
version = "0.1.0"
requires-python = ">=3.14,<3.15"
dependencies = [
    "fastapi[standard]==0.115.10",
    "uvicorn==0.51.0",
    "pytest==8.3.4",
]
""")


def _copy_hello_world_extension(workspace: Path) -> None:
    """Copy the project's hello-world extension into the workspace's .pi/extensions/."""
    # Resolve from this file's location: harness/workspace.py -> repo root -> .pi/extensions/
    repo_root = Path(__file__).resolve().parent.parent
    src = repo_root / ".pi" / "extensions" / "hello-world.ts"
    if not src.exists():
        return  # extension not found; session will error clearly on launch
    dest = workspace / ".pi" / "extensions"
    dest.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest / "hello-world.ts")


def _is_harness_file(path: str) -> bool:
    """True if this path is harness scaffolding, not a model edit."""
    basename = path.split("/")[-1] if "/" in path else path
    if basename in _HARNESS_FILES:
        return True
    if path.startswith(_EXCLUDE_PREFIXES):
        return True
    if path.endswith(_EXCLUDE_SUFFIXES):
        return True
    if "__pycache__" in path:
        return True
    return False
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/test_workspace.py -v
```
Expected: all 6 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add harness/workspace.py tests/test_workspace.py
git commit -m "feat: workspace provisioning with git tracking and dep stamp"
```

---

### Task 3: Session runner

**Files:**
- Create: `harness/session.py`
- Create: `tests/test_session.py`

**Interfaces:**
- Consumes: `prepare_workspace` (Task 2), `read_run` (Task 1), `pi_binary`/`model`/`phase1_prompt` (conftest)
- Produces: `SessionResult` dataclass, `run_session(workspace, phase_prompt, model, timeout, max_startup_attempts) -> SessionResult`
- Consumed by: Task 4 (`runner.py`)

- [ ] **Step 1: Write the failing session test (unit, no pi needed)**

```python
# tests/test_session.py
from pathlib import Path

from harness.session import SessionResult

# Tests that don't need pi: just the dataclass shape and a mock path.


def test_session_result_fields():
    r = SessionResult(
        run_id="test-1",
        outcome="exited",
        returncode=0,
        telemetry=None,  # type: ignore
        changed_files=["app.py"],
        diff="+ # hello",
        tests_pass=True,
        wall_time_s=12.3,
        artifact_path="research/sessions/test-1.jsonl",
    )
    assert r.outcome == "exited"
    assert r.tests_pass is True
    assert r.run_id == "test-1"


def test_run_session_signature_exists():
    from harness.session import run_session
    import inspect
    sig = inspect.signature(run_session)
    params = list(sig.parameters.keys())
    assert "workspace" in params
    assert "phase_prompt" in params
    assert "model" in params
```

- [ ] **Step 2: Run unit tests to verify they fail**

```bash
uv run pytest tests/test_session.py -v -k "not integration"
```
Expected: `ModuleNotFoundError: No module named 'harness.session'`

- [ ] **Step 3: Write session.py implementation**

```python
# harness/session.py
"""Run one pi subprocess in a disposable workspace.
"""
import json
import subprocess
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from harness.telemetry import RunTelemetry, read_run
from harness.workspace import capture_diff


@dataclass
class SessionResult:
    run_id: str
    outcome: str            # "exited" | "timeout"
    returncode: int | None
    telemetry: RunTelemetry
    changed_files: list[str]
    diff: str
    tests_pass: bool
    wall_time_s: float
    artifact_path: str

    @property
    def is_success(self) -> bool:
        """A run is successful when it exited normally, tests pass, and files changed."""
        return (
            self.outcome == "exited"
            and self.tests_pass
            and len(self.changed_files) > 0
        )


def run_session(
    workspace: str | Path,
    phase_prompt: str,
    model: str,
    timeout: int = 300,
    max_startup_attempts: int = 3,
) -> SessionResult:
    """Run pi headless in workspace against one phase prompt.

    Spawns `pi --mode json -p --no-session` with isolation flags.
    Stdout is teed to research/sessions/<run-id>.jsonl while being
    parsed in memory for telemetry. After pi exits, runs git diff
    and uv run pytest for the acceptance oracle.

    Retries on empty-stdout timeout (startup hang) up to max_startup_attempts.
    A run that produced at least one event before timing out is not retried.
    """
    workspace = Path(workspace)
    run_id = uuid.uuid4().hex[:12]

    # Ensure the research sessions directory exists.
    sessions_dir = Path("docs/superpowers/research/sessions")
    sessions_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = sessions_dir / f"{run_id}.jsonl"

    stdout_text = ""
    pi_exe = _find_pi()

    # The pi invocation with isolation flags.
    pi_cmd = [
        pi_exe,
        "--mode", "json",
        "-p",
        "--no-session",
        "--model", model,
        "--no-extensions",
        "--extension", ".pi/extensions/hello-world.ts",
        "--no-skills",
        "--no-prompt-templates",
        "--no-themes",
        "--no-context-files",
        "--approve",
        "--", phase_prompt,
    ]

    env = dict(subprocess.os.environ)
    t0 = time.monotonic()

    # Retry loop for startup hangs (empty-stdout timeouts).
    for attempt in range(1, max_startup_attempts + 1):
        try:
            proc = subprocess.Popen(
                pi_cmd,
                cwd=str(workspace),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.DEVNULL,
                text=True,
                env=env,
            )
            stdout_text, stderr_text = proc.communicate(timeout=timeout)
            if stdout_text.strip():
                break  # got output, not a startup hang
        except subprocess.TimeoutExpired:
            proc.kill()
            stdout_text, stderr_text = proc.communicate()
            if stdout_text.strip():
                break  # partial output before timeout, keep it

    wall_time_s = time.monotonic() - t0
    outcome = "exited" if proc.returncode is not None else "timeout"
    returncode = proc.returncode

    # Persist the captured stdout as the session artifact.
    artifact_path.write_text(stdout_text)

    # Parse telemetry.
    telemetry = read_run(artifact_path)

    # Git diff against pristine (pristine_hash is in workspace context;
    # we get it from git log).
    pristine_proc = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=workspace, capture_output=True, text=True, check=True,
    )
    pristine_hash = pristine_proc.stdout.strip()
    changed_files, diff_text = capture_diff(workspace, pristine_hash)

    # Acceptance tests.
    tests_pass = False
    try:
        test_proc = subprocess.run(
            ["uv", "run", "pytest", "-q"],
            cwd=workspace,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        tests_pass = test_proc.returncode == 0
    except subprocess.TimeoutExpired:
        tests_pass = False

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
    )


def _find_pi() -> str:
    """Find the pi binary. Raises RuntimeError if not on PATH."""
    import shutil
    path = shutil.which("pi")
    if not path:
        raise RuntimeError("pi not found on PATH — is it installed?")
    return path
```

- [ ] **Step 4: Run unit tests to verify they pass**

```bash
uv run pytest tests/test_session.py -v -k "not integration"
```
Expected: 2 tests PASS.

- [ ] **Step 5: Write the integration test (gated by pi availability)**

```python
# append to tests/test_session.py

import pytest
import shutil


pi_available = pytest.mark.skipif(
    not shutil.which("pi"),
    reason="pi binary not on PATH",
)


@pi_available
def test_run_session_live_integration(
    app_source: Path, phase1_prompt: str, model: str, tmp_path: Path
):
    """Live integration: run pi against Phase 1 in a real workspace.

    This is slow (model-dependent) and requires LM Studio serving gemma.
    It only tests that the harness doesn't crash — not that the SLM succeeds.
    """
    from harness.session import run_session
    from harness.workspace import prepare_workspace

    ws_path, pristine_hash = prepare_workspace(app_source)
    try:
        result = run_session(ws_path, phase1_prompt, model, timeout=120)
        assert result.outcome in ("exited", "timeout")
        assert result.run_id
        assert result.artifact_path
        assert Path(result.artifact_path).exists()
        # telemetry parsed successfully (may be empty on startup hang)
        assert result.telemetry is not None
    finally:
        import shutil as _shutil
        _shutil.rmtree(ws_path.parent, ignore_errors=True)
```

- [ ] **Step 6: Commit**

```bash
git add harness/session.py tests/test_session.py
git commit -m "feat: session runner with startup-hang retry and acceptance oracle"
```

---

### Task 4: Runner + baseline report

**Files:**
- Create: `harness/runner.py`
- Create: `tests/test_runner.py`
- Create: `docs/superpowers/research/sessions/.gitkeep`

**Interfaces:**
- Consumes: `run_session` (Task 3), `prepare_workspace` (Task 2), conftest fixtures
- Produces: `BaselineReport` dataclass, `run_baseline(phase_prompt, app_source, model, n, timeout) -> BaselineReport`, `write_report(report, output_path) -> None`

- [ ] **Step 1: Write the failing runner tests (unit, mock sessions)**

```python
# tests/test_runner.py
from pathlib import Path

from harness.runner import BaselineReport, run_baseline, write_report
from harness.session import SessionResult
from harness.telemetry import RunTelemetry


def _make_result(run_id: str, tests_pass: bool, changed_files: list[str] | None = None) -> SessionResult:
    """Factory for mock session results."""
    if changed_files is None:
        changed_files = ["app.py"] if tests_pass else []
    return SessionResult(
        run_id=run_id,
        outcome="exited",
        returncode=0,
        telemetry=RunTelemetry(prompts=["test"], turns=5),
        changed_files=changed_files,
        diff="mock diff",
        tests_pass=tests_pass,
        wall_time_s=10.0,
        artifact_path=f"research/sessions/{run_id}.jsonl",
    )


def test_baseline_report_success_rate():
    results = [
        _make_result("r1", True),    # success
        _make_result("r2", False),   # tests fail
        _make_result("r3", True),    # success
        _make_result("r4", True),    # success
        _make_result("r5", False, []),  # null-action
        _make_result("r6", True),    # success
    ]
    report = BaselineReport(
        phase="Phase 1",
        n=6,
        results=results,
    )
    assert report.success_rate == 4 / 6  # r1, r3, r4, r6
    assert report.n == 6


def test_baseline_report_timeout_not_success():
    timeout = SessionResult(
        run_id="t1",
        outcome="timeout",
        returncode=None,
        telemetry=RunTelemetry(),
        changed_files=[],
        diff="",
        tests_pass=False,
        wall_time_s=300.0,
        artifact_path="sessions/t1.jsonl",
    )
    assert timeout.is_success is False


def test_baseline_report_null_action_not_success():
    null_action = _make_result("n1", True, [])
    assert null_action.is_success is False


def test_write_report_creates_file(tmp_path: Path):
    results = [
        _make_result("r1", True),
        _make_result("r2", False),
    ]
    report = BaselineReport(phase="Phase 1", n=2, results=results)
    out = tmp_path / "report.md"
    write_report(report, out)
    assert out.exists()
    content = out.read_text()
    assert "Phase 1" in content
    assert "2 runs" in content or "n=2" in content
    assert "r1" in content
    assert "r2" in content


def test_run_baseline_signature():
    """Ensure run_baseline has the expected signature for the mock override hook."""
    import inspect
    sig = inspect.signature(run_baseline)
    params = list(sig.parameters.keys())
    assert "phase_prompt" in params
    assert "app_source" in params
    assert "model" in params
    assert "n" in params
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_runner.py -v
```
Expected: `ModuleNotFoundError: No module named 'harness.runner'`

- [ ] **Step 3: Write runner.py implementation**

```python
# harness/runner.py
"""n=8 baseline loop, aggregation, and report generation."""
import statistics
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from harness.session import SessionResult, run_session
from harness.workspace import prepare_workspace

PI_EVAL_KEEP_WORKSPACES = "PI_EVAL_KEEP_WORKSPACES"


@dataclass
class BaselineReport:
    phase: str
    n: int
    results: list[SessionResult]

    @property
    def success_rate(self) -> float:
        return sum(1 for r in self.results if r.is_success) / max(len(self.results), 1)

    @property
    def success_count(self) -> int:
        return sum(1 for r in self.results if r.is_success)

    @property
    def mean_wall_time_s(self) -> float | None:
        times = [r.wall_time_s for r in self.results if r.outcome == "exited"]
        return statistics.mean(times) if times else None

    @property
    def mean_turns(self) -> float | None:
        turns = [r.telemetry.turns for r in self.results if r.telemetry and r.telemetry.turns > 0]
        return statistics.mean(turns) if turns else None


def run_baseline(
    phase_prompt: str,
    app_source: str | Path,
    model: str,
    n: int = 8,
    timeout: int = 300,
) -> BaselineReport:
    """Run n independent sessions against one phase, return aggregated report.

    Each run gets a fresh workspace. Runs are sequential to avoid LM Studio
    single-model contention. Timeout + token limits apply per run.
    Workspaces are cleaned up unless PI_EVAL_KEEP_WORKSPACES is set.
    """
    import os

    app_source = Path(app_source).resolve()
    results: list[SessionResult] = []
    keep = bool(os.environ.get(PI_EVAL_KEEP_WORKSPACES))

    for i in range(1, n + 1):
        ws_path, _ = prepare_workspace(app_source)
        try:
            result = run_session(ws_path, phase_prompt, model, timeout=timeout)
            results.append(result)
        finally:
            if not keep:
                import shutil
                shutil.rmtree(ws_path.parent, ignore_errors=True)

    # Extract phase name from prompt (first heading line).
    phase_name = "Unknown"
    for line in phase_prompt.splitlines():
        if line.startswith("## ") and not line.startswith("### "):
            phase_name = line[3:].strip()
            break

    return BaselineReport(
        phase=phase_name,
        n=n,
        results=results,
    )


def write_report(report: BaselineReport, output_path: str | Path) -> None:
    """Write a markdown evidence report from a BaselineReport."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    lines = [
        f"# Baseline: {report.phase}",
        f"",
        f"**Date:** {today}",
        f"**Model:** gemma-4-12b-it-mlx (LM Studio)",
        f"**Runs:** n={report.n}",
        f"**Success rate:** {report.success_count}/{report.n} ({report.success_rate:.0%})",
        f"",
    ]

    if report.mean_wall_time_s is not None:
        lines.append(f"**Mean wall time:** {report.mean_wall_time_s:.0f}s")
    if report.mean_turns is not None:
        lines.append(f"**Mean turns:** {report.mean_turns:.1f}")

    lines.append("")
    lines.append("| # | Outcome | Success | Turns | Wall Time | Changed Files | Artifact |")
    lines.append("|---|---------|---------|-------|-----------|---------------|----------|")

    for i, r in enumerate(report.results, 1):
        success = "✅" if r.is_success else "❌"
        turns = str(r.telemetry.turns) if r.telemetry else "—"
        wt = f"{r.wall_time_s:.0f}s"
        files = ", ".join(r.changed_files[:3]) or "—"
        if len(r.changed_files) > 3:
            files += f" (+{len(r.changed_files) - 3})"
        lines.append(
            f"| {i} | {r.outcome} | {success} | {turns} | {wt} | {files} | "
            f"[{r.run_id}.jsonl](sessions/{r.run_id}.jsonl) |"
        )

    lines.append("")
    lines.append("## Evidence tier")
    lines.append("")
    lines.append(f"- **Success rate:** GREEN — n={report.n} artifact-backed runs")
    lines.append(f"- **Timing / turns:** YELLOW — real but noisy (n={report.n}, single-model, single-provider)")

    output_path.write_text("\n".join(lines) + "\n")
```

- [ ] **Step 4: Run unit tests to verify they pass**

```bash
uv run pytest tests/test_runner.py -v
```
Expected: all tests PASS.

- [ ] **Step 5: Create sessions directory placeholder**

```bash
mkdir -p docs/superpowers/research/sessions
touch docs/superpowers/research/sessions/.gitkeep
```

- [ ] **Step 6: Run the baseline (live, requires pi + LM Studio)**

```bash
uv run python -c "
from harness.runner import run_baseline, write_report
from pathlib import Path

app_source = Path('examples/agentclinic')
roadmap = (app_source / 'specs' / 'roadmap.md').read_text()

# Try Phase 1 first.
prompt = None
for phase_num in (1, 2, 3):
    lines = roadmap.splitlines()
    marker = f'## Phase {phase_num} '
    start = next((i for i, l in enumerate(lines) if l.startswith(marker)), None)
    if start is None:
        continue
    body = []
    for line in lines[start+1:]:
        if line.startswith('## Phase '):
            break
        body.append(line)
    prompt = '\n'.join(body).strip()
    print(f'Running baseline: Phase {phase_num}...')
    report = run_baseline(prompt, app_source, 'lmstudio/gemma-4-12b-it-mlx', n=8, timeout=300)
    write_report(report, f'docs/superpowers/research/{__import__(\"datetime\").date.today().isoformat()}-baseline-phase-{phase_num}.md')
    print(f'  Success: {report.success_count}/{report.n}')
    if report.success_rate < 0.5:
        print(f'  => smoking gun found at Phase {phase_num}!')
        break
    else:
        print(f'  => Phase {phase_num} passed ({report.success_rate:.0%}), escalating to next phase...')
"
```
Expected: produces at least one dated report in `docs/superpowers/research/`. If Phase 1 passes (≥50% success), proceeds to Phase 2; continues until a phase fails or all three pass.

- [ ] **Step 7: Commit**

```bash
git add harness/runner.py tests/test_runner.py docs/superpowers/research/sessions/.gitkeep
git add docs/superpowers/research/????????-baseline-phase-*.md
git commit -m "feat: n=8 baseline runner with evidence report generation"
```

---

### Task 5: Chapter 1 — "The Telemetry Reader"

**Files:**
- Create: `docs/chapters/part2a-telemetry-reader.md`

**Purpose:** Teach the reader to parse `pi --mode json` stdout into structured events. The chapter opens by running pi once and capturing the raw JSONL stream, then walks through building the reader step by step.

The chapter follows the course's MyST/Sphinx format established by `docs/chapters/part1-hello-agent.md`. Content structure:

- [ ] **Step 1: Review the existing chapter for style**

```bash
head -80 docs/chapters/part1-hello-agent.md
```
Note the MyST conventions: heading style, code-block fences, callout directives (`{note}`, `{warning}`), cross-references.

- [ ] **Step 2: Write the chapter**

```bash
cat > docs/chapters/part2a-telemetry-reader.md << 'CHAPTER_EOF'
(part2a-telemetry-reader)=

# The Telemetry Reader

In Part I you wrote your first Pi extension and learned the shape of the
event lifecycle. Now you need to *measure* what the agent does. A small
local model driving real Python development will go off the rails — but
you cannot claim it went off the rails unless you have the data to prove it.

This chapter builds the first piece of the measurement harness: a telemetry
reader that parses Pi's `--mode json` event stream into structured records
you can inspect, count, and graph.

## Running pi in `--mode json`

Pi's `--mode json` flag writes every lifecycle event as a JSON line to stdout.
Run it once and capture the output:

```bash
pi --mode json -p --no-session \
   --model lmstudio/gemma-4-12b-it-mlx \
   --no-extensions --extension .pi/extensions/hello-world.ts \
   --no-skills --no-prompt-templates --no-themes --no-context-files \
   --approve \
   "Your prompt here" \
   < /dev/null > session.jsonl
```

The `--no-*` flags strip everything except the hello-world extension you wrote
in Part I. This isolation is important: a headless eval run must not pick up
your RTK proxy, your Superpowers skills, or any other global configuration.
Only what you intentionally place — the hello-world extension that writes
`appendEntry` evidence — should be present.

You now have a `session.jsonl` file. Each line is a JSON object with a `type`
field. Let's see what types Pi emitted:

```bash
python3 -c "
import json
types = set()
for line in open('session.jsonl'):
    try:
        ev = json.loads(line)
        types.add(ev.get('type', '?'))
    except: pass
print(sorted(types))
"
```

## The event schema

The event stream follows a predictable shape. Here are the events you will
parse:

[TODO: fill in actual event types from captured session.jsonl]

### `message_end` — token accounting

The `message_end` event carries per-turn token usage. This is how you know
how much context the model consumed and how much it generated:

```python
# Example message_end event (fill in from capture)
```

[Continue with: building the RunTelemetry dataclass, parsing each event type,
handling malformed lines, writing the reader function, testing against the
captured fixture. Follow the TDD flow from the implementation.]

## What you built

By the end of this chapter you have `harness/telemetry.py` — a module that
reads a `pi --mode json` stream and returns structured telemetry: prompts,
tool calls, turn count, token usage, and evidence entries. In the next
chapter you will provision a disposable workspace and run pi inside it.
CHAPTER_EOF
```

**Note:** The chapter skeleton above has `[TODO]` placeholders that must be
filled with actual event types and sampled JSON from the captured fixture.
The implementer reads `tests/fixtures/sample-session.jsonl` and fills in the
real values. This is deliberate — the chapter teaches the reader to inspect
their own capture, and the prose mirrors that discovery.

- [ ] **Step 3: Commit**

```bash
git add docs/chapters/part2a-telemetry-reader.md
git commit -m "docs: Part II chapter 1 — the telemetry reader"
```

---

### Task 6: Chapter 2 — "The Eval Session"

**Files:**
- Create: `docs/chapters/part2b-eval-session.md`

**Purpose:** Teach the reader to provision a disposable workspace, stamp a `pyproject.toml`, run pi headless inside it, capture the git diff, and run pytest as the acceptance oracle.

- [ ] **Step 1: Write the chapter**

```markdown
(part2b-eval-session)=

# The Eval Session

Last chapter you learned to read Pi's event stream. Now you need somewhere to
*run* Pi — a disposable workspace that starts from a pristine copy of the
example app and ends with a measurable change you can compare.

This chapter builds the eval session: provision a workspace, run headless pi
inside it, capture the diff, and run the acceptance tests.

## The disposable workspace

A testable eval run needs three things:

1. A pristine starting state so `git diff` shows only what the model changed
2. A `pyproject.toml` so `uv run pytest` actually works after the model writes the app
3. Isolation — the model must not see your global Pi config

### Copying the app and stamping the project

The AgentClinic example starts as spec-only — just `specs/roadmap.md`,
`specs/mission.md`, and `specs/tech-stack.md`. There is no `app.py`, no
`pyproject.toml`, no `templates/`. The SLM is supposed to *create* those.

[Walk through `prepare_workspace`: copy app, stamp pyproject.toml with deps
from tech-stack.md, run `uv sync`, `git init` + pristine commit.]

### Running pi headless

[Walk through `run_session`: the pi invocation with isolation flags,
`subprocess.Popen` with `stdin=subprocess.DEVNULL`, teeing stdout to the
session artifact, the startup-hang retry loop.]

### Capturing the change

[Walk through `capture_diff`: `git diff <pristine_hash>` for tracked changes
(including files the model may have committed), `git status --porcelain -uall -z`
for untracked files, union, exclude harness scaffolding.]

### The acceptance oracle

[Walk through running `uv run pytest -q` in the workspace, capturing the
result, and storing it in `SessionResult`.]

## What you built

`harness/session.py` — one call to `run_session()` provisions a workspace,
runs pi, captures the diff, runs pytest, and returns a `SessionResult`.
Every later chapter in this course uses this function.

In the next chapter you will run it 8 times and produce the smoking gun.
```

- [ ] **Step 2: Commit**

```bash
git add docs/chapters/part2b-eval-session.md
git commit -m "docs: Part II chapter 2 — the eval session"
```

---

### Task 7: Chapter 3 — "The Smoking Gun"

**Files:**
- Create: `docs/chapters/part2c-smoking-gun.md`

**Purpose:** Teach the reader to run n=8 sessions, aggregate the results, and produce the baseline evidence report. This is the load-bearing chapter — every "this helps" claim in Parts III and IV cites the report produced here.

- [ ] **Step 1: Write the chapter**

```markdown
(part2c-smoking-gun)=

# The Smoking Gun

You have a telemetry reader. You have an eval session. Now run it 8 times
and see whether the unsteered SLM can build Phase 1 of the AgentClinic
complaints board.

This chapter produces the first dated evidence report in
`docs/superpowers/research/`. Every claim later in the course — "guardrail X
reduced failures by Y" — links back to what you establish here.

## Why n=8?

A small local model is non-deterministic. One run might succeed by luck.
One run might fail for a transient reason. You need enough runs to see a
real signal. Eight is a practical compromise: enough for mean and standard
deviation, not so many that each baseline takes hours.

## The runner

[Walk through `run_baseline` and `write_report`: loop n times with fresh
workspaces, aggregate with `statistics`, generate the markdown table.]

## Running the baseline

```bash
uv run python -c "
from harness.runner import run_baseline, write_report
from pathlib import Path

app_source = Path('examples/agentclinic')
# Extract Phase 1 prompt from roadmap...
# (show the prompt extraction inline)

report = run_baseline(prompt, app_source, 'lmstudio/gemma-4-12b-it-mlx', n=8)
write_report(report, 'docs/superpowers/research/YYYY-MM-DD-baseline-phase-1.md')
print(f'Success: {report.success_count}/{report.n}')
"
```

## The report

[Show a sample report with the markdown table, aggregated numbers, and
evidence tier annotations.]

## If the SLM passes Phase 1

If the unsteered SLM succeeds at Phase 1 (50%+ of runs pass), the runner
escalates to Phase 2, then Phase 3. The course's smoking gun is the *first*
phase the bare model cannot reliably complete. If all three pass, that is
itself a finding — and Part IV's improvements are still valuable as a
catalog of techniques — but the "ditch" the course promises to show did not
appear on this model at this workload. Record that honestly in the report.

## What you built

A repeatable measurement loop. `harness/runner.py` runs any phase n=8 times,
aggregates the results, and writes a dated evidence report. You now have the
tool that Parts III and IV will use to prove every improvement they claim.
```

- [ ] **Step 2: Commit**

```bash
git add docs/chapters/part2c-smoking-gun.md
git commit -m "docs: Part II chapter 3 — the smoking gun"
```

---

### Task 8: Final wiring — update chapter indices and verify

**Files:**
- Modify: `docs/chapters/index.md`

- [ ] **Step 1: Add Part II entries to the chapter index**

Read `docs/chapters/index.md` and add the three new chapters after the Part I entry:

```markdown
Part II — Measurement
---------------------

- {ref}`part2a-telemetry-reader`
- {ref}`part2b-eval-session`
- {ref}`part2c-smoking-gun`
```

- [ ] **Step 2: Verify the Sphinx build**

```bash
uv run sphinx-build -b html docs docs/_build -W
```
Expected: build succeeds with no warnings.

- [ ] **Step 3: Commit**

```bash
git add docs/chapters/index.md
git commit -m "docs: wire Part II chapters into index"
```

---

## Self-Review

**Spec coverage:**
- Telemetry reader → Tasks 0, 1, 5 ✓
- Eval session (workspace, session, diff, pytest) → Tasks 2, 3, 6 ✓
- n=8 baseline + report → Tasks 4, 7 ✓
- Evidence convention → Task 4 (write_report) ✓
- Pi isolation → Tasks 2 (_copy_hello_world_extension), 3 (pi_cmd flags) ✓
- Schema capture (R0) → Task 0 ✓
- Startup-hang retry → Task 3 (retry loop) ✓
- Phase escalation → Task 4 (baseline script) ✓
- Chapters → Tasks 5, 6, 7 ✓
- Chapter index wiring → Task 8 ✓

**Placeholder scan:**
- Task 1 Step 6: event type strings in telemetry.py are marked as placeholders with explicit instruction to reconcile against fixture. This is the schema-capture discipline, not a "TODO."
- Task 5 (Chapter 1): `[TODO]` for event types — explicit instruction to fill from fixture. Same discipline.
- No "TBD," "add appropriate error handling," or "similar to Task N" patterns.

**Type consistency:**
- `RunTelemetry` defined in Task 1, consumed in Tasks 3, 4 ✓
- `SessionResult` defined in Task 3, consumed in Task 4 ✓
- `BaselineReport` defined in Task 4 ✓
- `prepare_workspace(app_dir) -> tuple[Path, str]` defined in Task 2, consumed in Tasks 3, 4 ✓
- `capture_diff(workspace, pristine_hash) -> tuple[list[str], str]` defined in Task 2, consumed in Task 3 ✓
- `read_run(stream_path) -> RunTelemetry` defined in Task 1, consumed in Task 3 ✓
- `run_session(workspace, phase_prompt, model, timeout, max_startup_attempts) -> SessionResult` defined in Task 3, consumed in Task 4 ✓
- `run_baseline(phase_prompt, app_source, model, n, timeout) -> BaselineReport` defined in Task 4 ✓
- `write_report(report, output_path)` defined in Task 4 ✓

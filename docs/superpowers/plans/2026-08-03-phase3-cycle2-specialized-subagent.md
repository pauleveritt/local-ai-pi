# Phase 3, Cycle 2 — Specialized subagent implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make one Pi run delegate to a child Pi run using this project's own `implementer` specialist, under an agent directory the project controls, with the delegation visible in the parent's captured stdout.

**Architecture:** Pi's shipped subagent extension is loaded by path alongside `hello-world.ts` — no TypeScript is written. `PI_CODING_AGENT_DIR`, which the spawned child inherits, points at a pre-provisioned directory holding our specialist and an empty `extensions/`, which both isolates the child from ambient extensions and makes the specialist discoverable from a disposable workspace. The shipped extension tree and the committed agent-directory skeleton are both digested into `RunConditions`.

**Tech Stack:** Python 3.14, pytest, ruff, pyrefly, Sphinx (MyST), `@earendil-works/pi-coding-agent` 0.82.0.

**Design:** `docs/superpowers/specs/2026-08-03-phase3-cycle2-specialized-subagent-design.md`

## Global Constraints

- Python `>=3.14,<3.15`. No new runtime dependencies. **No TypeScript is written or vendored.**
- Gates, all four before any commit: `uv run pytest`, `uv run ruff check .`, `uv run pyrefly check`, `uv run sphinx-build -W -b html docs docs/_build/html`.
- Ruff lint selects `E,F,I,UP,B,SIM`; `E501` ignored. Import sorting enforced.
- **Runs are sequential, never concurrent** — one shared local model has no isolation. Never launch a Pi run while another is in flight, and never abandon one: an orphaned run stays queued against the model server and makes the *next* run look hung. (This cost three data points during the spec work.)
- **Never `git commit` while a `run_batch()` is in flight.**
- Model server liveness before any live run: `uv run python -c "from harness.liveness import check_model_server_alive; check_model_server_alive(); print('alive')"`. When it is down, `pi` exits 0 with empty stderr and the harness records a fabricated result that looks like data.
- The controlled agent directory must be **pre-provisioned**. Pointing `PI_CODING_AGENT_DIR` at an empty directory makes Pi bootstrap — `git clone` of `obra/superpowers` plus npm installs. That path must be unreachable from the harness.
- Every new doc must be in a toctree in `docs/superpowers/index.md` or strict Sphinx fails.
- Work happens on branch `phase3` in the worktree at `.worktrees/phase3`.

---

## File Structure

| File | Responsibility | Change |
|---|---|---|
| `harness/subagent.py` | Resolving the shipped extension; provisioning the controlled agent dir | Create |
| `harness/runner.py` | Pi invocation, run conditions, batch contract | Modify |
| `harness/telemetry.py` | Derived measurements from stdout | Modify — delegations |
| `agentdir/agents/implementer.md` | The specialist, committed as data | Create |
| `agentdir/settings.json` | Settings for the controlled dir | Create |
| `agentdir/README.md` | What this directory is and why | Create |
| `examples/agentclinic/specs/orchestrator.md` | The prompt that gives the parent a reason to delegate | Create |
| `tests/test_subagent.py` | Resolver and provisioning tests | Create |
| `tests/test_runner.py`, `tests/test_telemetry.py` | Existing suites | Modify |
| `tests/fixtures/pi-run-0.82.0-delegation.jsonl` | Captured stdout of a real delegation | Create (Task 1) |
| `docs/superpowers/research/2026-08-03-phase3-cycle2-delegation-shape.md` | What a delegation looks like on the wire | Create (Task 1) |

---

## Task 1: The gating spike — what does a delegation look like on the wire?

The cycle's central unknown. The parent's `tool_execution_end` reaches stdout carrying `result` — confirmed in `tests/fixtures/pi-run-0.82.0-entry-appended.jsonl`, where every such event has keys `["isError","result","toolCallId","toolName","type"]`. But for builtin tools that `result` holds only `content`. **Whether the subagent tool's `details` — the child's messages, turns, and usage — survives into the raw event is unproven, and cycle 3 depends on it.**

This task is deliberately done by hand, outside the harness, so that the answer gates the machinery rather than the machinery gating the answer.

**Files:**
- Create: `tests/fixtures/pi-run-0.82.0-delegation.jsonl`
- Create: `docs/superpowers/research/2026-08-03-phase3-cycle2-delegation-shape.md`
- Modify: `docs/superpowers/index.md`

**Interfaces:**
- Consumes: nothing.
- Produces: the fixture, and a documented answer to whether `tool_execution_end.result.details` carries child usage. Tasks 5 and 6 depend on the answer.

- [ ] **Step 1: Resolve the shipped extension by hand**

Run:

```bash
uv run python -c "
import subprocess
from pathlib import Path
p = subprocess.run(['volta','which','pi'], capture_output=True, text=True)
c = Path(p.stdout.strip())
for parent in [c, *c.parents]:
    hit = parent / 'lib' / 'node_modules' / '@earendil-works' / 'pi-coding-agent' / 'examples' / 'extensions' / 'subagent'
    if hit.is_dir():
        print(hit); break
"
```

Expected: a path ending `examples/extensions/subagent`. Record it; the rest of this task refers to it as `$SUB`.

- [ ] **Step 2: Build a scratch agent directory by hand**

The scratch directory is **not** the committed one — Task 4 builds that. This is a throwaway used only to answer the spike's question.

```bash
SCRATCH=$(mktemp -d)/agentdir
mkdir -p "$SCRATCH/agents" "$SCRATCH/extensions"
cp ~/.pi/agent/models.json ~/.pi/agent/models-store.json ~/.pi/agent/auth.json "$SCRATCH/"
cat > "$SCRATCH/agents/implementer.md" <<'EOF'
---
name: implementer
description: Writes and edits Python files in the working directory to satisfy one stated requirement.
model: omlx/gemma-4-12B-it-MLX-8bit
---

You implement exactly one stated change in the current working directory.

Write the files you are asked for and nothing else. Do not explain your
reasoning at length. When you are finished, reply with a short list of the
files you created or changed.
EOF
echo "$SCRATCH"
```

Note `models.json`, `models-store.json`, and `auth.json` are copied so the relocated directory can reach the local model. **`extensions/` is created empty on purpose** — that is what excludes the ambient `rtk.ts`. No `AGENTS.md` is copied.

- [ ] **Step 3: Verify the model server is alive**

Run: `uv run python -c "from harness.liveness import check_model_server_alive; check_model_server_alive(); print('alive')"`
Expected: prints `alive`. If it raises, run `/Users/pauleveritt/.omlx/bin/omlx start` and re-check. Do not proceed on a dead server.

- [ ] **Step 4: Run one delegation by hand**

Use a Python wrapper rather than a bare shell command so the run has a hard timeout and cannot be orphaned against the single-threaded model server:

```bash
uv run python - <<'PY'
import os, subprocess, tempfile
SUB = "<the path from Step 1>"
SCRATCH = "<the path from Step 2>"
prompt = (
    "Use the subagent tool to delegate to the agent named 'implementer'. "
    "Give it this task: create a file called hello.py containing a function "
    "greet(name) that returns 'Hello, ' followed by the name. "
    "Do not write the file yourself; delegate it."
)
cmd = ["pi","--print","--mode","json","--no-session","--model","omlx/gemma-4-12B-it-MLX-8bit",
       "--no-extensions","--extension",SUB,"--no-skills","--no-prompt-templates","--no-themes",
       "--no-context-files","--approve",prompt]
env = {**os.environ, "PI_CODING_AGENT_DIR": SCRATCH}
work = tempfile.mkdtemp()
r = subprocess.run(cmd, cwd=work, env=env, capture_output=True, text=True, timeout=600)
open("tests/fixtures/pi-run-0.82.0-delegation.jsonl","w").write(r.stdout)
print("exit", r.returncode, "lines", len([l for l in r.stdout.split("\n") if l.strip()]))
print("stderr", r.stderr[:300])
PY
```

Expected: exit 0 and a substantial line count.

- [ ] **Step 5: Answer the spike's question**

Run:

```bash
uv run python - <<'PY'
import json
events = []
for line in open("tests/fixtures/pi-run-0.82.0-delegation.jsonl"):
    try: events.append(json.loads(line))
    except json.JSONDecodeError: pass
names = [e.get("toolName") for e in events if e.get("type") == "tool_execution_end"]
print("tool_execution_end toolNames:", names)
for e in events:
    if e.get("type") == "tool_execution_end" and e.get("toolName") == "subagent":
        res = e.get("result") or {}
        print("result keys:", sorted(res))
        det = res.get("details")
        print("details type:", type(det).__name__)
        if isinstance(det, dict):
            print("details keys:", sorted(det))
            print(json.dumps(det, indent=2)[:2000])
PY
```

Record the actual output. The question is answered either way:

- **If `details` is present with per-agent usage** — cycle 3's attribution is a reader over data already in `pi_stdout`. Say so.
- **If `details` is absent or empty** — cycle 3 needs another route. That is this cycle's finding, and Task 5's design changes shape. **Stop and report before continuing to Task 2.**

If no `subagent` tool call appears at all, the model declined to delegate. Retry once with a more explicit prompt; if it still declines, report — prompt design becomes the cycle's problem rather than plumbing.

- [ ] **Step 6: Write the research note**

Create `docs/superpowers/research/2026-08-03-phase3-cycle2-delegation-shape.md` recording, with file:line citations into the installed package where the claim is about Pi's behaviour:

- The exact command and environment used, verbatim
- The `tool_execution_end` event shape for `toolName: "subagent"`, quoted from the fixture
- Whether `details` carries child usage, and what fields exactly
- The count of `tool_execution_start`/`tool_execution_end` pairs, and which agent ran
- Whether the child's own stdout appears anywhere in the parent's stream
- **What this means for cycle 3**, stated plainly

State clearly which claims come from running and which from reading. This project's recurring failure is claims justified by reading alone.

- [ ] **Step 7: Add the note to the toctree**

In `docs/superpowers/index.md`, in the `:caption: Research` toctree, add after `research/2026-08-02-phase3-cycle1-event-vocabulary`:

```
research/2026-08-03-phase3-cycle2-delegation-shape
```

Add a matching bullet to the visible `## Research` list, following the style of its neighbours.

- [ ] **Step 8: Record the fixture's provenance**

Append a section to `tests/fixtures/README.md` following the shape of the existing `pi-run-0.82.0-entry-appended.jsonl` section:

```bash
shasum -a 256 tests/fixtures/pi-run-0.82.0-delegation.jsonl
wc -l -c tests/fixtures/pi-run-0.82.0-delegation.jsonl
```

State the SHA-256, line and byte counts, that it is `pi_stdout` from a hand-run delegation against `omlx/gemma-4-12B-it-MLX-8bit` under Pi 0.82.0 with the shipped subagent extension and a relocated `PI_CODING_AGENT_DIR`, and that it is the first fixture containing a delegation.

- [ ] **Step 9: Verify the docs build and commit**

Run: `rm -rf docs/_build && uv run sphinx-build -W -b html docs docs/_build/html`
Expected: `build succeeded.`

```bash
git add tests/fixtures/pi-run-0.82.0-delegation.jsonl tests/fixtures/README.md docs/superpowers/research/2026-08-03-phase3-cycle2-delegation-shape.md docs/superpowers/index.md
git commit -m "research(phase3-cycle2): what a delegation looks like on the wire

Hand-run delegation captured under a relocated PI_CODING_AGENT_DIR, so
the shape cycle 3 must read is established by running rather than by
reading the types.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Task 2: Digest a directory tree

Cycle 1's `_extension_digest` raises on a directory, deliberately, so this cycle would decide how a tree is hashed rather than inherit a plausible wrong answer. This is that decision.

**Files:**
- Modify: `harness/runner.py:134-143` (`_extension_digest`)
- Modify: `tests/test_runner.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `_extension_digest(path: Path) -> str` now accepts a directory and returns a SHA-256 over sorted relative paths and their file contents. Still raises `FileNotFoundError` for a missing path. Tasks 4 and 6 rely on it.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_runner.py`:

```python
def test_extension_digest_hashes_a_directory_tree(tmp_path):
    tree = tmp_path / "ext"
    (tree / "nested").mkdir(parents=True)
    (tree / "index.ts").write_text("one")
    (tree / "nested" / "agents.md").write_text("two")

    assert len(runner._extension_digest(tree)) == 64


def test_directory_digest_changes_when_any_file_changes(tmp_path):
    tree = tmp_path / "ext"
    (tree / "nested").mkdir(parents=True)
    (tree / "index.ts").write_text("one")
    (tree / "nested" / "agents.md").write_text("two")
    before = runner._extension_digest(tree)

    (tree / "nested" / "agents.md").write_text("changed")

    assert runner._extension_digest(tree) != before


def test_directory_digest_changes_when_a_file_is_renamed(tmp_path):
    # Content-only hashing would miss this: the bytes are identical and
    # only the path moved. A renamed agent file is a different extension.
    tree = tmp_path / "ext"
    tree.mkdir()
    (tree / "a.md").write_text("same")
    before = runner._extension_digest(tree)

    (tree / "a.md").rename(tree / "b.md")

    assert runner._extension_digest(tree) != before


def test_directory_digest_is_stable_across_calls(tmp_path):
    tree = tmp_path / "ext"
    tree.mkdir()
    (tree / "index.ts").write_text("one")

    assert runner._extension_digest(tree) == runner._extension_digest(tree)


def test_extension_digest_still_raises_on_a_missing_path(tmp_path):
    with pytest.raises(FileNotFoundError):
        runner._extension_digest(tmp_path / "absent")
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_runner.py -k digest -v`
Expected: the four directory tests FAIL with `ValueError: extension is a directory, not a file`. `test_extension_digest_still_raises_on_a_missing_path` passes already — a missing path is not a directory, so it reaches `read_bytes()` and raises `FileNotFoundError`.

- [ ] **Step 3: Replace the helper**

In `harness/runner.py`, replace `_extension_digest` entirely:

```python
def _extension_digest(path: Path) -> str:
    """SHA-256 identifying one extension, file or directory tree.

    A directory is hashed over its sorted relative paths *and* each
    file's contents, so that renaming a file changes the digest even
    though no byte of content did. Pi's shipped subagent extension is a
    tree whose `agents/*.md` filenames are meaningful, and a run made
    against a renamed specialist is a different run.

    Raises `FileNotFoundError` on a missing path, at conditions time,
    rather than 600 seconds into a run.
    """
    if not path.exists():
        raise FileNotFoundError(f"extension not found: {path}")
    if path.is_file():
        return hashlib.sha256(path.read_bytes()).hexdigest()

    digest = hashlib.sha256()
    for item in sorted(p for p in path.rglob("*") if p.is_file()):
        digest.update(str(item.relative_to(path)).encode())
        digest.update(b"\0")
        digest.update(hashlib.sha256(item.read_bytes()).digest())
    return digest.hexdigest()
```

- [ ] **Step 4: Update the directory-raises test from cycle 1**

`tests/test_runner.py` contains `test_extension_digest_raises_on_a_directory`, which asserted the deliberate deferral this task resolves. Delete it — the behaviour it pinned is now intentionally gone, and the four new tests cover the replacement. Do not leave it asserting the opposite of the code.

- [ ] **Step 5: Run the tests to verify they pass**

Run: `uv run pytest tests/test_runner.py -v`
Expected: all PASS.

- [ ] **Step 6: Run the full gates**

Run: `uv run pytest && uv run ruff check . && uv run pyrefly check`
Expected: all pass.

- [ ] **Step 7: Commit**

```bash
git add harness/runner.py tests/test_runner.py
git commit -m "feat(phase3-cycle2): digest a directory tree

Cycle 1 made _extension_digest raise on a directory so this cycle would
decide how a tree is hashed. It hashes sorted relative paths as well as
contents, so renaming an agent file changes the digest even though no
byte of content did.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Task 3: Resolve the shipped extension

**Files:**
- Create: `harness/subagent.py`
- Create: `tests/test_subagent.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `harness.subagent.subagent_extension_dir() -> Path`, returning the directory containing the shipped extension's `index.ts`. Raises `RuntimeError` with a remediation message if it cannot be found. Honours the environment variable `SATYRN_SUBAGENT_EXTENSION` as an override. Task 6 calls it.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_subagent.py`:

```python
import pytest

from harness.subagent import subagent_extension_dir


def test_resolves_the_installed_subagent_extension():
    # The real installed package. This is the one test in the suite that
    # depends on Pi being installed -- which every live run already does.
    resolved = subagent_extension_dir()

    assert resolved.is_dir()
    assert (resolved / "index.ts").is_file()


def test_an_explicit_override_wins(tmp_path, monkeypatch):
    override = tmp_path / "my-subagent"
    override.mkdir()
    (override / "index.ts").write_text("// stub")
    monkeypatch.setenv("SATYRN_SUBAGENT_EXTENSION", str(override))

    assert subagent_extension_dir() == override


def test_an_override_without_an_index_is_refused(tmp_path, monkeypatch):
    override = tmp_path / "not-an-extension"
    override.mkdir()
    monkeypatch.setenv("SATYRN_SUBAGENT_EXTENSION", str(override))

    with pytest.raises(RuntimeError, match="index.ts"):
        subagent_extension_dir()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_subagent.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'harness.subagent'`.

- [ ] **Step 3: Write the resolver**

Create `harness/subagent.py`:

```python
"""Locating Pi's shipped subagent extension, and provisioning the agent
directory both parent and child read.

The extension is used *by path*, never vendored. A copy would freeze our
code against a substrate that keeps moving -- the posture that produced
this project's two worst drift incidents -- while a path plus a digest in
`RunConditions` makes a Pi upgrade refuse a checkpoint resume instead.
"""

import os
import shutil
import subprocess
from pathlib import Path

_ENV_OVERRIDE = "SATYRN_SUBAGENT_EXTENSION"
_RELATIVE = Path("examples") / "extensions" / "subagent"
_PACKAGE = Path("lib") / "node_modules" / "@earendil-works" / "pi-coding-agent"


def subagent_extension_dir() -> Path:
    """Directory holding the installed subagent extension's `index.ts`."""
    override = os.environ.get(_ENV_OVERRIDE)
    if override:
        candidate = Path(override)
        if not (candidate / "index.ts").is_file():
            raise RuntimeError(
                f"{_ENV_OVERRIDE}={override} has no index.ts; it is not an extension"
            )
        return candidate

    for start in _pi_locations():
        for parent in [start, *start.parents]:
            for candidate in (parent / _RELATIVE, parent / _PACKAGE / _RELATIVE):
                if (candidate / "index.ts").is_file():
                    return candidate

    raise RuntimeError(
        "could not locate Pi's shipped subagent extension; "
        f"set {_ENV_OVERRIDE} to the directory containing its index.ts"
    )


def _pi_locations() -> list[Path]:
    """Where the `pi` executable might be, most specific first.

    `volta which` is asked first because a volta-managed `pi` on PATH is
    a shim, and resolving the shim leads to volta rather than to Pi.
    """
    locations = []
    try:
        found = subprocess.run(
            ["volta", "which", "pi"], capture_output=True, text=True, timeout=10
        )
        if found.returncode == 0 and found.stdout.strip():
            locations.append(Path(found.stdout.strip()))
    except (OSError, subprocess.SubprocessError):
        pass
    on_path = shutil.which("pi")
    if on_path:
        locations.append(Path(on_path).resolve())
    return locations
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_subagent.py -v`
Expected: all PASS.

- [ ] **Step 5: Run the full gates**

Run: `uv run pytest && uv run ruff check . && uv run pyrefly check`
Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add harness/subagent.py tests/test_subagent.py
git commit -m "feat(phase3-cycle2): resolve Pi's shipped subagent extension

Used by path, never vendored. volta's shim is asked first because
resolving it from PATH leads to volta rather than to Pi.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Task 4: The controlled agent directory

**Files:**
- Create: `agentdir/agents/implementer.md`
- Create: `agentdir/settings.json`
- Create: `agentdir/README.md`
- Modify: `harness/subagent.py`
- Modify: `tests/test_subagent.py`

**Interfaces:**
- Consumes: nothing from Task 3 beyond the module existing.
- Produces: `harness.subagent.AGENT_DIR_SKELETON: Path` (the committed `agentdir/`), and `harness.subagent.provision_agent_dir(destination: Path) -> Path`, which copies the skeleton plus the local model configuration into `destination` and returns it. Task 6 calls it.

- [ ] **Step 1: Write the specialist**

Create `agentdir/agents/implementer.md`:

```markdown
---
name: implementer
description: Writes and edits Python files in the working directory to satisfy one stated requirement. Use for any task that creates or changes code.
model: omlx/gemma-4-12B-it-MLX-8bit
---

You implement exactly one stated change in the current working directory.

Write the files you are asked for and nothing else. Do not restate the task,
and do not explain your reasoning at length. When you are finished, reply
with a short list of the files you created or changed.
```

The `model:` line is load-bearing. `--model` is passed to the child only `if (agent.model)` (`index.ts:295`), so an `implementer.md` without it spawns a child running Pi's *default* model — potentially a cloud model, silently, inside a measurement of a local one.

- [ ] **Step 2: Write the settings and the README**

Create `agentdir/settings.json`:

```json
{}
```

Deliberately empty. In particular it must not set `defaultProjectTrust`: `"always"` would make project-local files trusted in the workspace, reopening the channel that `--no-extensions` closes.

Create `agentdir/README.md`:

```markdown
# The controlled agent directory

This is the skeleton of the directory Pi reads when the harness sets
`PI_CODING_AGENT_DIR`. It is committed as data, not generated.

**Why it exists.** Pi's shipped subagent extension spawns its child with
`["--mode","json","-p","--no-session"]` and nothing else — the child
inherits none of the harness's isolation flags. It does inherit the
environment, and `getAgentDir()` honours `PI_CODING_AGENT_DIR`. So pointing
that variable at this directory does two jobs at once: the child cannot see
ambient extensions in `~/.pi/agent/extensions/`, and `agents/implementer.md`
is found as a *user-scope* agent regardless of the working directory — which
matters because project-scope agents are discovered by walking up from cwd,
and the harness runs in a disposable temp workspace.

**`extensions/` is empty on purpose.** That emptiness is the isolation.

**There is no `AGENTS.md` here on purpose.** One in the agent directory would
be loaded into the child's context.

**Never point `PI_CODING_AGENT_DIR` at an empty directory.** Pi bootstraps a
missing agent directory by cloning a third-party repository and running npm
installs — slow, network-dependent, and pinned to nobody's revision.
`provision_agent_dir` copies this skeleton plus the local model
configuration; a missing skeleton fails loudly instead.

Model configuration (`models.json`, `models-store.json`, `auth.json`) is
copied from the real agent directory at provisioning time rather than
committed, because it is machine-specific and `auth.json` holds credentials.
```

- [ ] **Step 3: Write the failing tests**

Append to `tests/test_subagent.py`:

```python
import json

from harness.subagent import AGENT_DIR_SKELETON, provision_agent_dir


def test_the_specialist_pins_the_local_model():
    # --model is passed to the child only `if (agent.model)`. Without this
    # line the delegated half of a run silently uses Pi's default model.
    text = (AGENT_DIR_SKELETON / "agents" / "implementer.md").read_text()

    assert "model: omlx/gemma-4-12B-it-MLX-8bit" in text


def test_the_skeleton_ships_an_empty_extensions_dir():
    # The emptiness is the isolation: it is what the child sees instead of
    # ~/.pi/agent/extensions/.
    extensions = AGENT_DIR_SKELETON / "extensions"

    assert extensions.is_dir()
    assert list(extensions.iterdir()) == []


def test_the_skeleton_carries_no_agents_md():
    # One here would be loaded into the child's context.
    assert not (AGENT_DIR_SKELETON / "AGENTS.md").exists()


def test_settings_do_not_grant_default_project_trust():
    settings = json.loads((AGENT_DIR_SKELETON / "settings.json").read_text())

    assert settings.get("defaultProjectTrust") is None


def test_provisioning_copies_the_specialist_and_model_config(tmp_path):
    destination = provision_agent_dir(tmp_path / "agentdir")

    assert (destination / "agents" / "implementer.md").is_file()
    assert (destination / "extensions").is_dir()
    assert (destination / "models.json").is_file()


def test_provisioning_is_idempotent(tmp_path):
    destination = tmp_path / "agentdir"
    provision_agent_dir(destination)

    provision_agent_dir(destination)

    assert (destination / "agents" / "implementer.md").is_file()
```

- [ ] **Step 4: Run the tests to verify they fail**

Run: `uv run pytest tests/test_subagent.py -v`
Expected: FAIL with `ImportError: cannot import name 'AGENT_DIR_SKELETON'`.

- [ ] **Step 5: Create the empty extensions directory**

Git does not track empty directories, so the skeleton's `extensions/` needs a keeper file that is not itself an extension:

```bash
mkdir -p agentdir/extensions
printf '%s\n' "This directory is empty on purpose; see ../README.md." > agentdir/extensions/.gitkeep
```

`.gitkeep` is not a `.ts` file, so Pi's extension discovery ignores it. `test_the_skeleton_ships_an_empty_extensions_dir` must therefore ignore dotfiles — update its assertion to:

```python
    assert [p.name for p in extensions.iterdir() if not p.name.startswith(".")] == []
```

- [ ] **Step 6: Write the provisioner**

Append to `harness/subagent.py`:

```python
REPO_ROOT = Path(__file__).resolve().parents[1]
AGENT_DIR_SKELETON = REPO_ROOT / "agentdir"

# Machine-specific and credential-bearing, so copied at provisioning time
# rather than committed. Without them the relocated directory cannot reach
# the local model server.
_MODEL_CONFIG = ("models.json", "models-store.json", "auth.json", "trust.json")


def provision_agent_dir(destination: Path) -> Path:
    """Copy the committed skeleton plus local model config into place.

    Pi bootstraps a *missing* agent directory by cloning a third-party
    repository and running npm installs. Provisioning must therefore
    always run before an invocation, and must fail loudly when the
    skeleton is absent rather than leaving Pi to improvise.
    """
    if not AGENT_DIR_SKELETON.is_dir():
        raise RuntimeError(f"agent directory skeleton missing: {AGENT_DIR_SKELETON}")

    shutil.copytree(AGENT_DIR_SKELETON, destination, dirs_exist_ok=True)
    (destination / "extensions").mkdir(exist_ok=True)

    source = Path.home() / ".pi" / "agent"
    for name in _MODEL_CONFIG:
        candidate = source / name
        if candidate.is_file():
            shutil.copy2(candidate, destination / name)

    if not (destination / "models.json").is_file():
        raise RuntimeError(
            f"no models.json found at {source}; the provisioned agent "
            "directory cannot reach the model server"
        )
    return destination
```

- [ ] **Step 7: Run the tests to verify they pass**

Run: `uv run pytest tests/test_subagent.py -v`
Expected: all PASS.

- [ ] **Step 8: Run the full gates**

Run: `uv run pytest && uv run ruff check . && uv run pyrefly check`
Expected: all pass. If ruff flags `agentdir/` content, confirm it contains no Python; it should not.

- [ ] **Step 9: Commit**

```bash
git add agentdir harness/subagent.py tests/test_subagent.py
git commit -m "feat(phase3-cycle2): the controlled agent directory

Committed as data: the implementer specialist, an empty extensions
directory whose emptiness is the isolation, and no AGENTS.md. Model
configuration is copied at provisioning time because it is
machine-specific and one file holds credentials.

The specialist pins the local model. --model reaches the child only if
the agent's frontmatter sets it, so omitting it would run the delegated
half of a measurement on Pi's default model.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Task 5: Delegations in telemetry

**Files:**
- Modify: `harness/telemetry.py`
- Modify: `tests/test_telemetry.py`

**Interfaces:**
- Consumes: `tests/fixtures/pi-run-0.82.0-delegation.jsonl` from Task 1.
- Produces: a frozen dataclass `harness.telemetry.Delegation` with fields `agent: str | None` and `mode: str | None`, and `RunTelemetry.delegations: tuple[Delegation, ...]` declared as the **last** field, after `custom_entries`. Task 6 relies on both.

**Before writing code, read Task 1's research note.** It records the actual shape of a `subagent` `tool_execution_end`. If `details` is absent, the field extraction below must be adjusted to what the note documents, and the note — not this plan — is the authority.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_telemetry.py`:

```python
DELEGATION_FIXTURE = Path(__file__).parent / "fixtures" / "pi-run-0.82.0-delegation.jsonl"


def test_reads_a_delegation_from_a_real_run():
    telemetry = read_telemetry(DELEGATION_FIXTURE.read_text())

    assert len(telemetry.delegations) >= 1
    assert telemetry.delegations[0].agent == "implementer"


def test_a_run_without_delegations_has_none():
    assert read_telemetry(_real_run()).delegations == ()


def test_reads_the_delegation_mode():
    stream = json.dumps({
        "type": "tool_execution_end",
        "toolName": "subagent",
        "toolCallId": "t1",
        "result": {"details": {"mode": "parallel", "results": [{"agent": "implementer"}]}},
    })

    assert read_telemetry(stream).delegations == (
        Delegation(agent="implementer", mode="parallel"),
    )


def test_a_delegation_with_no_details_is_still_recorded():
    # The tool ran. Recording it as unknown-shaped is honest; dropping it
    # would under-count delegations and quietly weaken the refusal check.
    stream = json.dumps({
        "type": "tool_execution_end", "toolName": "subagent",
        "toolCallId": "t1", "result": {"content": "done"},
    })

    assert read_telemetry(stream).delegations == (Delegation(agent=None, mode=None),)


def test_non_subagent_tools_are_not_delegations():
    assert read_telemetry(_real_run()).delegations == ()
```

Add `Delegation` to the existing `from harness.telemetry import …` line.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_telemetry.py -k delegation -v`
Expected: FAIL with `ImportError: cannot import name 'Delegation'`.

- [ ] **Step 3: Add the dataclass and the field**

In `harness/telemetry.py`, add after the `ToolCall` dataclass:

```python
@dataclass(frozen=True)
class Delegation:
    agent: str | None  # None = the tool ran but reported no agent name
    mode: str | None  # None = no mode reported; "single" is the only one accepted
```

And add to `RunTelemetry` as the last field, after `custom_entries`:

```python
    delegations: tuple[Delegation, ...]
```

- [ ] **Step 4: Parse them**

In `read_telemetry`, add an accumulator beside the others:

```python
    delegations: list[Delegation] = []
```

Extend the existing `case "tool_execution_end":` branch. It currently reads:

```python
            case "tool_execution_end":
                ended[event["toolCallId"]] = event.get("isError")
```

Replace with:

```python
            case "tool_execution_end":
                ended[event["toolCallId"]] = event.get("isError")
                if event.get("toolName") == "subagent":
                    delegations.append(_delegation(event))
```

And add the helper below `read_telemetry`:

```python
def _delegation(event: dict) -> Delegation:
    """Read one `subagent` tool result into a Delegation.

    Tolerant in the module's established style: a result that carries no
    details is recorded with unknown fields rather than dropped. The tool
    ran either way, and under-counting delegations would quietly weaken
    the check that refuses non-single modes.
    """
    result = event.get("result")
    details = result.get("details") if isinstance(result, dict) else None
    if not isinstance(details, dict):
        return Delegation(agent=None, mode=None)
    mode = details.get("mode")
    results = details.get("results")
    first = results[0] if isinstance(results, list) and results else None
    agent = first.get("agent") if isinstance(first, dict) else None
    return Delegation(
        agent=agent if isinstance(agent, str) else None,
        mode=mode if isinstance(mode, str) else None,
    )
```

Pass it in the return:

```python
        custom_entries=tuple(custom_entries),
        delegations=tuple(delegations),
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `uv run pytest tests/test_telemetry.py -v`
Expected: all PASS. If `test_reads_a_delegation_from_a_real_run` fails, the fixture's shape differs from Task 1's note — trust the fixture, fix the parser, and say so in the report.

- [ ] **Step 6: Run the full gates**

Run: `uv run pytest && uv run ruff check . && uv run pyrefly check`
Expected: all pass.

- [ ] **Step 7: Commit**

```bash
git add harness/telemetry.py tests/test_telemetry.py
git commit -m "feat(phase3-cycle2): read delegations from captured stdout

A subagent tool_execution_end becomes a Delegation carrying the agent
name and the mode. A result with no details is recorded with unknown
fields rather than dropped: the tool ran either way, and under-counting
would weaken the refusal check that keeps runs sequential.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Task 6: Enable the delegation end to end

**Files:**
- Modify: `harness/runner.py`
- Modify: `tests/test_runner.py`
- Create: `examples/agentclinic/specs/orchestrator.md`
- Modify: `ROADMAP.md`, `docs/superpowers/index.md`

**Interfaces:**
- Consumes: `subagent_extension_dir()` and `provision_agent_dir()` from Tasks 3-4; `Delegation` and `RunTelemetry.delegations` from Task 5; `_extension_digest`'s directory support from Task 2.
- Produces: the finished cycle.

- [ ] **Step 1: Write the orchestrator prompt**

Create `examples/agentclinic/specs/orchestrator.md`:

```markdown
Build a small FastAPI application in the current directory.

You have a `subagent` tool. Use it to delegate the implementation to the
agent named `implementer`, one task at a time. Do not write application
files yourself — your job is to decide what is needed and to delegate it.

Delegate one task at a time and wait for each to finish before starting the
next.

The application needs:

- `app.py` exposing a FastAPI app with a `GET /` route returning HTML
- `templates/index.html` rendered by that route
- `tests/test_app.py` covering the route with `TestClient`
```

The "one task at a time" instruction is doing real work: it is the prompt-level counterpart of the refusal check, keeping one child on the single-threaded model server at a time.

- [ ] **Step 2: Write the failing tests**

Append to `tests/test_runner.py`:

```python
def test_pi_command_loads_the_subagent_extension():
    command = _pi_command("model-name", "task text")

    flagged = [
        command[i + 1] for i, item in enumerate(command) if item == "--extension"
    ]
    assert any(path.endswith("subagent") for path in flagged)


def test_run_batch_refuses_a_run_that_delegated_in_parallel(tmp_path, monkeypatch):
    # Parallel mode would put several children on the single-threaded local
    # model at once -- the isolation rule broken from inside a run.
    checkpoint = tmp_path / "checkpoint.jsonl"
    conditions = RunConditions(
        "model", ("pi",), "0.82.0", "sha", "rev", 600, 30, ("digest",), "agentsha"
    )
    monkeypatch.setattr(runner, "_conditions", lambda *args: conditions)
    stdout = json.dumps({
        "type": "tool_execution_end", "toolName": "subagent", "toolCallId": "t1",
        "result": {"details": {"mode": "parallel", "results": [{"agent": "implementer"}]}},
    })
    monkeypatch.setattr(
        runner,
        "run_agentclinic_phase1",
        lambda **kwargs: RunResult(
            "d", _grade_result(), stdout, "", 0, conditions=conditions
        ),
    )

    with pytest.raises(RuntimeError, match="single"):
        runner.run_batch(checkpoint, target=1, model="model")


def test_run_batch_accepts_a_single_mode_delegation(tmp_path, monkeypatch):
    checkpoint = tmp_path / "checkpoint.jsonl"
    conditions = RunConditions(
        "model", ("pi",), "0.82.0", "sha", "rev", 600, 30, ("digest",), "agentsha"
    )
    monkeypatch.setattr(runner, "_conditions", lambda *args: conditions)
    stdout = json.dumps({
        "type": "tool_execution_end", "toolName": "subagent", "toolCallId": "t1",
        "result": {"details": {"mode": "single", "results": [{"agent": "implementer"}]}},
    })
    monkeypatch.setattr(
        runner,
        "run_agentclinic_phase1",
        lambda **kwargs: RunResult(
            "d", _grade_result(), stdout, "", 0, conditions=conditions
        ),
    )

    records = runner.run_batch(checkpoint, target=1, model="model")

    assert len(records) == 1
```

- [ ] **Step 3: Run the tests to verify they fail**

Run: `uv run pytest tests/test_runner.py -k "subagent or delegat" -v`
Expected: FAIL — the extension is not yet in the command, and `run_batch` does not yet check modes.

- [ ] **Step 4: Load the extension and set the environment**

In `harness/runner.py`, add the import:

```python
from harness.subagent import provision_agent_dir, subagent_extension_dir
```

Change `EXTENSIONS` to include the shipped tree — **resolved lazily, not at import time**:

```python
@cache
def extensions() -> tuple[Path, ...]:
    """The extensions every run loads, resolved on first use.

    Not a module constant: `subagent_extension_dir()` raises when Pi is
    not installed, and a constant would turn that into a collection
    error for the whole test suite rather than a failure of the tests
    that actually need Pi.
    """
    return (
        REPO_ROOT / ".pi" / "extensions" / "hello-world.ts",
        subagent_extension_dir(),
    )
```

Add `from functools import cache` at the top. Delete the `EXTENSIONS` constant and change both signatures that defaulted to it — `_pi_command(model, prompt, extensions=EXTENSIONS)` and `_conditions(model, command, timeout, extensions=EXTENSIONS)` — to default to `None` and resolve inside:

```python
def _pi_command(
    model: str, prompt: str, extensions: tuple[Path, ...] | None = None
) -> list[str]:
    paths = extensions if extensions is not None else globals()["extensions"]()
```

That `globals()` lookup is ugly. Avoid it by naming the function `resolved_extensions()` instead of `extensions()`, and keeping the parameter named `extensions`:

```python
@cache
def resolved_extensions() -> tuple[Path, ...]:
    ...


def _pi_command(
    model: str, prompt: str, extensions: tuple[Path, ...] | None = None
) -> list[str]:
    paths = resolved_extensions() if extensions is None else extensions
```

Apply the same `None` default and resolution to `_conditions`. Update cycle 1's `test_pi_command_defaults_to_the_projects_extensions`, which references `runner.EXTENSIONS`, to call `runner.resolved_extensions()`.

In `run_agentclinic_phase1`, provision the agent directory inside the workspace's parent and pass it to Pi. Replace the `run_process(...)` call so it reads:

```python
        agent_dir = provision_agent_dir(workspace.parent / "satyrn-agentdir")
        pi_proc = run_process(
            command,
            timeout=timeout,
            cwd=workspace,
            env={**os.environ, "PI_CODING_AGENT_DIR": str(agent_dir)},
        )
```

Add `import os` at the top if absent. The child inherits this environment, which is the whole mechanism.

- [ ] **Step 5: Record the specialist as a run condition**

The spec requires the provisioned agent directory to be digested too — *"the implementer's system prompt is a run condition exactly as the task spec is"*. Digest the **committed skeleton**, not the provisioned copy: the copy carries `models.json` and `auth.json`, which are machine-specific and would make the digest differ between contributors for reasons unrelated to the run.

Add a field to `RunConditions`, last, after `extension_digests`:

```python
    agent_dir_digest: str
```

Extend its docstring with:

```
    `agent_dir_digest` covers the committed agent-directory skeleton,
    whose `agents/implementer.md` is the delegated half of a run's
    system prompt. Editing that prompt changes what was measured as
    surely as editing the task spec does. The skeleton is digested
    rather than the provisioned copy, because the copy carries
    machine-specific model configuration.
```

Set it in `_conditions`:

```python
        agent_dir_digest=_extension_digest(AGENT_DIR_SKELETON),
```

importing `AGENT_DIR_SKELETON` from `harness.subagent`. In `harness/checkpoint.py`, add to the `RunConditions(...)` construction, using the same sentinel discipline cycle 1 established:

```python
                        agent_dir_digest=data["conditions"].get(
                            "agent_dir_digest", "<pre-cycle2>"
                        ),
```

Then update every existing positional `RunConditions(...)` construction in `tests/test_runner.py` and the keyword one in `tests/test_checkpoint.py` to supply the ninth value — `"agentsha"` positionally, or `agent_dir_digest="agentsha"` by keyword. Run `grep -rn "RunConditions(" harness/ tests/` to find them all; missing one is a `TypeError`.

Add this test to `tests/test_runner.py`:

```python
def test_conditions_record_the_agent_directory_digest():
    first = runner._conditions("model", ["pi"], 600, extensions=())

    assert len(first.agent_dir_digest) == 64
```

and this to `tests/test_checkpoint.py`:

```python
def test_a_checkpoint_predating_the_agent_digest_still_loads(tmp_path):
    path = tmp_path / "checkpoint.jsonl"
    record = json.loads(json.dumps(asdict(replace(
        _sample_result(),
        conditions=RunConditions(
            model="model", pi_command=("pi",), pi_version="0.82.0",
            task_spec_sha256="abc", harness_revision="def", run_timeout=600,
            grade_timeout=30, extension_digests=("x",), agent_dir_digest="y",
        ),
    ))))
    del record["conditions"]["agent_dir_digest"]
    path.write_text(json.dumps(record) + "\n")

    loaded = load_checkpoint(path)

    assert loaded[0].conditions is not None
    assert loaded[0].conditions.agent_dir_digest == "<pre-cycle2>"
```

Run: `uv run pytest tests/test_runner.py tests/test_checkpoint.py -v`
Expected: all PASS.

- [ ] **Step 6: Add the refusal check**

In `harness/runner.py`, inside `run_batch`'s loop, after `result = run_agentclinic_phase1(model=model)` and before `append_checkpoint`:

```python
        _refuse_unless_single_mode(result)
```

And add the helper:

```python
def _refuse_unless_single_mode(result: RunResult) -> None:
    """Abort the batch on any delegation that was not single-mode.

    Pi's subagent tool also offers parallel and chain modes. Parallel
    would put several children on the local model at once, and this
    project runs sequentially because one shared local model has no
    isolation. Refusing here rather than in grading is deliberate: the
    run may be perfectly good work, but it was made under conditions the
    batch does not accept -- the same posture as a conditions mismatch.
    """
    from harness.telemetry import read_telemetry

    for delegation in read_telemetry(result.pi_stdout).delegations:
        if delegation.mode is not None and delegation.mode != "single":
            raise RuntimeError(
                f"run delegated in {delegation.mode!r} mode; only 'single' is accepted"
            )
```

- [ ] **Step 7: Run the tests to verify they pass**

Run: `uv run pytest -v`
Expected: all PASS, two skipped. `test_pi_command_defaults_to_the_projects_extensions` from cycle 1 asserts one `--extension` per entry in `EXTENSIONS` and should still pass with two entries.

- [ ] **Step 8: Verify the model server, then prove it live**

Run: `uv run python -c "from harness.liveness import check_model_server_alive; check_model_server_alive(); print('alive')"`
Expected: `alive`.

Then add this live test to `tests/test_runner.py` and run it:

```python
@pytest.mark.skipif(
    os.environ.get("SATYRN_LIVE") != "1",
    reason="set SATYRN_LIVE=1 to require an actual Pi/model run",
)
def test_a_live_run_delegates_to_our_implementer():
    from harness.telemetry import read_telemetry

    result = run_agentclinic_phase1()
    delegations = read_telemetry(result.pi_stdout).delegations

    assert delegations, "no delegation reached the parent's stdout"
    assert any(d.agent == "implementer" for d in delegations)
    assert all(d.mode in (None, "single") for d in delegations)
```

Run: `SATYRN_LIVE=1 uv run pytest tests/test_runner.py::test_a_live_run_delegates_to_our_implementer -v`
Expected: PASS.

This run uses `TASK_SPEC`, not the orchestrator prompt. If it fails because the model never delegates, that is the finding: the task spec gives no reason to delegate. Report it — wiring the orchestrator prompt into the harness as a selectable task is cycle 3 or 4's business, not a silent change here.

- [ ] **Step 9: Close the cycle in the roadmap**

In `ROADMAP.md`, change the Phase 3 cycle 2 row's **State** from `Specced` to `Done`, and add a link to the plan beside the existing spec link.

- [ ] **Step 10: Add the plan to the toctree**

In `docs/superpowers/index.md`, in the `:caption: Plans` toctree, add after `plans/2026-08-02-phase3-cycle1-observable-extension`:

```
plans/2026-08-03-phase3-cycle2-specialized-subagent
```

- [ ] **Step 11: Run the full gates**

Run: `uv run pytest && uv run ruff check . && uv run pyrefly check`
then `rm -rf docs/_build && uv run sphinx-build -W -b html docs docs/_build/html`
Expected: all pass, `build succeeded.`

- [ ] **Step 12: Commit**

```bash
git add harness/runner.py tests/test_runner.py examples/agentclinic/specs/orchestrator.md ROADMAP.md docs/superpowers/index.md
git commit -m "feat(phase3-cycle2): delegate to our own implementer

The shipped subagent extension is loaded by path alongside hello-world.ts,
and PI_CODING_AGENT_DIR points at a provisioned directory the child
inherits -- which both hides ambient extensions from the child and makes
our specialist discoverable from a disposable workspace.

run_batch refuses any delegation that was not single-mode. Parallel would
put several children on the single-threaded local model at once.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Done when

- A live run delegates to `implementer` and the delegation is visible in `read_telemetry(result.pi_stdout).delegations`
- The child cannot see ambient extensions: `PI_CODING_AGENT_DIR` points at the provisioned directory, whose `extensions/` is empty
- `implementer.md` pins `omlx/gemma-4-12B-it-MLX-8bit`, and a test says so
- `_extension_digest` hashes a directory tree, paths as well as contents; the shipped extension is recorded in `extension_digests` and the committed agent-directory skeleton in `agent_dir_digest`, so editing `implementer.md` refuses a checkpoint resume the way editing the task spec does
- `run_batch` refuses a run that delegated in any mode other than `single`
- The delegation's wire shape is documented from a real capture, with the cycle 3 consequence stated
- All four gates pass

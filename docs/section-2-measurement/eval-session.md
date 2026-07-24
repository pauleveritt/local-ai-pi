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

`prepare_workspace()` copies the example into a temp directory, stamps a
`pyproject.toml` with the dependencies from `tech-stack.md`, installs them,
and creates the pristine git commit:

```python
def prepare_workspace(app_dir):
    workspace = tempdir() / "workspace"

    # Copy app source, excluding venv and caches
    shutil.copytree(app_dir, workspace,
                    ignore=shutil.ignore_patterns(".venv", ".git", "__pycache__"))

    # Stamp pyproject.toml with pinned dependencies
    (workspace / "pyproject.toml").write_text("""\
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

    # Copy the hello-world extension so the workspace is self-contained
    shutil.copy2(repo_root / ".pi/extensions/hello-world.ts",
                 workspace / ".pi/extensions/hello-world.ts")

    # Install deps, init git, commit pristine baseline
    subprocess.run(["uv", "sync"], cwd=workspace)
    subprocess.run(["git", "init"], cwd=workspace)
    (workspace / ".gitignore").write_text(".venv/\n__pycache__/\n")
    subprocess.run(["git", "add", "-A"], cwd=workspace)
    subprocess.run(["git", "commit", "-m", "pristine"], cwd=workspace)

    return workspace, git("rev-parse HEAD")
```

```{note}
The `pyproject.toml` is *stamped*, not copied from the example. The example
has no `pyproject.toml` — it's a spec-only directory. The harness creates
one with the exact dependency versions the course uses.
```

### The .gitignore is written before the pristine commit

If `.venv/` were committed, `git diff` would show it as a changed directory
every time `uv sync` touches pip metadata. Writing `.gitignore` before the
commit keeps the venv out of the baseline.

### Running pi headless

`run_session()` spawns pi inside the workspace with isolation flags:

```python
pi_cmd = [
    "pi",
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
    phase_prompt,  # positional, no --
]
```

The `--no-*` flags strip global configuration. `--extension` whitelists only
the hello-world extension. `--approve` trusts the project-local extension in
headless mode. `--no-session` prevents Pi from writing its own session file;
the harness captures stdout as the sole artifact.

```{warning}
Use `stdin=subprocess.DEVNULL` when spawning the subprocess. Without it,
Pi hangs waiting for stdin EOF. This is a known footgun; see KICKOFF.md
for the full story.
```

### Startup-hang retry

Local models occasionally stall before producing any output — the server
accepts the request but nothing comes back. `run_session()` retries up to
three times on empty-stdout timeouts. A run that produced at least one
event before timing out is *not* retried — that is a real measurement.

### Capturing the change

After pi exits, `capture_diff()` runs two git commands:

- `git diff <pristine_hash>` — for tracked changes, including files the model
  may have committed via `git add` + `git commit`
- `git status --porcelain -uall -z` — for untracked files the model never staged

The union of both commands (minus harness scaffolding like `pyproject.toml`
and `.pytest_cache/`) is the model's change surface.

### The acceptance oracle

Finally, `uv run pytest -q` in the workspace. If the SLM wrote a working
FastAPI app, the smoke test passes. If it didn't — that's a data point.

```python
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
        return (self.outcome in ("exited", "exited-with-hang")
                and self.tests_pass
                and len(self.changed_files) > 0)
```

A run is "successful" when:
- It exited normally (no timeout) or completed its work but the process
  lifecycle misbehaved (`exited-with-hang` — the server hung or failed to exit
  cleanly after the agent finished its task). Treating exit hangs as failures
  would charge task-level metrics for server symptoms uncorrelated with the
  interventions under test.
- `pytest` passed
- The model actually wrote something (not a null-action run)

## What you built

`harness/session.py` — one call to `run_session()` provisions a workspace,
runs pi, captures the diff, runs pytest, and returns a `SessionResult`.
Every later chapter in this course uses this function.

In the next chapter you will run it 8 times and produce the smoking gun.

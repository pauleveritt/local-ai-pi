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
#
# .gitignore is deliberately NOT here (closes F3): it is written by
# prepare_workspace, but it is model-visible and model-editable inside the
# workspace, and a model editing it to hide a created file from `git status`
# is itself evidence, not scaffolding to filter out.
_HARNESS_FILES = frozenset({
    "pyproject.toml",   # stamped by prepare_workspace
})

# Prefixes for files the harness creates — excluded from capture_diff.
_HARNESS_PREFIXES = (".pi-eval-prompt-",)

# Build artifacts the harness's own tooling creates — never model edits.
# .venv/ matters here specifically because of --ignored (added for F3): it
# is gitignored, so before --ignored it was invisible to `git status -uall`
# regardless; --ignored surfaces it, and it holds thousands of pinned
# dependency files that would otherwise flood changed_files as noise. This
# does not reopen F3 -- grade_acceptance() never reads from a workspace's
# .venv/ at all (the grader is a separate directory built from an
# allowlist), so a model editing its own .venv/ only affects its own
# self-report test run, already documented as a signal, never the grade.
_EXCLUDE_PREFIXES = (".pytest_cache/", ".venv/")
_EXCLUDE_SUFFIXES = (".pyc", ".pyo")


def prepare_workspace(
    app_dir: str | Path, seed: str | Path | None = None
) -> tuple[Path, str]:
    """Copy app_dir into a disposable temp workspace, stamp a pyproject.toml
    with dependencies from tech-stack.md, install via uv sync, init a git repo,
    and commit everything as the pristine baseline.

    seed, when given, is a reference-solution directory (e.g.
    examples/reference/phase-1) overlaid into the workspace BEFORE the
    pristine commit — so a Phase N run starts from the completed prior-phase
    state and `changed_files` reflects only the model's Phase N work.
    See the oracle-repair plan, Amendment 1 (incremental start-state).

    Returns (workspace_path, pristine_commit_hash).
    """
    app_dir = Path(app_dir).resolve()
    # Resolve to collapse /var -> /private/var symlink on macOS so paths
    # reported by subprocesses match what we expect.
    workspace = (Path(tempfile.mkdtemp(prefix="pi-eval-")) / "workspace").resolve()

    # Ignore reference/ — it contains answer keys that must never leak
    # into a measurement workspace. Belt-and-suspenders: the directory was
    # moved outside examples/agentclinic/ for the same reason. See:
    # docs/section-2-measurement/research/2026-07-24-oracle-invalid-incident.md
    shutil.copytree(
        app_dir,
        workspace,
        ignore=shutil.ignore_patterns(".venv", ".git", "__pycache__", "reference"),
    )

    # Overlay the seed (prior-phase reference solution) before the stamp and
    # the pristine commit, per Amendment 1.
    if seed is not None:
        seed_dir = Path(seed).resolve()
        if not seed_dir.is_dir():
            raise FileNotFoundError(f"seed directory does not exist: {seed_dir}")
        for src in sorted(seed_dir.rglob("*")):
            if src.is_file():
                dest = workspace / src.relative_to(seed_dir)
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dest)

    # Stamp pyproject.toml with the dependencies from tech-stack.md.
    _stamp_pyproject(workspace)

    # Copy the hello-world extension so the workspace is self-contained.
    _copy_hello_world_extension(workspace)

    # Copy .pi/agents/ so the subagent extension can discover specialists.
    _copy_agents(workspace)

    # Copy prompts/ so --append-system-prompt paths resolve.
    _copy_prompts(workspace)

    # Install dependencies. No --frozen here — each workspace gets its own
    # resolution. The dep set is small (fastapi, uvicorn, pytest) and stable.
    subprocess.run(
        ["uv", "sync"],
        cwd=workspace,
        check=True,
        capture_output=True,
        text=True,
    )

    # Write .gitignore so .venv/ stays out of the pristine commit.
    (workspace / ".gitignore").write_text(".venv/\n__pycache__/\n")

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


def capture_diff(
    workspace: str | Path, pristine_hash: str, seed: str | Path | None = None,
) -> tuple[list[str], str]:
    """Return (changed_files, full_diff) for a workspace since its pristine commit.

    Uses `git diff <pristine_hash>` (for tracked changes, including files the
    model may have committed), `git status --porcelain -uall --ignored -z`
    (for untracked files the model never staged, INCLUDING ones a model hid
    via .gitignore — closes F3: `-uall` alone still omits ignored paths), and,
    when `seed` is given, a hash comparison of every seeded file against its
    reference source (closes F3's second half — detects preservation
    breakage independent of git, so it still fires even against a workspace
    where git itself has been tampered with). Unions all three.
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

    # git status for untracked files, including gitignored ones.
    status_proc = subprocess.run(
        ["git", "status", "--porcelain", "-uall", "--ignored", "-z"],
        cwd=workspace, capture_output=True, text=True, check=True,
    )
    status_files: list[str] = []
    for record in status_proc.stdout.split("\0"):
        if not record:
            continue
        path = record[3:]  # XY PATH format
        status_files.append(path)

    seed_mismatches = _seed_mismatches(workspace, seed) if seed is not None else []

    # Union tracked + untracked + seed-hash mismatches, deduplicate, exclude
    # harness scaffolding.
    all_files = list(dict.fromkeys(diff_files + status_files + seed_mismatches))
    changed_files = [
        f for f in all_files
        if not _is_harness_file(f)
    ]

    return changed_files, diff_text


def _seed_mismatches(workspace: Path, seed: str | Path) -> list[str]:
    """Relative paths of seeded files whose content in `workspace` no longer
    hashes the same as the reference source in `seed` -- detected by direct
    comparison, not by trusting the workspace's own git history."""
    import hashlib

    seed_dir = Path(seed).resolve()
    mismatches: list[str] = []
    for src in seed_dir.rglob("*"):
        if not src.is_file():
            continue
        rel = str(src.relative_to(seed_dir))
        dest = workspace / rel
        if not dest.is_file():
            mismatches.append(rel)
            continue
        if hashlib.sha256(src.read_bytes()).digest() != hashlib.sha256(dest.read_bytes()).digest():
            mismatches.append(rel)
    return mismatches


def _stamp_pyproject_text() -> str:
    """The canonical workspace pyproject.toml. Shared with session.py, which
    re-stamps it before the acceptance run so a model edit cannot steer
    grading (pyproject.toml is excluded from capture_diff, so such an edit
    would otherwise be invisible)."""
    return """\
[project]
name = "agentclinic"
version = "0.1.0"
requires-python = ">=3.14,<3.15"
dependencies = [
    "fastapi[standard]==0.115.10",
    "uvicorn==0.51.0",
    "pytest==8.3.4",
]

[tool.pytest.ini_options]
pythonpath = ["."]
"""


def _stamp_pyproject(workspace: Path) -> None:
    """Write a pyproject.toml with the AgentClinic dependencies into workspace."""
    pyproject = workspace / "pyproject.toml"
    # This pythonpath line is load-bearing — without it, `uv run pytest`
    # cannot import `app` from `tests/` and the acceptance oracle fails
    # correct solutions. See:
    # docs/section-2-measurement/research/2026-07-24-oracle-invalid-incident.md
    pyproject.write_text(_stamp_pyproject_text())


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


def _copy_agents(workspace: Path) -> None:
    """Copy .pi/agents/ specialist files into the workspace so the subagent
    extension's discoverAgents can find them (it walks up from CWD)."""
    repo_root = Path(__file__).resolve().parent.parent
    src = repo_root / ".pi" / "agents"
    if not src.exists() or not any(src.iterdir()):
        return
    dest = workspace / ".pi" / "agents"
    dest.mkdir(parents=True, exist_ok=True)
    for f in src.iterdir():
        if f.is_file():
            shutil.copy2(f, dest / f.name)


def _copy_prompts(workspace: Path) -> None:
    """Copy prompts/ directory into the workspace so --append-system-prompt
    paths resolve relative to CWD."""
    repo_root = Path(__file__).resolve().parent.parent
    src = repo_root / "prompts"
    if not src.exists() or not any(src.iterdir()):
        return
    dest = workspace / "prompts"
    dest.mkdir(parents=True, exist_ok=True)
    for f in src.iterdir():
        if f.is_file():
            shutil.copy2(f, dest / f.name)


def _is_harness_file(path: str) -> bool:
    """True if this path is harness scaffolding, not a model edit."""
    basename = path.split("/")[-1] if "/" in path else path
    if basename in _HARNESS_FILES:
        return True
    if path.startswith(_HARNESS_PREFIXES):
        return True
    if path.startswith(_EXCLUDE_PREFIXES):
        return True
    if path.endswith(_EXCLUDE_SUFFIXES):
        return True
    # Path-segment match, not substring (Rule 8 review, 2026-07-26 -- Fable):
    # "__pycache__" in path would also match a model's own
    # my__pycache__helper.py, silently dropping a real model file from
    # changed_files -- the exact evidence-hiding F3 exists to close.
    if "__pycache__" in path.split("/"):
        return True
    return False


def seed_for_phase(phase: int) -> Path | None:
    """The canonical start-state seed for a phase-N run (Amendment 1).

    Phase 1 starts empty; phase N >= 2 starts from the cumulative reference
    solution of phase N-1 (examples/reference/phase-<N-1>). Raises if the
    required fixture does not exist yet — a phase must not be measured
    against a missing start state.
    """
    if phase <= 1:
        return None
    repo_root = Path(__file__).resolve().parent.parent
    seed = repo_root / "examples" / "reference" / f"phase-{phase - 1}"
    if not seed.is_dir():
        raise FileNotFoundError(
            f"No reference fixture for phase {phase - 1} at {seed} — "
            f"author it before measuring phase {phase} (oracle-repair plan, Amendment 1)."
        )
    return seed


def acceptance_suite_for_phase(phase: int) -> Path:
    """The harness-owned acceptance suite for a phase (Amendment 3).

    This is the grade: overlaid into the workspace after the model finishes,
    so the model cannot edit what judges it. Human-authored by design.
    Raises if the suite is missing — a phase must never be measured against
    an oracle that does not exist.
    """
    repo_root = Path(__file__).resolve().parent.parent
    suite = repo_root / "examples" / "acceptance" / f"phase-{phase}" / "test_acceptance.py"
    if not suite.is_file():
        raise FileNotFoundError(
            f"No acceptance suite for phase {phase} at {suite} — "
            f"author it before measuring (oracle-repair plan, Amendment 3)."
        )
    return suite

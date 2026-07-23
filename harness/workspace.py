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
    ".gitignore",        # written by prepare_workspace
})

# Prefixes for files the harness creates — excluded from capture_diff.
_HARNESS_PREFIXES = (".pi-eval-prompt-",)

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
    if "__pycache__" in path:
        return True
    return False

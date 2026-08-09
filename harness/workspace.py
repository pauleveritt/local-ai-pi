import os
import shutil
import subprocess
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

GIT_ENV = {
    "PATH": os.defpath,
    "GIT_AUTHOR_NAME": "satyrn-engine",
    "GIT_AUTHOR_EMAIL": "satyrn-engine@localhost",
    "GIT_COMMITTER_NAME": "satyrn-engine",
    "GIT_COMMITTER_EMAIL": "satyrn-engine@localhost",
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_TERMINAL_PROMPT": "0",
}


@contextmanager
def disposable_dir(prefix: str) -> Iterator[Path]:
    """Yield a fresh temp directory, removed on exit including on exception."""
    workspace = Path(tempfile.mkdtemp(prefix=prefix))
    try:
        yield workspace
    finally:
        shutil.rmtree(workspace, ignore_errors=True)


def git_init_commit(workspace: Path, message: str) -> None:
    """Turn a populated directory into a git repo with exactly one commit.

    Hermetic by construction: `GIT_ENV` disables global and system
    config, and `core.hooksPath` is pointed at the null device, so a
    developer's own hooks and identity cannot reach in and change what a
    workspace looks like.

    The `.git/info/exclude` entries keep Python's runtime droppings out
    of `git status`. That matters more than tidiness: a later cycle
    diffs a workspace to decide what a model changed, and a stray
    `__pycache__` would read as candidate output.
    """
    subprocess.run(
        ["git", "init", "-q"],
        cwd=workspace,
        check=True,
        capture_output=True,
        env=GIT_ENV,
    )
    subprocess.run(
        ["git", "add", "-A"],
        cwd=workspace,
        check=True,
        capture_output=True,
        env=GIT_ENV,
    )
    subprocess.run(
        [
            "git",
            "-c",
            f"core.hooksPath={os.devnull}",
            "commit",
            "-q",
            "--no-gpg-sign",
            "--allow-empty",
            "-m",
            message,
        ],
        cwd=workspace,
        check=True,
        capture_output=True,
        env=GIT_ENV,
    )
    (workspace / ".git" / "info" / "exclude").write_text(
        "# Satyrn harness runtime artifacts\n__pycache__/\n*.pyc\n.pytest_cache/\n"
    )


@contextmanager
def prepare_workspace(source_dir: Path | None = None) -> Iterator[Path]:
    """Copy source_dir, when supplied, into a fresh temp directory,
    git-init it with an initial commit, and yield the workspace path.

    Passing no source directory creates a literally empty workspace. The
    workspace is removed on exit.
    """
    with disposable_dir("satyrn-workspace-") as workspace:
        if source_dir is not None:
            shutil.copytree(
                source_dir,
                workspace,
                dirs_exist_ok=True,
                ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"),
            )
        git_init_commit(workspace, "initial workspace state")
        yield workspace

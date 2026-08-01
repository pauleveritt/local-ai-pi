import os
import shutil
import subprocess
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

_GIT_ENV = {
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
def prepare_workspace(source_dir: Path | None = None) -> Iterator[Path]:
    """Copy source_dir, when supplied, into a fresh temp directory,
    git-init it with an initial commit, and yield the workspace path.

    Passing no source directory creates a literally empty workspace. The
    workspace is removed on exit.
    """
    workspace = Path(tempfile.mkdtemp(prefix="satyrn-workspace-"))
    try:
        if source_dir is not None:
            shutil.copytree(
                source_dir,
                workspace,
                dirs_exist_ok=True,
                ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"),
            )
        subprocess.run(
            ["git", "init", "-q"],
            cwd=workspace,
            check=True,
            capture_output=True,
            env=_GIT_ENV,
        )
        subprocess.run(
            ["git", "add", "-A"],
            cwd=workspace,
            check=True,
            capture_output=True,
            env=_GIT_ENV,
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
                "initial workspace state",
            ],
            cwd=workspace,
            check=True,
            capture_output=True,
            env=_GIT_ENV,
        )
        yield workspace
    finally:
        shutil.rmtree(workspace, ignore_errors=True)

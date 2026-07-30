import os
import shutil
import subprocess
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

_GIT_ENV = {
    **os.environ,
    "GIT_AUTHOR_NAME": "satyrn-engine",
    "GIT_AUTHOR_EMAIL": "satyrn-engine@localhost",
    "GIT_COMMITTER_NAME": "satyrn-engine",
    "GIT_COMMITTER_EMAIL": "satyrn-engine@localhost",
}


@contextmanager
def prepare_workspace(source_dir: Path) -> Iterator[Path]:
    """Copy source_dir into a fresh temp directory, git-init it with an
    initial commit of the copied state, and yield the workspace path.

    The workspace is removed on exit.
    """
    workspace = Path(tempfile.mkdtemp(prefix="satyrn-workspace-"))
    try:
        shutil.copytree(
            source_dir,
            workspace,
            dirs_exist_ok=True,
            ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"),
        )
        subprocess.run(
            ["git", "init", "-q"], cwd=workspace, check=True, capture_output=True
        )
        subprocess.run(
            ["git", "add", "-A"], cwd=workspace, check=True, capture_output=True
        )
        subprocess.run(
            ["git", "commit", "-q", "--no-gpg-sign", "-m", "initial workspace state"],
            cwd=workspace,
            check=True,
            capture_output=True,
            env=_GIT_ENV,
        )
        yield workspace
    finally:
        shutil.rmtree(workspace, ignore_errors=True)

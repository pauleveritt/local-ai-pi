import shutil
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def prepare_workspace(source_dir: Path) -> Iterator[Path]:
    """Copy source_dir into a fresh temp directory and yield the path.

    The workspace is removed on exit.
    """
    workspace = Path(tempfile.mkdtemp(prefix="satyrn-workspace-"))
    try:
        shutil.copytree(source_dir, workspace, dirs_exist_ok=True)
        yield workspace
    finally:
        shutil.rmtree(workspace, ignore_errors=True)

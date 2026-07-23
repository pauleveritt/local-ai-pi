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


def test_prepare_workspace_excludes_venv_from_git(app_source: Path):
    ws_path, _ = prepare_workspace(app_source)
    try:
        # .venv/ exists (created by uv sync) but should NOT be in git
        assert (ws_path / ".venv").exists()
        result = subprocess.run(
            ["git", "ls-files", "--", ".venv"],
            cwd=ws_path, capture_output=True, text=True,
        )
        assert result.stdout.strip() == "", " .venv should not be git-tracked"
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

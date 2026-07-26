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


def test_capture_diff_does_not_hide_model_file_named_like_pycache(app_source: Path):
    """Rule 8 review, 2026-07-26 (Fable): '__pycache__' in path was a
    substring match, so a model's own my__pycache__helper.py was silently
    dropped from changed_files -- exactly the evidence-hiding F3 exists to
    close. Must be a path-segment match instead."""
    ws_path, pristine_hash = prepare_workspace(app_source)
    try:
        (ws_path / "my__pycache__helper.py").write_text("# real model file\n")
        changed_files, _ = capture_diff(ws_path, pristine_hash)
        assert "my__pycache__helper.py" in changed_files
    finally:
        import shutil
        shutil.rmtree(ws_path.parent, ignore_errors=True)


def test_capture_diff_detects_gitignore_hidden_file(app_source: Path):
    """F3, plan-mandated gate: a model can append its own created file to
    .gitignore to hide it from `git status`. Both the edited .gitignore
    (previously filtered as harness scaffolding) and the hidden file
    (previously invisible to `-uall` without `--ignored`) must surface."""
    ws_path, pristine_hash = prepare_workspace(app_source)
    try:
        gitignore = ws_path / ".gitignore"
        gitignore.write_text(gitignore.read_text() + "evil_module.py\n")
        (ws_path / "evil_module.py").write_text("# hidden from git status\n")

        changed_files, _ = capture_diff(ws_path, pristine_hash)

        assert ".gitignore" in changed_files
        assert "evil_module.py" in changed_files
    finally:
        import shutil
        shutil.rmtree(ws_path.parent, ignore_errors=True)


def test_capture_diff_detects_seed_hash_mismatch_independent_of_git(app_source: Path, tmp_path: Path):
    """F3, second half: a seeded file's content is hash-compared against its
    reference source, independent of git. `git update-index --skip-worktree`
    genuinely hides a real content change from both `git diff <pristine>`
    and `git status` (verified directly) -- a model could use this to
    silently break preservation while git reports a clean, unchanged file.
    The hash comparison must still catch it."""
    seed_dir = tmp_path / "seed"
    seed_dir.mkdir()
    (seed_dir / "app.py").write_text("# reference app\n")

    ws_path, pristine_hash = prepare_workspace(app_source, seed=seed_dir)
    try:
        subprocess.run(
            ["git", "update-index", "--skip-worktree", "app.py"],
            cwd=ws_path, check=True,
        )
        (ws_path / "app.py").write_text("# tampered\n")

        # Confirm git itself is fooled -- otherwise this test proves nothing.
        git_changed, git_diff_text = capture_diff(ws_path, pristine_hash)
        assert "app.py" not in git_changed, "git was not actually fooled -- test premise is stale"
        assert git_diff_text == ""

        changed_files, _ = capture_diff(ws_path, pristine_hash, seed=seed_dir)

        assert "app.py" in changed_files
    finally:
        import shutil
        shutil.rmtree(ws_path.parent, ignore_errors=True)

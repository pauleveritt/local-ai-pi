import shutil
import subprocess
import sys
from pathlib import Path

import pytest

import harness.workspace as workspace_module
from harness.workspace import prepare_workspace

REPO_ROOT = Path(__file__).resolve().parents[1]
PHASE_1 = REPO_ROOT / "examples" / "agentclinic" / "phase-1"


def test_prepare_workspace_copies_files_into_a_new_directory(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "app.py").write_text("x = 1\n")

    with prepare_workspace(source) as workspace:
        assert workspace != source
        assert (workspace / "app.py").read_text() == "x = 1\n"


def test_prepare_workspace_cleans_up_on_exit(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "app.py").write_text("x = 1\n")

    with prepare_workspace(source) as workspace:
        created = workspace

    assert not created.exists()


def test_prepare_workspace_cleans_up_when_the_body_raises(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "app.py").write_text("x = 1\n")

    leaked = None
    with pytest.raises(RuntimeError), prepare_workspace(source) as workspace:
        leaked = workspace
        raise RuntimeError("boom")

    assert not leaked.exists()


def test_prepare_workspace_git_inits_with_a_commit(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "app.py").write_text("x = 1\n")

    with prepare_workspace(source) as workspace:
        assert (workspace / ".git").is_dir()
        log = subprocess.run(
            ["git", "log", "--oneline"],
            cwd=workspace,
            check=True,
            capture_output=True,
            text=True,
        )
        assert log.stdout.strip() != ""


def test_prepare_workspace_accepts_the_reference_solution():
    with prepare_workspace(PHASE_1 / "reference") as workspace:
        shutil.copy(
            PHASE_1 / "acceptance" / "test_acceptance.py",
            workspace / "test_acceptance.py",
        )
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "-q"],
            cwd=workspace,
            capture_output=True,
            text=True,
        )

    assert result.returncode == 0
    assert "4 passed" in result.stdout


def test_prepare_workspace_rejects_the_broken_solution():
    with prepare_workspace(PHASE_1 / "broken") as workspace:
        shutil.copy(
            PHASE_1 / "acceptance" / "test_acceptance.py",
            workspace / "test_acceptance.py",
        )
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "-q"],
            cwd=workspace,
            capture_output=True,
            text=True,
        )

    assert result.returncode != 0
    assert "4 failed" in result.stdout
    assert "assert 404 == 200" in result.stdout


def test_prepare_workspace_provisions_the_empty_fixture():
    with prepare_workspace(PHASE_1 / "empty") as workspace:
        log = subprocess.run(
            ["git", "log", "--oneline"],
            cwd=workspace,
            check=True,
            capture_output=True,
            text=True,
        )
        assert log.stdout.strip() != ""


def test_prepare_workspace_commits_a_literally_empty_source(tmp_path):
    source = tmp_path / "empty-source"
    source.mkdir()

    with prepare_workspace(source) as workspace:
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=workspace,
            check=True,
            capture_output=True,
            text=True,
        )
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=workspace,
            check=True,
            capture_output=True,
            text=True,
        )

        assert head.stdout.strip()
        assert status.stdout == ""
        assert [path.name for path in workspace.iterdir()] == [".git"]


def test_prepare_workspace_can_create_an_empty_workspace_without_a_fixture():
    with prepare_workspace() as workspace:
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=workspace,
            check=True,
            capture_output=True,
            text=True,
        )

        assert head.stdout.strip()
        assert [path.name for path in workspace.iterdir()] == [".git"]


def test_prepare_workspace_disables_a_global_pre_commit_hook(tmp_path, monkeypatch):
    source = tmp_path / "source"
    source.mkdir()
    (source / "app.py").write_text("x = 1\n")
    hooks = tmp_path / "hooks"
    hooks.mkdir()
    pre_commit = hooks / "pre-commit"
    pre_commit.write_text("#!/bin/sh\nexit 1\n")
    pre_commit.chmod(0o755)
    global_config = tmp_path / "global.gitconfig"
    subprocess.run(
        ["git", "config", "--file", str(global_config), "core.hooksPath", str(hooks)],
        check=True,
    )
    monkeypatch.setitem(
        workspace_module._GIT_ENV, "GIT_CONFIG_GLOBAL", str(global_config)
    )

    with prepare_workspace(source) as workspace:
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=workspace,
            check=True,
            capture_output=True,
            text=True,
        )

    assert head.stdout.strip()

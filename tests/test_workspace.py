import shutil
import subprocess
import sys
from pathlib import Path

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

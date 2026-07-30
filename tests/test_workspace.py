import subprocess

from harness.workspace import prepare_workspace


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

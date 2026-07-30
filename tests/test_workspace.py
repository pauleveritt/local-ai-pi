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

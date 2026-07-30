"""Refusal of model-written config: the grader declining to certify a run
at all, as distinct from rejecting a solution that failed the suite."""
from pathlib import Path

from harness.grading import _refused_config


def test_refused_config_finds_a_root_level_pytest_ini(tmp_path):
    (tmp_path / "app.py").write_text("x = 1\n")
    (tmp_path / "pytest.ini").write_text("[pytest]\n")

    assert _refused_config(tmp_path) == ("pytest.ini",)


def test_refused_config_finds_a_nested_conftest(tmp_path):
    (tmp_path / "app.py").write_text("x = 1\n")
    nested = tmp_path / "sub"
    nested.mkdir()
    (nested / "conftest.py").write_text("")

    assert _refused_config(tmp_path) == ("sub/conftest.py",)


def test_refused_config_ignores_a_nested_pytest_ini(tmp_path):
    """A nested pytest.ini is inert -- pytest reads ini files at the
    rootdir -- so refusing it would refuse a file that cannot act."""
    (tmp_path / "app.py").write_text("x = 1\n")
    nested = tmp_path / "sub"
    nested.mkdir()
    (nested / "pytest.ini").write_text("[pytest]\n")

    assert _refused_config(tmp_path) == ()


def test_refused_config_is_empty_for_a_clean_workspace(tmp_path):
    (tmp_path / "app.py").write_text("x = 1\n")

    assert _refused_config(tmp_path) == ()


def test_refused_config_finds_every_root_level_name(tmp_path):
    for name in (
        "pyproject.toml", "pytest.ini", "tox.ini",
        "setup.cfg", "conftest.py", "sitecustomize.py",
    ):
        (tmp_path / name).write_text("")

    assert _refused_config(tmp_path) == (
        "conftest.py", "pyproject.toml", "pytest.ini",
        "setup.cfg", "sitecustomize.py", "tox.ini",
    )

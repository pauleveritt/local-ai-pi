"""Refusal of model-written config: the grader declining to certify a run
at all, as distinct from rejecting a solution that failed the suite."""
from pathlib import Path

from harness.grading import _refused_config, grade
from harness.workspace import prepare_workspace
from tests.test_subversion import (
    _attack_with_collect_only,
    _attack_with_exit_at_import,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
PHASE_1 = REPO_ROOT / "examples" / "agentclinic" / "phase-1"
SUITE = PHASE_1 / "acceptance" / "test_acceptance.py"


def test_refused_config_finds_a_root_level_pytest_ini(tmp_path):
    (tmp_path / "app.py").write_text("x = 1\n")
    (tmp_path / "pytest.ini").write_text("[pytest]\n")

    assert _refused_config(tmp_path) == ("pytest.ini",)


def test_refused_config_finds_a_root_level_dot_pytest_ini(tmp_path):
    (tmp_path / "app.py").write_text("x = 1\n")
    (tmp_path / ".pytest.ini").write_text("[pytest]\n")

    assert _refused_config(tmp_path) == (".pytest.ini",)


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
        "pyproject.toml", "pytest.ini", ".pytest.ini", "tox.ini",
        "setup.cfg", "conftest.py", "sitecustomize.py",
    ):
        (tmp_path / name).write_text("")

    assert _refused_config(tmp_path) == (
        ".pytest.ini", "conftest.py", "pyproject.toml", "pytest.ini",
        "setup.cfg", "sitecustomize.py", "tox.ini",
    )


def test_grade_refuses_a_workspace_carrying_config_without_running_pytest(tmp_path):
    """The returncode is the load-bearing assertion: None proves no
    process ran, which is the entire point of refusing early. `accepted`
    proves nothing here -- cycle 3 already rejects this attack."""
    with prepare_workspace(_attack_with_collect_only(tmp_path)) as workspace:
        result = grade(workspace, SUITE)

    assert result.refused_config == ("pytest.ini",)
    assert result.returncode is None
    assert result.accepted is False


def test_grade_does_not_refuse_the_clean_reference_solution():
    """Control: proves refused_config is not simply always populated."""
    with prepare_workspace(PHASE_1 / "reference") as workspace:
        result = grade(workspace, SUITE)

    assert result.refused_config == ()
    assert result.accepted is True


def test_grade_does_not_refuse_an_attack_that_writes_no_config(tmp_path):
    """Control: proves refusal is specific, not blanket. This attack
    carries no config file, so it must still be caught by cycle 3's
    completion-marker logic rather than by refusal."""
    with prepare_workspace(_attack_with_exit_at_import(tmp_path)) as workspace:
        result = grade(workspace, SUITE)

    assert result.refused_config == ()
    assert result.returncode == 0
    assert result.accepted is False

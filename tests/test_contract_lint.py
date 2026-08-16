"""harness/contract_lint.py: the one gate criterion that survived measurement.

Deterministic -- no model, no answer key, no network. The three cases
below are the ones the 2026-08-16 corpus sweep actually decided; the full
16-packet corpus stays on the `phase11-inspect-contract` branch.
"""

import pytest

from harness.contract_lint import ContractLintUnusable, impossible_paths


@pytest.fixture
def tree(tmp_path):
    (tmp_path / "src" / "svcs").mkdir(parents=True)
    (tmp_path / "src" / "svcs" / "_core.py").write_text("x = 1\n")
    (tmp_path / "src" / "svcs" / "flask.py").write_text("x = 1\n")
    return tmp_path


def test_a_path_in_the_tree_is_clean(tree):
    task = "Edit `src/svcs/_core.py` and rebind svc."
    assert impossible_paths(task, ["src/svcs/_core.py"], tree) == ()


def test_blocks_a_path_that_is_neither_in_the_tree_nor_writable(tree):
    # The real authored-draft defect: the tree has _core.py.
    task = "Add the guard to `src/svcs/container.py`."
    assert impossible_paths(task, ["src/svcs/_core.py"], tree) == (
        "src/svcs/container.py",
    )


def test_blocks_the_second_real_authored_defect(tree):
    # The tree has flask.py, not a flask/ package.
    task = "Register the extension in `src/svcs/flask/app.py`."
    assert impossible_paths(task, ["src/svcs/_core.py"], tree) == (
        "src/svcs/flask/app.py",
    )


def test_a_declared_new_file_is_allowed_because_creating_it_is_the_task(tree):
    # The committed `autowire` contract names a module that does not exist
    # yet. Judging absence alone would reject it.
    task = "Create `src/svcs/_autowire.py` with the autowire helpers."
    assert impossible_paths(task, ["src/svcs/_autowire.py"], tree) == ()


def test_reports_each_offending_path_once_in_order(tree):
    task = "Touch `src/svcs/a.py`, then `src/svcs/b.py`, then `src/svcs/a.py`."
    assert impossible_paths(task, ["src/svcs/_core.py"], tree) == (
        "src/svcs/a.py",
        "src/svcs/b.py",
    )


def test_bare_words_and_dotted_attributes_are_not_paths(tree):
    # Without the slash requirement this matches `aget`; without the
    # extension requirement it matches `app.router`.
    task = "Call `aget` and read `app.router.lifespan_context`."
    assert impossible_paths(task, ["src/svcs/_core.py"], tree) == ()


def test_refuses_to_judge_without_bounds(tree):
    with pytest.raises(ContractLintUnusable, match="writableFiles"):
        impossible_paths("Edit `src/svcs/x.py`.", [], tree)


def test_refuses_to_judge_without_a_tree(tmp_path):
    with pytest.raises(ContractLintUnusable, match="base tree"):
        impossible_paths("Body.", ["a/b.py"], tmp_path / "absent")

"""tools/deliver_candidate.py --contract: the product path into the implementer.

AC-1 is the point of this file: every refusal happens before a model call.
Asserting only on the exit code would pass even if the call had already
happened, so each refusal test asserts `run_process` was never invoked.
"""

import pytest

import tools.deliver_candidate as deliver_candidate

CONTRACT = """\
---
writableFiles: [src/svcs/_core.py]
validation: pytest -q
---
# Enter async context managers

Append `(name, svc)` to `self._on_close`, rebind `svc`.
"""


@pytest.fixture
def repo(tmp_path):
    (tmp_path / "src" / "svcs").mkdir(parents=True)
    (tmp_path / "src" / "svcs" / "_core.py").write_text("x = 1\n")
    return tmp_path


@pytest.fixture
def no_model(monkeypatch):
    """Fail loudly if anything reaches the model. AC-1's instrument."""
    calls = []

    def explode(*args, **kwargs):
        calls.append(args)
        raise AssertionError("a model call was made on a refusal path")

    monkeypatch.setattr(deliver_candidate, "run_process", explode)
    monkeypatch.setattr(
        deliver_candidate, "check_model_server_alive", lambda *a, **k: None
    )
    return calls


def _run(repo, contract_path):
    return deliver_candidate.main(
        [
            "--repo",
            str(repo),
            "--task",
            "t",
            "--contract",
            str(contract_path),
            "--model",
            "omlx/test",
            "--skip-server-check",
        ]
    )


def test_missing_contract_file_refuses_without_calling_the_model(
    repo, tmp_path, no_model, capsys
):
    assert _run(repo, tmp_path / "absent.md") == 2
    assert no_model == []
    assert "no contract file" in capsys.readouterr().err


def test_invalid_contract_refuses_without_calling_the_model(
    repo, tmp_path, no_model, capsys
):
    bad = tmp_path / "bad.md"
    bad.write_text("---\nvalidation: pytest -q\n---\nBody.\n")
    assert _run(repo, bad) == 2
    assert no_model == []
    assert "writableFiles" in capsys.readouterr().err


def test_a_path_that_cannot_exist_refuses_without_calling_the_model(
    repo, tmp_path, no_model, capsys
):
    bad = tmp_path / "bad.md"
    bad.write_text(
        "---\nwritableFiles: [src/svcs/_core.py]\nvalidation: pytest -q\n---\n"
        "Add the guard to `src/svcs/container.py`.\n"
    )
    assert _run(repo, bad) == 2
    assert no_model == []
    err = capsys.readouterr().err
    assert "src/svcs/container.py" in err


def test_an_unusable_lint_exits_4_not_2(repo, tmp_path, no_model, monkeypatch, capsys):
    def unusable(*args, **kwargs):
        raise deliver_candidate.ContractLintUnusable("bounds vanished")

    monkeypatch.setattr(deliver_candidate, "impossible_paths", unusable)
    good = tmp_path / "good.md"
    good.write_text(CONTRACT)
    assert _run(repo, good) == 4
    assert no_model == []
    assert "instrument" in capsys.readouterr().err.lower()


def test_prompt_file_is_gone(repo, tmp_path):
    with pytest.raises(SystemExit):
        deliver_candidate.main(
            [
                "--repo",
                str(repo),
                "--task",
                "t",
                "--prompt-file",
                str(tmp_path / "p.md"),
                "--model",
                "omlx/test",
            ]
        )


def test_a_contract_run_sets_the_child_env_and_selects_the_implementer(
    repo, tmp_path, monkeypatch
):
    """The two seams that reach the child: the env var and the extension."""
    good = tmp_path / "good.md"
    good.write_text(CONTRACT)
    seen = {}

    def fake_deliver(repo_arg, task, prompt, run_model, validation, **kwargs):
        seen["prompt"] = prompt
        seen["validation"] = validation
        seen["writable"] = kwargs.get("writable")
        raise deliver_candidate.DeliveryRefused("stop here, the wiring is what we test")

    monkeypatch.setattr(deliver_candidate, "deliver", fake_deliver)
    monkeypatch.setattr(
        deliver_candidate, "check_model_server_alive", lambda *a, **k: None
    )
    assert _run(repo, good) == 2
    assert "Append `(name, svc)`" in seen["prompt"]
    assert seen["validation"] == ("pytest", "-q")
    assert seen["writable"] == ("src/svcs/_core.py",)

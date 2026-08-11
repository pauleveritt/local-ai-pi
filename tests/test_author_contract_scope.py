"""The writable-scope line injected into the authoring prompt.

flask-extensions's contract told the executor to update a docs file the
task's own writable policy excludes, and a letter-perfect code fix was
rejected out-of-scope for it. This is the fix: the author is told the
real boundary instead of guessing at good practice.
"""

from tools.author_contract import compose_prompt


def test_scope_names_the_real_writable_paths() -> None:
    prompt = compose_prompt("INSTRUCTION", ("src/svcs/**",), "BRIEF")
    assert "src/svcs/**" in prompt
    assert "may only change files matching" in prompt


def test_scope_forbids_documentation_specifically() -> None:
    """The exact failure mode: a contract asking for a docs update."""
    prompt = compose_prompt("INSTRUCTION", ("src/svcs/flask.py",), "BRIEF")
    assert "not documentation" in prompt


def test_instruction_scope_and_brief_all_present_in_order() -> None:
    prompt = compose_prompt("INSTRUCTION", ("a/**",), "BRIEF")
    assert prompt.index("INSTRUCTION") < prompt.index("a/**") < prompt.index("BRIEF")


def test_multiple_writable_globs_all_named() -> None:
    prompt = compose_prompt("I", ("src/svcs/fastapi.py", "src/svcs/starlette.py"), "B")
    assert "src/svcs/fastapi.py" in prompt
    assert "src/svcs/starlette.py" in prompt

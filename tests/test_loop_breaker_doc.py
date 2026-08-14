"""The user-facing loop-breaker page must not drift from the extension.

Phase 5 cycle 12. This is the first document in the repository written for
someone outside the project, and it quotes the extension's constants and its
refusal text. Every other published table here has a recompute path; a page
that tells a stranger to set `THRESHOLD` has the same obligation, and the
usual failure is silent -- the source changes and the instructions keep
saying what used to be true.

The measured claims on that page (55 healthy runs, 239 of 261 calls, 12
refusals across two runs, both passing) come from the cycle 6 and cycle 10
records and recompute from the checkpoints named there. They are not pinned
here, because the checkpoints live outside version control and a test that
skips when they are missing would pin nothing.
"""

import re

from harness import runner

PAGE = runner.REPO_ROOT / "docs" / "engine" / "loop-breaker.md"


def _flat(text: str) -> str:
    """Collapse layout so comparisons are about content.

    The page hard-wraps prose and the extension builds its message by
    concatenating adjacent template literals, so every fragment worth
    checking spans a line break in one file or the other. Without this the
    tests fail on rewrapping, which trains people to loosen them.
    """
    joined = re.sub(r"`\s*\+\s*`", "", text)
    # Markdown blockquote markers sit at the start of every wrapped line of
    # the quoted refusal, so stripping them has to happen before the
    # whitespace collapse or they land in the middle of the sentence.
    unquoted = re.sub(r"(?m)^\s*>\s?", "", joined)
    return re.sub(r"\s+", " ", unquoted)


def _constant(name: str) -> int:
    source = runner.LOOP_BREAKER.read_text()
    match = re.search(rf"const {name} = (\d+);", source)
    assert match is not None, f"{name} not found in {runner.LOOP_BREAKER}"
    return int(match.group(1))


def test_the_page_states_the_defaults_the_extension_actually_uses():
    page = _flat(PAGE.read_text())
    window, threshold = _constant("WINDOW"), _constant("THRESHOLD")

    assert f"| `WINDOW` | {window} |" in page
    assert f"| `THRESHOLD` | {threshold} |" in page


def test_the_page_quotes_the_real_refusal_text():
    """The page shows the message a user's model will receive. Reworded
    steering in the extension must reach the page, because the whole point of
    quoting it is that a reader recognises it when they see it in a log.
    """
    source = _flat(runner.LOOP_BREAKER.read_text())
    page = _flat(PAGE.read_text())

    for fragment in (
        "You have already run this exact",
        "in a row and the result will not change. Do not repeat it.",
        "Use what you already know and take the next concrete action",
        "if you were looking for files and found none, create them.",
    ):
        assert fragment in source, fragment
        assert fragment in page, fragment


def test_the_page_tells_subagent_users_where_the_child_actually_looks():
    """The one thing a user cannot discover cheaply and this project paid a
    cycle to learn. If this paragraph is ever dropped, the page is worse than
    incomplete -- it recommends the project-scope install that silently fails
    to guard the process most likely to loop.
    """
    page = _flat(PAGE.read_text()).lower()

    assert "~/.pi/agent/extensions/" in page
    assert "the child does not load your project's extensions" in page

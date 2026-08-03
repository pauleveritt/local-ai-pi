"""Code quoted from files this project owns must match those files.

**What a green run does and does not mean.** It means every fenced block in
a checked document that was declared to come from one of this project's own
files appears verbatim in that file. It does NOT mean the document is
correct: quotations from the installed Pi package are deliberately not
checked here, because a test asserting on a third-party file's contents
would fail on any contributor whose Pi version differs, for a reason they
could not fix in this repository. Those claims are guarded only by the
version stated in the prose and by the read/run labels in the gotchas
record -- which is weaker, and is said here rather than implied.

Only chapters and research notes are checked -- specs and plans are
historical records that quote code as it was proposed, and gating them
would force rewriting history. A block is checked when the paragraph
introducing it names a repository path. That keeps the convention visible in the prose a reader sees, rather
than in a marker only the test knows about.
"""

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

# Only the living teaching documents. Specs and plans are historical
# records: they quote code as it was *proposed*, and a plan whose snippet
# no longer matches the file is accurate about what was planned, not
# wrong. Gating them would force either rewriting history or watering
# this check down to nothing.
CHECKED_DIRS = (
    REPO_ROOT / "docs" / "superpowers" / "chapters",
    REPO_ROOT / "docs" / "superpowers" / "research",
)

# A fenced block, plus the text just before it, so we can see which file
# the prose said it came from.
_BLOCK = re.compile(r"(?P<intro>[^\n]*)\n+```[a-z]*\n(?P<body>.*?)```", re.DOTALL)
# The character class excludes ":", so a citation written as a single
# backtick span with a trailing line number (e.g. `harness/runner.py:15`)
# never matches. That style is used elsewhere in this project's docs, and
# any fenced block introduced that way is silently unchecked by this test.
# Known and accepted: measured cost is zero blocks today. Do not widen the
# class to "fix" this without re-checking that cost.
_OWNED = re.compile(r"`((?:examples|harness|tests|\.pi)/[\w./-]+)`")


def quoted_blocks(text: str) -> list[tuple[str, str]]:
    """Return (repo_path, quoted_body) for blocks introduced by a repo path."""
    found = []
    for match in _BLOCK.finditer(text):
        owned = _OWNED.search(match.group("intro"))
        if owned:
            found.append((owned.group(1), match.group("body")))
    return found


def test_the_extractor_finds_a_block_introduced_by_a_repo_path():
    text = "See `harness/runner.py`:\n\n```python\nx = 1\n```\n"

    assert quoted_blocks(text) == [("harness/runner.py", "x = 1\n")]


def test_the_extractor_ignores_a_block_with_no_repo_path():
    text = "Some prose:\n\n```python\nx = 1\n```\n"

    assert quoted_blocks(text) == []


def _documents() -> list[Path]:
    return sorted(doc for directory in CHECKED_DIRS for doc in directory.glob("*.md"))


def _checkable() -> list[tuple[Path, str, str]]:
    cases = []
    for doc in _documents():
        for repo_path, body in quoted_blocks(doc.read_text()):
            source = REPO_ROOT / repo_path
            if source.is_file():
                cases.append((doc, repo_path, body))
    return cases


def test_at_least_five_blocks_are_checked():
    # Without this, a regression in the extractor would make every
    # parametrised case below vanish and the suite still pass -- the
    # failure mode tests/test_research_records.py guards the same way.
    assert len(_checkable()) >= 5


@pytest.mark.parametrize(
    ("doc", "repo_path", "body"),
    _checkable(),
    ids=lambda value: value.name if isinstance(value, Path) else "",
)
def test_a_quoted_block_matches_its_source(doc: Path, repo_path: str, body: str):
    source = (REPO_ROOT / repo_path).read_text()

    assert body.strip() in source, (
        f"{doc.name} quotes {repo_path}, but that text is not in the file"
    )

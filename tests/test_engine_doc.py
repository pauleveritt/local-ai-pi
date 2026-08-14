"""The README's engine section must not drift from the bundle.

Phase 9. The README tells a stranger to copy `.pi/extensions/engine.ts`
into user scope. The loop-breaker page has a drift test for the same
reason; the engine section is the front door for the same artifact plus
preserve-symbols. Constants and refusal text quoted in the README are
pinned here so the instructions cannot keep saying what used to be true.

The same holds for `docs/engine/index.md` — the page the README points at
for the detail. Anything it says about the artifact's constants or its
install destination is pinned to the artifact itself.
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
README = REPO_ROOT / "README.md"
ENGINE = REPO_ROOT / ".pi" / "extensions" / "engine.ts"
ENGINE_INDEX = REPO_ROOT / "docs" / "engine" / "index.md"


def _flat(text: str) -> str:
    return " ".join(text.split())


def test_the_engine_install_command_is_one_line():
    readme = _flat(README.read_text())
    command = "cp .pi/extensions/engine.ts ~/.pi/agent/extensions/"
    assert command in readme


def test_the_engine_artifact_exists():
    # Not vacuous: nothing else here imports the artifact, so without this
    # the file could vanish and the suite stay green.
    assert ENGINE.is_file()


def test_the_engine_section_points_at_docs_engine_index():
    readme = _flat(README.read_text())
    assert "docs/engine/index.md" in readme


def test_the_engine_index_exists_and_names_the_install_destination():
    # Not vacuous: nothing else here imports the page, so without this it
    # could vanish (or stop naming where the file goes) and stay green.
    index = ENGINE_INDEX.read_text()
    assert ENGINE_INDEX.is_file()
    # The artifact's own install comment says where; the page must agree.
    assert "~/.pi/agent/extensions/" in ENGINE.read_text()
    assert "~/.pi/agent/extensions/" in index


def test_quoted_engine_index_constants_match_the_artifact():
    source = ENGINE.read_text()
    index = ENGINE_INDEX.read_text()
    for name in ("WINDOW", "THRESHOLD"):
        match = re.search(rf"^export const {name} = (\d+)", source, re.MULTILINE)
        assert match, f"{name} missing from {ENGINE}"
        # Any index mention of the constant must carry the artifact's value.
        for mention in re.finditer(rf"{name}[^0-9]*(\d+)", index):
            assert mention.group(1) == match.group(1)


def test_quoted_loop_breaker_constants_match_the_artifact():
    source = ENGINE.read_text()
    readme = README.read_text()
    for name in ("WINDOW", "THRESHOLD"):
        match = re.search(rf"^export const {name} = (\d+)", source, re.MULTILINE)
        assert match, f"{name} missing from {ENGINE}"
        # Any README mention of the constant must carry the artifact's value.
        for mention in re.finditer(rf"{name}[^0-9]*(\d+)", readme):
            assert mention.group(1) == match.group(1)


def test_the_user_facing_vocabulary_is_the_new_one():
    # "Bounded executor" retired in Phase 10; the front door must not keep
    # naming the old product. The front you invoke is the orchestrator and
    # the bounded worker it drives is the implementer.
    readme = _flat(README.read_text())
    index = _flat(ENGINE_INDEX.read_text())
    for text in (readme, index):
        assert "bounded executor" not in text
        assert "orchestrator" in text
        assert "implementer" in text

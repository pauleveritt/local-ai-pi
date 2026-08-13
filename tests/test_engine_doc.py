"""The README's engine section must not drift from the bundle.

Phase 9. The README tells a stranger to copy `.pi/extensions/engine.ts`
into user scope. The loop-breaker page has a drift test for the same
reason; the engine section is the front door for the same artifact plus
preserve-symbols. Constants and refusal text quoted in the README are
pinned here so the instructions cannot keep saying what used to be true.
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
README = REPO_ROOT / "README.md"
ENGINE = REPO_ROOT / ".pi" / "extensions" / "engine.ts"


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


def test_quoted_loop_breaker_constants_match_the_artifact():
    source = ENGINE.read_text()
    readme = README.read_text()
    for name in ("WINDOW", "THRESHOLD"):
        match = re.search(rf"^export const {name} = (\d+)", source, re.MULTILINE)
        assert match, f"{name} missing from {ENGINE}"
        # Any README mention of the constant must carry the artifact's value.
        for mention in re.finditer(rf"{name}[^0-9]*(\d+)", readme):
            assert mention.group(1) == match.group(1)

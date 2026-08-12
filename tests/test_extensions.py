"""The teaching extensions load under the installed Pi.

This replaces a type-check. There is no `tsc` and no Node toolchain in this
Python repository, and getting one means either a network install per test
run or a `package.json` plus a TypeScript devDependency. Loading the
extension under Pi tests the real question -- does Pi accept this file --
rather than a proxy for it.

Live-gated: it needs the model server, because the only way to see a tool
actually register is to let a model call it.
"""

import json
import os
import subprocess
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
WORD_COUNT = REPO_ROOT / "examples" / "extensions" / "word-count.ts"


def test_the_teaching_extension_exists():
    # Not vacuous: the live test below skips without SATYRN_LIVE, so
    # without this the file could vanish and the suite stay green.
    assert WORD_COUNT.is_file()


@pytest.mark.skipif(
    os.environ.get("SATYRN_LIVE") != "1",
    reason="set SATYRN_LIVE=1 to require an actual Pi/model run",
)
def test_the_word_count_extension_registers_its_tool():
    command = [
        "pi",
        "--print",
        "--mode",
        "json",
        "--no-session",
        "--model",
        "omlx/gemma-4-12B-it-MLX-8bit",
        "--no-extensions",
        "--extension",
        str(WORD_COUNT),
        "--no-skills",
        "--no-prompt-templates",
        "--no-themes",
        "--no-context-files",
        "--approve",
        "Use the word_count tool on the text 'one two three'. "
        "Reply with only the number.",
    ]
    result = subprocess.run(
        command, cwd=tempfile.mkdtemp(), capture_output=True, text=True, timeout=300
    )

    assert "Extension error" not in result.stderr
    called = []
    for line in result.stdout.split("\n"):
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "tool_execution_end":
            called.append(event.get("toolName"))
    assert "word_count" in called

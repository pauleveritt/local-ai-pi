"""`resolve_cell` must describe the agent directory the run actually uses.

The bug this pins: `resolve_cell` hashed the repository's own
`pi-agent-dir/models.json` unconditionally, while
`deliver_candidate --agent-dir ...` runs Pi against the caller's
directory. The receipt then recorded `models_json_sha256`, `max_tokens`
and `base_url` from a file the run never read -- and `Cell.verify()`
compares against exactly those, so wrong provenance is worse than none.
"""

import json
from pathlib import Path

from harness.cell_resolution import resolve_cell


def _agent_dir(tmp_path: Path, name: str, max_tokens: int, base_url: str) -> Path:
    directory = tmp_path / name
    directory.mkdir()
    (directory / "models.json").write_text(
        json.dumps(
            {
                "providers": {
                    "omlx": {
                        "baseUrl": base_url,
                        "models": [
                            {"id": "m", "maxTokens": max_tokens, "contextWindow": 4096}
                        ],
                    }
                }
            }
        )
    )
    return directory


def test_the_recorded_models_json_is_the_one_the_run_will_read(tmp_path):
    theirs = _agent_dir(tmp_path, "theirs", 111, "http://theirs:1")
    cell = resolve_cell("omlx/m", "read", (), 1.0, agent_dir=theirs)

    assert cell["max_tokens"] == "111"
    assert cell["base_url"] == "http://theirs:1"


def test_two_different_agent_dirs_do_not_resolve_to_the_same_cell(tmp_path):
    # The actual failure mode: before the fix both calls returned the
    # repository default, so a contributor's run and a measured run were
    # indistinguishable in the record.
    a = _agent_dir(tmp_path, "a", 111, "http://a:1")
    b = _agent_dir(tmp_path, "b", 222, "http://b:2")

    first = resolve_cell("omlx/m", "read", (), 1.0, agent_dir=a)
    second = resolve_cell("omlx/m", "read", (), 1.0, agent_dir=b)

    assert first["models_json_sha256"] != second["models_json_sha256"]
    assert (first["max_tokens"], second["max_tokens"]) == ("111", "222")


def test_a_missing_models_json_is_recorded_as_absent_not_guessed(tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    cell = resolve_cell("omlx/m", "read", (), 1.0, agent_dir=empty)
    assert cell["models_json_sha256"] == "absent"
    assert "max_tokens" not in cell


def test_the_default_is_still_this_repositorys_agent_dir():
    # Measured runs pass nothing and must keep resolving the pinned dir.
    from harness.cell_resolution import AGENT_DIR

    assert (
        resolve_cell("omlx/x", "read", (), 1.0)["models_json_sha256"]
        == (
            resolve_cell("omlx/x", "read", (), 1.0, agent_dir=AGENT_DIR)[
                "models_json_sha256"
            ]
        )
    )

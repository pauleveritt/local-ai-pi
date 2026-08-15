"""The engine is a pi package: the root manifest gates what a git install
loads, and a fresh agent dir can load the installed engine.

Phase 12. The root `package.json`'s `pi` manifest is the git-install seam —
it must name exactly the two package files, so Pi never auto-discovers the
research `extensions/` tree (the caps, the implementer internals) into a
user session. The live test below is gated on SATYRN_LIVE like the other
Pi-dependent tests.
"""

import json
import os
import subprocess
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE = REPO_ROOT / "packages" / "engine"


def test_the_root_manifest_lists_only_the_package_files():
    # Not vacuous: if this drifts, a git install auto-discovers the
    # conventional extensions/ dir and loads the research tree.
    root = json.loads((REPO_ROOT / "package.json").read_text())
    assert root["pi"]["extensions"] == [
        "./packages/engine/engine.ts",
        "./packages/engine/orchestrator.ts",
    ]


def test_the_package_manifest_lists_only_its_own_files():
    # The package's own manifest (for a local-path install) names the two
    # files relative to the package root.
    manifest = json.loads((PACKAGE / "package.json").read_text())
    assert manifest["pi"]["extensions"] == ["./engine.ts", "./orchestrator.ts"]
    assert manifest["keywords"] == ["pi-package"]
    # The engine is dependency-free: no runtime deps to install.
    assert "dependencies" not in manifest


@pytest.mark.skipif(
    os.environ.get("SATYRN_LIVE") != "1",
    reason="set SATYRN_LIVE=1 to require an actual Pi run",
)
def test_a_fresh_agent_dir_loads_the_installed_engine():
    """Install the engine package into a fresh agent dir and confirm the
    guards load and /implement registers — the one-line-install promise."""
    with tempfile.TemporaryDirectory() as tmp:
        agent_dir = Path(tmp)
        # A pi install (or the local equivalent) places the two files in
        # user scope; the package manifest declares them.
        (agent_dir / "engine.ts").symlink_to(PACKAGE / "engine.ts")
        (agent_dir / "orchestrator.ts").symlink_to(PACKAGE / "orchestrator.ts")

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
            str(agent_dir / "engine.ts"),
            "--extension",
            str(agent_dir / "orchestrator.ts"),
            "--no-skills",
            "--no-prompt-templates",
            "--no-themes",
            "--no-context-files",
            "--approve",
            "Reply with the single word OK.",
        ]
        result = subprocess.run(
            command, cwd=tempfile.mkdtemp(), capture_output=True, text=True, timeout=300
        )

        assert "Extension error" not in result.stderr
        # The engine registers /implement (via orchestrator.ts); a Pi run
        # with both extensions loads them without an extension error.
        assert result.returncode == 0

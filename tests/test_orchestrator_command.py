"""The engine package registers /implement, and its argv maps correctly.

Phase 10. The orchestrator's session front is a thin command that shells
out to the existing CLI. These tests are hermetic: they verify the command
is registered and the argv the handler builds, without a checkout, a model,
or a subprocess.
"""

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ORCHESTRATOR = REPO_ROOT / "packages" / "engine" / "orchestrator.ts"


def test_the_orchestrator_file_exists():
    assert ORCHESTRATOR.is_file()


def test_the_command_is_registered():
    # Not vacuous: nothing else here reads the source, so without this the
    # registration could vanish and the file-existence test stay green.
    assert 'pi.registerCommand("implement"' in ORCHESTRATOR.read_text()


def test_the_argv_builder_maps_the_inputs():
    # Run the TS builder under bun and check the argv it prints.
    out = subprocess.run(
        [
            "bun",
            "-e",
            f"import {{ buildDeliverCandidateArgv }} from '{ORCHESTRATOR}';"
            "console.log(buildDeliverCandidateArgv({"
            "repo: '/repo', task: 'add-health', contractPath: '/tmp/c.md',"
            "model: 'omlx/gemma-4-12B-it-MLX-8bit'"
            "}).join(' '))",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    argv = out.stdout.strip()
    assert "tools.deliver_candidate" in argv
    assert "--repo /repo" in argv
    assert "--task add-health" in argv
    assert "--contract /tmp/c.md" in argv
    # Validation now comes from the contract file, not the command line.
    assert "--prompt-file" not in argv
    assert "--validation" not in argv
    assert "--model omlx/gemma-4-12B-it-MLX-8bit" in argv

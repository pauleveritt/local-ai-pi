"""Resolve an attempt's live configuration into a recorded cell.

Extracted from `harness/screen.py` (2026-08-12) for the same reason
`harness/pi_invocation.py` was: the candidate-delivery product path
(`tools/deliver_candidate.py`) needs `resolve_cell` and `PROBE_EXTENSION`
and nothing else from that 1,000-line mechanism-screen module, but
importing them dragged the whole screening apparatus -- and its own
`harness.similarity` / `harness.validity` dependencies -- into the
product's import closure. That blocked separating the screening
laboratory from the shipped path.

`screen.py` imports these back rather than redefining them, so the
screen's own recorded cells stay byte-identical to the product's.
"""

import hashlib
import json
import subprocess
from pathlib import Path

from harness.pi_invocation import pi_env
from harness.workload import sha256_file

PROBE_EXTENSION = Path(__file__).resolve().parents[1] / "extensions" / "probe-cap.ts"
"""Loose budgets for a headroom probe, which is not the same thing as an arm.

The envelope's 16 turns and 30 tool calls mirror the engine's implementer
child and were calibrated for `read,write` with no way to execute anything.
Once the executor has a working environment it has more useful work to do
per task, and the budget did not move with it: on `registry-iter` -- the
declared floor -- the model closed the whole gap, ran the suite, found a
doctest it had just broken, and hit the ceiling before it could repair it.
A probe whose budget truncates repair manufactures the false floor it exists
to rule out.
"""


def resolve_cell(
    model: str, tools: str, extensions: tuple[Path, ...], timeout: float
) -> dict[str, str]:
    """Everything about this attempt that a later reader must not have to infer.

    Resolved by reading the actual configuration -- the model entry Pi
    will use, the extension bytes, the installed Pi version -- rather
    than by restating the flags. A restated flag agrees with the run by
    convention; a hash of the file disagrees loudly when someone edits
    it mid-sweep, which is exactly what happened when an output cap was
    swapped for one stage and restored afterwards.
    """
    # Order-sensitive on purpose: extensions load in sequence, and two
    # sets with the same members in a different order are not the same
    # arm.
    digests = ":".join(
        sha256_file(e) if e.is_file() else "absent" for e in extensions
    )
    cell: dict[str, str] = {
        "model": model,
        "tools": tools,
        "extensions": ",".join(e.name for e in extensions),
        "extensions_sha256": hashlib.sha256(digests.encode()).hexdigest(),
        "wall_clock_seconds": str(timeout),
    }
    try:
        version = subprocess.run(
            ["pi", "--version"], capture_output=True, text=True, timeout=30
        )
        cell["pi_version"] = version.stdout.strip() or version.stderr.strip()
    except Exception:
        cell["pi_version"] = "unknown"

    models_json = Path(pi_env(inherit_venv=True).get("PI_CODING_AGENT_DIR", "")) / "models.json"
    cell["models_json_sha256"] = (
        sha256_file(models_json) if models_json.is_file() else "absent"
    )
    # The resolved per-model limits, not the flag: `maxTokens` is the
    # value that silently made four of gemma's five failures look like
    # incapacity, and it appeared in no attempt record.
    if models_json.is_file():
        data = json.loads(models_json.read_text())
        wanted = model.split("/", 1)[-1]
        for provider in data.get("providers", {}).values():
            for entry in provider.get("models", []):
                if entry.get("id") == wanted:
                    cell["max_tokens"] = str(entry.get("maxTokens", "?"))
                    cell["context_window"] = str(entry.get("contextWindow", "?"))
                    cell["base_url"] = str(provider.get("baseUrl", "?"))
    return cell

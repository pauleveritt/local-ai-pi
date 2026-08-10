"""Experiment B: is magicmock-factory's failure the output cap?

At maxTokens 8192 this task went 1/6 accepted, 4/6 no-progress, 1/6
damaged, and every failure contained a `stopReason: length` turn. That
is the same mechanism the overnight run demonstrated on async-cm-enter:
a real answer, truncated before the model could act on it.

Prespecified before running: >=6/8 accepted confirms cap-runaway as the
mechanism (Fisher one-sided p ~ 0.01 against the 8192 baseline);
<=3/8 means the bimodality is intrinsic to the task, not the cap.

maxTokens is restored in `finally` from a saved copy, never via git --
this worktree carries uncommitted drift and a hard reset would take real
work with it. Same discipline as tools/overnight.py.
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

MODELS_JSON = Path("pi-agent-dir/models.json")
GEMMA = "gemma-4-12B-it-MLX-8bit"
OUT = Path("workloads/svcs/screen/variance-magicmock-32k")


def set_max_tokens(value: int) -> int:
    data = json.loads(MODELS_JSON.read_text())
    previous = None
    for provider in data["providers"].values():
        for model in provider["models"]:
            if model["id"] == GEMMA:
                previous = model["maxTokens"]
                model["maxTokens"] = value
    if previous is None:
        raise SystemExit(f"{GEMMA} not in {MODELS_JSON}")
    MODELS_JSON.write_text(json.dumps(data, indent=2) + "\n")
    json.loads(MODELS_JSON.read_text())
    return previous


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    backup = OUT / "models.json.before"
    shutil.copy2(MODELS_JSON, backup)
    previous = set_max_tokens(32768)
    print(f"maxTokens {previous} -> 32768", flush=True)
    try:
        return subprocess.run(
            [
                sys.executable, "-m", "tools.replicate",
                "--cohort", "workloads/svcs/cohort.toml",
                "--model", "omlx/gemma-4-12B-it-MLX-8bit",
                "--task", "magicmock-factory",
                "--replicates", "8",
                "--out", str(OUT),
            ]
        ).returncode
    finally:
        shutil.copy2(backup, MODELS_JSON)
        print("maxTokens restored to", previous, flush=True)


if __name__ == "__main__":
    sys.exit(main())

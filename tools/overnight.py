"""The unattended overnight run: author drafts, then three sweeps.

Nobody is watching. That changes what the code owes: every stage checks
the server before it spends anything, every stage writes what it did to
`MORNING.md` as it goes rather than at the end, and a stage that cannot
run is skipped with a reason instead of taking the rest of the night
down with it.

Stages, in order and strictly sequential:

  1  author 8 draft contracts with Qwen, read-only  (~70 min)
  2  Qwen, draft-contract arm, 8 tasks              (~90 min)
  3  gemma, draft-contract arm, at maxTokens 8192   (~60 min)
  4  gemma, brief-only, at maxTokens 32768          (~75 min)

Stage 3 keeps the measured cell's output cap so the contract is the only
variable against it. Stage 4 changes only the cap, so the cap is the only
variable -- four of gemma's five brief-only failures died at `length`
with an 8192 ceiling, one of them with the correct fix written out and
truncated mid-sentence, and until that is separated the 12B column is
not a capability measurement.

Between stages the temp directory is swept. A workspace left by a crash
is an answer key for every task whose base predates it, and cycle 1 lost
its ceiling task to exactly that. Deleting them is the validity-safe
direction and a single sequential driver cannot race itself.
"""

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from collections.abc import Sequence
from pathlib import Path

COHORT = "workloads/svcs/cohort.toml"
SERVER = "http://127.0.0.1:8001"
QWEN = "omlx/Qwen3.6-27B-8bit"
GEMMA = "omlx/gemma-4-12B-it-MLX-8bit"
MODELS_JSON = Path("pi-agent-dir/models.json")


def note(out_root: Path, text: str) -> None:
    """Append to MORNING.md now, not at the end.

    A driver that writes its report last has nothing to say about the
    failure that killed it.
    """
    path = out_root / "MORNING.md"
    with path.open("a") as handle:
        handle.write(text.rstrip() + "\n")
    print(text.rstrip(), flush=True)


def server_alive() -> bool:
    try:
        request = urllib.request.Request(
            f"{SERVER}/v1/models", headers={"Authorization": "Bearer not-needed"}
        )
        with urllib.request.urlopen(request, timeout=10) as response:
            json.loads(response.read())
        return True
    except Exception:
        return False


def sweep_temp() -> int:
    root = Path(tempfile.gettempdir())
    removed = 0
    for path in root.glob("satyrn-*"):
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
            removed += 1
    return removed


def run(command: list[str], log: Path) -> int:
    with log.open("a") as handle:
        return subprocess.run(command, stdout=handle, stderr=subprocess.STDOUT).returncode


def set_max_tokens(model_id: str, value: int) -> int:
    data = json.loads(MODELS_JSON.read_text())
    previous = None
    for provider in data["providers"].values():
        for model in provider["models"]:
            if model["id"] == model_id:
                previous = model["maxTokens"]
                model["maxTokens"] = value
    if previous is None:
        raise SystemExit(f"{model_id} not in {MODELS_JSON}")
    MODELS_JSON.write_text(json.dumps(data, indent=2) + "\n")
    json.loads(MODELS_JSON.read_text())
    return previous


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--tasks", type=Path, default=Path(COHORT))
    args = parser.parse_args(argv)
    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    log = out / "driver.log"

    # Restored from a saved copy in `finally`, never with git: this
    # worktree carries uncommitted drift and a hard reset here would take
    # real work with it.
    models_backup = out / "models.json.before"
    shutil.copy2(MODELS_JSON, models_backup)

    import harness.workload as workload

    cohort = workload.load_cohort(args.tasks, require_accounting=True)
    tasks = list(cohort.included)
    note(out, f"# Overnight run\n\nCohort: {len(tasks)} tasks\n")

    drafts = out / "drafts"
    started = time.monotonic()
    try:
        # ---- stage 1: authoring ------------------------------------
        if not server_alive():
            note(out, "STAGE 1 ABORTED: server not reachable. Nothing else ran.")
            return 1
        note(out, "## Stage 1 - authoring draft contracts (Qwen, read-only)\n")
        authored = []
        for task in tasks:
            existing = drafts / f"{task}.md"
            if existing.is_file() and existing.read_text().strip():
                authored.append(task)
                note(out, f"- {task}: draft already present, kept")
                continue
            code = run(
                [sys.executable, "-m", "tools.author_contract", "--task", task,
                 "--model", QWEN, "--out", str(drafts)],
                log,
            )
            if code == 0:
                authored.append(task)
            note(out, f"- {task}: {'authored' if code == 0 else 'FAILED'}")
        note(out, f"\n{len(authored)}/{len(tasks)} drafts.\n")

        # ---- stages 2 and 3: contract arms -------------------------
        if len(authored) < len(tasks):
            note(out, f"Contract arms need all {len(tasks)} drafts; have "
                      f"{len(authored)}. Skipping stages 2-3, running stage 4.\n")
        else:
            for label, model in (
                ("qwen27b-draft-contract", QWEN),
                # Deliberately at the measured cell's 8192 cap, so the
                # contract is the only variable against it.
                ("gemma12b-draft-contract", GEMMA),
            ):
                sweep_temp()
                if not server_alive():
                    note(out, f"STAGE {label} ABORTED: server unreachable.")
                    return 1
                note(out, f"## {label}\n")
                code = run(
                    [sys.executable, "-m", "tools.screen_workload",
                     "--cohort", COHORT, "--model", model, "--server", SERVER,
                     "--tools", "read,bash,edit,write", "--probe", "--timeout", "1800",
                     "--contract-draft-dir", str(drafts),
                     "--out", f"workloads/svcs/screen/{label}"],
                    log,
                )
                note(out, f"exit {code}\n")

        # ---- stage 4: the confound repair --------------------------
        sweep_temp()
        if not server_alive():
            note(out, "STAGE 4 ABORTED: server unreachable.")
            return 1
        previous = set_max_tokens("gemma-4-12B-it-MLX-8bit", 32768)
        note(out, f"## gemma12b-brief-32k (maxTokens {previous} -> 32768)\n")
        code = run(
            [sys.executable, "-m", "tools.screen_workload",
             "--cohort", COHORT, "--model", GEMMA, "--server", SERVER,
             "--tools", "read,bash,edit,write", "--probe", "--timeout", "1800",
             "--out", "workloads/svcs/screen/gemma12b-brief-32k"],
            log,
        )
        note(out, f"exit {code}\n")
        return 0
    finally:
        shutil.copy2(models_backup, MODELS_JSON)
        note(out, f"\nmodels.json restored. Elapsed {(time.monotonic()-started)/3600:.1f}h.")
        note(out, "\nMorning: audit authoring transcripts for firewall reaches, "
                  "run tools/audit_attempt.py on every new screen dir, then "
                  "tools/report_screen.py, then score against PREDICTIONS.")


if __name__ == "__main__":
    sys.exit(main())

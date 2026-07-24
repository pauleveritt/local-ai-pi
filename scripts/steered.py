"""Steered arm runner: SP2 profile, n=8, at the candidate ditch phase.

Arm A: untuned orchestrator prompt (from git commit 1b452e8, the pre-tuning
configuration). Arm B: current tuned orchestrator prompt.

Usage: python scripts/steered.py [phase] [--untuned | --tuned]
"""
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from harness.runner import run_baseline, write_report
from harness.workspace import seed_for_phase
from harness.session import InvocationProfile

ROADMAP = REPO_ROOT / "examples" / "agentclinic" / "specs" / "roadmap.md"
APP_SOURCE = REPO_ROOT / "examples" / "agentclinic"
MODEL = "omlx/gemma-4-12B-it-MLX-8bit"

# The shipped Pi subagent extension.
SUBTAGENT_PATH_FILE = REPO_ROOT / ".pi" / "subagent-extension-path.txt"
if SUBTAGENT_PATH_FILE.exists():
    SUBAGENT_PATH = SUBTAGENT_PATH_FILE.read_text().strip()
else:
    # Fallback — adjust to your install.
    SUBAGENT_PATH = "/Users/pauleveritt/.volta/tools/image/packages/@earendil-works/pi-coding-agent/lib/node_modules/@earendil-works/pi-coding-agent/examples/extensions/subagent/index.ts"

ORCHESTRATOR_PROMPT = REPO_ROOT / "prompts" / "orchestrator.md"
# Untuned prompt version (pre-tuning baseline).
UNTUNED_COMMIT = "1b452e8"


def extract_phase_prompt(phase: int) -> str:
    text = ROADMAP.read_text()
    pattern_start = f"## Phase {phase} "
    pattern_next = f"## Phase {phase + 1} "
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.startswith(pattern_start) and start is None:
            start = i
        elif start is not None and line.startswith(pattern_next):
            return "\n".join(lines[start:i]).strip()
    if start is not None:
        return "\n".join(lines[start:]).strip()
    raise ValueError(f"Phase {phase} not found in roadmap")


def run_steered(phase: int, untuned: bool = False):
    label = "untuned" if untuned else "tuned"
    print(f"Arm {'A (untuned)' if untuned else 'B (tuned)'}: Phase {phase}, SP2, n=8")
    print(f"Model: {MODEL}")
    print()

    research_dir = REPO_ROOT / "docs" / "section-3-sdd" / "research"
    research_dir.mkdir(parents=True, exist_ok=True)

    prompt = extract_phase_prompt(phase)

    # Self-heal: a killed prior run (SIGTERM skips finally) can leave the
    # prompt swapped to untuned. Always restore to HEAD before deciding.
    subprocess.run(
        ["git", "checkout", "--", str(ORCHESTRATOR_PROMPT)],
        cwd=REPO_ROOT, check=True, capture_output=True,
    )
    # For untuned arm, temporarily swap in the pre-tuning orchestrator prompt.
    saved = None
    if untuned:
        saved = ORCHESTRATOR_PROMPT.read_text()
        untuned_text = subprocess.run(
            ["git", "show", f"{UNTUNED_COMMIT}:prompts/orchestrator.md"],
            cwd=REPO_ROOT, capture_output=True, text=True, check=True,
        ).stdout
        ORCHESTRATOR_PROMPT.write_text(untuned_text)
        print("Swapped to untuned orchestrator (commit 1b452e8)")
        print()

    try:
        report = run_baseline(
            phase_prompt=prompt,
            app_source=APP_SOURCE,
            model=MODEL,
            profile=InvocationProfile.sp2(SUBAGENT_PATH),
            n=8,
            timeout=900,
            phase_name=f"Phase {phase} — {'Untuned' if untuned else 'Tuned'} SP2",
            seed=seed_for_phase(phase),
            research_dir=research_dir,
        )

        today = __import__("datetime").datetime.now().isoformat()[:10]
        output = research_dir / f"{today}-post-repair-sp2-phase{phase}-{label}.md"
        write_report(report, output)

        print()
        print(f"Report: {output}")
        print(f"Success: {report.success_count}/{report.n} ({report.success_rate:.0%})")
        hang_count = sum(1 for r in report.results if r.outcome == "exited-with-hang")
        if hang_count:
            print(f"Hang incidence: {hang_count}/{report.n}")
        if report.drift_count > 0:
            print(f"Drift incidence: {report.drift_count}/{report.n} "
                  f"(overreach={report.overreach_count}, "
                  f"validation-drift={report.validation_drift_count})")
        if report.mean_wall_time_s:
            print(f"Mean task duration: {report.mean_wall_time_s:.0f}s")
        if report.mean_turns:
            print(f"Mean turns: {report.mean_turns:.1f}")

    finally:
        if saved is not None:
            ORCHESTRATOR_PROMPT.write_text(saved)
            print()
            print("Restored tuned orchestrator prompt.")


if __name__ == "__main__":
    phase = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    untuned = "--untuned" in sys.argv
    run_steered(phase, untuned=untuned)

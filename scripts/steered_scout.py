"""Steered scout: n=4, tuned orchestrator, SP2 profile, at a given phase.

Scout-before-pool, matching this project's own methodology (Amendment 2,
Task 8's unsteered scouts). Config (model, profile, timeout, seed, acceptance
suite) is identical to the eventual n=16 pre-registered batch
(docs/superpowers/specs/2026-07-28-section3-cost-equivalence-metrics.md) so
this n=4 result is poolable into that batch later rather than discarded.

Usage: python scripts/steered_scout.py [phase]
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from harness.runner import run_baseline, write_report
from harness.workspace import acceptance_suite_for_phase, seed_for_phase
from harness.session import InvocationProfile
from scripts.steered import extract_phase_prompt, MODEL, SUBAGENT_PATH

N = 4


def run_scout(phase: int):
    print(f"Steered scout (tuned): Phase {phase}, SP2, n={N}")
    print(f"Model: {MODEL}")
    print()

    research_dir = REPO_ROOT / "docs" / "section-3-sdd" / "research"
    research_dir.mkdir(parents=True, exist_ok=True)

    prompt = extract_phase_prompt(phase)

    checkpoint_dir = REPO_ROOT / ".pi-eval-checkpoints"
    checkpoint_dir.mkdir(exist_ok=True)
    checkpoint_path = checkpoint_dir / f"steered-tuned-phase{phase}-n16.jsonl"

    report = run_baseline(
        phase_prompt=prompt,
        app_source=REPO_ROOT / "examples" / "agentclinic",
        model=MODEL,
        profile=InvocationProfile.sp2(SUBAGENT_PATH),
        n=N,
        timeout=900,
        phase_name=f"Phase {phase} — Tuned SP2 (scout)",
        seed=seed_for_phase(phase),
        acceptance_suite=acceptance_suite_for_phase(phase),
        research_dir=research_dir,
        checkpoint_path=checkpoint_path,
    )

    today = __import__("datetime").datetime.now().isoformat()[:10]
    output = research_dir / f"{today}-post-repair-sp2-phase{phase}-tuned-scout-n4.md"
    write_report(report, output)

    print()
    print(f"Report: {output}")
    print(f"Success: {report.success_count}/{report.n} ({report.success_rate:.0%})")
    hang_count = sum(1 for r in report.results if r.outcome == "exited-with-hang")
    if hang_count:
        print(f"Hang incidence: {hang_count}/{report.n}")
    if report.mean_wall_time_s:
        print(f"Mean task duration: {report.mean_wall_time_s:.0f}s")
    if report.mean_turns:
        print(f"Mean turns: {report.mean_turns:.1f}")
    print(f"Checkpoint (poolable to n=16 later): {checkpoint_path}")


if __name__ == "__main__":
    phase = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    run_scout(phase)

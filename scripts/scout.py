"""Post-repair scout: run n=16 for a given phase with SP1 profile.

Locate the first phase where the unsteered model fails. Decision rule:
  >=15/16 → escalate to next phase (Amendment 2; pooled results only).
  <=12/16 → candidate ditch; stop escalating.
  13-14/16 → ambiguous; decide the site with the human.
  All phases solved → stop and return decision to human.
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from harness.runner import run_baseline, write_report
from harness.workspace import acceptance_suite_for_phase, seed_for_phase
from harness.session import InvocationProfile

ROADMAP = REPO_ROOT / "examples" / "agentclinic" / "specs" / "roadmap.md"
APP_SOURCE = REPO_ROOT / "examples" / "agentclinic"
MODEL = "omlx/gemma-4-12B-it-MLX-8bit"
N = 16  # Amendment 2: unsteered batches are n=16 (~60s/run); pooled decisions only


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


def run_scout(phase: int) -> int:
    """Run n=16 SP1 scouts for a phase. Returns success count.

    Amendment 2 decision rule (pooled results only, never a sub-batch):
    >=15/16 phase solved, escalate; <=12/16 candidate ditch; between,
    ambiguous -- report and decide with the human."""
    prompt = extract_phase_prompt(phase)
    research_dir = REPO_ROOT / "docs" / "section-2-measurement" / "research"
    research_dir.mkdir(parents=True, exist_ok=True)

    print(f"Phase {phase} prompt: {len(prompt)} bytes")
    print(f"Model: {MODEL}")
    print(f"Profile: SP1 (hello-world extension only, timeout=300s)")
    print(f"n={N}")
    print()

    report = run_baseline(
        phase_prompt=prompt,
        app_source=APP_SOURCE,
        model=MODEL,
        profile=InvocationProfile.sp1(),
        n=N,
        timeout=300,
        phase_name=f"Phase {phase} — {_phase_title(phase)}",
        seed=seed_for_phase(phase),
acceptance_suite=acceptance_suite_for_phase(phase),
        research_dir=research_dir,
    )

    today = __import__("datetime").datetime.now().isoformat()[:10]
    output = research_dir / f"{today}-post-repair-sp1-phase{phase}.md"
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

    return report.success_count


def _phase_title(phase: int) -> str:
    titles = {1: "Home Page", 2: "Complaints Board", 3: "Add Complaint"}
    return titles.get(phase, f"Phase {phase}")


if __name__ == "__main__":
    phase = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    success_count = run_scout(phase)

    # Amendment 2 decision rule, on POOLED results only (never a sub-batch).
    if success_count >= 15:
        print(f"\n→ {success_count}/{N} — Phase {phase} solved. Escalate to Phase {phase + 1}.")
    elif success_count <= 12:
        print(f"\n→ {success_count}/{N} — candidate ditch at Phase {phase}.")
    else:
        print(f"\n→ {success_count}/{N} — AMBIGUOUS (13-14/16). Report honestly; "
              f"decide the site with the human rather than auto-escalating.")

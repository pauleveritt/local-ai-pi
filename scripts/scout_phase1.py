"""Post-repair scout: Phase 1, n=4, SP1 (no-delegation) profile.

Locate the first phase where the unsteered model fails. Decision rule:
  4/4 pass → escalate to next phase.
  ≤3/4 pass → candidate ditch; stop escalating.
"""
import sys
from pathlib import Path

# Ensure the worktree root is on sys.path.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from harness.runner import run_baseline, write_report
from harness.session import InvocationProfile

REPO_ROOT = Path(__file__).resolve().parent.parent
ROADMAP = REPO_ROOT / "examples" / "agentclinic" / "specs" / "roadmap.md"
APP_SOURCE = REPO_ROOT / "examples" / "agentclinic"
RESEARCH_DIR = REPO_ROOT / "docs" / "section-2-measurement" / "research"
MODEL = "omlx/gemma-4-12B-it-MLX-8bit"
PHASE = 1
N = 4


def extract_phase_prompt(phase: int) -> str:
    """Extract the Phase N section from the roadmap."""
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
    # Last phase — grab to end.
    if start is not None:
        return "\n".join(lines[start:]).strip()
    raise ValueError(f"Phase {phase} not found in roadmap")


prompt = extract_phase_prompt(PHASE)
print(f"Phase {PHASE} prompt: {len(prompt)} bytes")
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
    phase_name=f"Phase {PHASE} — Home Page",
    research_dir=RESEARCH_DIR,
)

today = __import__("datetime").datetime.now().isoformat()[:10]
output = RESEARCH_DIR / f"{today}-post-repair-sp1-phase{PHASE}.md"
write_report(report, output)

print()
print(f"Report: {output}")
print(f"Success: {report.success_count}/{report.n} ({report.success_rate:.0%})")
hang_count = sum(1 for r in report.results if r.outcome == "exited-with-hang")
if hang_count:
    print(f"Hang incidence: {hang_count}/{report.n}")
print(f"Mean wall time: {report.mean_wall_time_s:.0f}s" if report.mean_wall_time_s else "Mean wall time: N/A")
print(f"Mean turns: {report.mean_turns:.1f}" if report.mean_turns else "Mean turns: N/A")

if report.success_count == 4:
    print("\n→ 4/4 — Phase 1 solved. Escalate to Phase 2.")
elif report.success_count <= 3:
    print(f"\n→ {report.success_count}/4 — candidate ditch at Phase 1. Pool to n=8 next.")

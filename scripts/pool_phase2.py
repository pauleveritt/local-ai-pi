"""Pooled Phase 2 baseline: n=8, SP1, identical config — canonical unsteered
baseline at the candidate ditch."""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from harness.runner import run_baseline, write_report
from harness.workspace import acceptance_suite_for_phase, seed_for_phase
from harness.session import InvocationProfile

ROADMAP = REPO_ROOT / "examples" / "agentclinic" / "specs" / "roadmap.md"
APP_SOURCE = REPO_ROOT / "examples" / "agentclinic"
RESEARCH_DIR = REPO_ROOT / "docs" / "section-2-measurement" / "research"
MODEL = "omlx/gemma-4-12B-it-MLX-8bit"


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


prompt = extract_phase_prompt(2)
print(f"Phase 2 pooled baseline: n=8, SP1")
print(f"Model: {MODEL}")
print()

report = run_baseline(
    phase_prompt=prompt,
    app_source=APP_SOURCE,
    model=MODEL,
    profile=InvocationProfile.sp1(),
    n=8,
    timeout=300,
    phase_name="Phase 2 — Complaints Board (pooled n=8, SP1)",
    seed=seed_for_phase(2),
acceptance_suite=acceptance_suite_for_phase(2),
    research_dir=RESEARCH_DIR,
)

today = __import__("datetime").datetime.now().isoformat()[:10]
output = RESEARCH_DIR / f"{today}-post-repair-sp1-phase2-pooled.md"
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

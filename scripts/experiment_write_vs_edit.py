"""Isolated experiment: does blocking whole-file writes to INHERITED files
prevent preservation breakage?

Background. lessons.md #12 clause 2 says whole-file writes are unsafe when
another phase owns part of the file. Forensics on 8 seeded Phase 2 runs found
a perfect split: 6/6 runs that EXTENDED inherited files passed; 2/2 that
REWROTE one failed, including the preservation breaker. That is correlation.
This makes it causal by intervening.

Design. Both arms run the identical seeded Phase 2 workload. The only
difference is the guard extension. Grading uses the PHASE 1 acceptance suite,
not phase 2's — so `preserved` answers exactly one question: after doing Phase
2 work, does Phase 1 still function?

  Arm CONTROL  — current tool surface.
  Arm GUARDED  — plus inherited-file-guard.ts: `write` blocked on files that
                 existed at session start; `write` to new files and `edit`
                 everywhere still allowed.

Secondary check: did the run actually do Phase 2 work? A run that changes
nothing would "preserve" vacuously, so preservation is only meaningful
alongside did_phase2_work.
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from harness.session import InvocationProfile, run_session  # noqa: E402
from harness.workspace import (  # noqa: E402
    acceptance_suite_for_phase,
    prepare_workspace,
    seed_for_phase,
)

MODEL = "omlx/gemma-4-12B-it-MLX-8bit"
N = int(sys.argv[1]) if len(sys.argv) > 1 else 4
GUARD = str(REPO_ROOT / ".pi" / "extensions" / "inherited-file-guard.ts")
PHASE = 2
PHASE1_ACCEPTANCE = acceptance_suite_for_phase(1)
RESEARCH = REPO_ROOT / "docs" / "section-2-measurement" / "research"

PHASE2_ARTIFACTS = ("models.py", "complaints.html")


def extract_phase_prompt(phase: int) -> str:
    text = (REPO_ROOT / "examples" / "agentclinic" / "specs" / "roadmap.md").read_text()
    start = text.index(f"## Phase {phase} ")
    try:
        end = text.index(f"## Phase {phase + 1} ")
    except ValueError:
        end = len(text)
    return text[start:end].strip()


def run_arm(label: str, extensions: list[str]) -> list[dict]:
    profile = InvocationProfile(extensions=extensions, timeout=300)
    prompt = extract_phase_prompt(PHASE)
    rows = []
    print(f"\n=== ARM {label} (n={N}) ===")
    for i in range(1, N + 1):
        print(f"  run {i}/{N}...", end=" ", flush=True)
        ws, pristine = prepare_workspace(
            REPO_ROOT / "examples" / "agentclinic", seed=seed_for_phase(PHASE)
        )
        try:
            r = run_session(
                ws, prompt, MODEL,
                pristine_hash=pristine,
                profile=profile,
                timeout=300,
                research_dir=RESEARCH,
                acceptance_suite=PHASE1_ACCEPTANCE,
            )
            did_work = any(
                any(a in f for a in PHASE2_ARTIFACTS) for f in r.changed_files
            )
            rows.append({
                "run": i, "arm": label, "outcome": r.outcome,
                "preserved": r.tests_pass, "did_phase2_work": did_work,
                "changed": r.changed_files, "artifact": r.artifact_path,
            })
            print(
                f"{r.outcome} | phase1 preserved: {'YES' if r.tests_pass else 'NO'}"
                f" | did phase2 work: {'yes' if did_work else 'no'}"
            )
        finally:
            import shutil
            shutil.rmtree(Path(ws).parent, ignore_errors=True)
    return rows


def summarize(rows: list[dict], label: str) -> None:
    n = len(rows)
    broke = sum(1 for r in rows if not r["preserved"])
    worked = sum(1 for r in rows if r["did_phase2_work"])
    both = sum(1 for r in rows if r["preserved"] and r["did_phase2_work"])
    print(f"  {label}: preservation broken {broke}/{n} | did phase-2 work {worked}/{n} "
          f"| both preserved AND worked {both}/{n}")


if __name__ == "__main__":
    control = run_arm("CONTROL", [".pi/extensions/hello-world.ts"])
    guarded = run_arm("GUARDED", [".pi/extensions/hello-world.ts", GUARD])

    print("\n=== RESULT (preservation = phase-1 acceptance after phase-2 work) ===")
    summarize(control, "CONTROL")
    summarize(guarded, "GUARDED")

import subprocess
from dataclasses import dataclass
from pathlib import Path

from harness.grading import GradeResult, grade
from harness.liveness import check_model_server_alive
from harness.workspace import prepare_workspace

REPO_ROOT = Path(__file__).resolve().parents[1]
PHASE_1 = REPO_ROOT / "examples" / "agentclinic" / "phase-1"
TASK_SPEC = REPO_ROOT / "examples" / "agentclinic" / "specs" / "roadmap.md"
EXTENSION = REPO_ROOT / ".pi" / "extensions" / "hello-world.ts"


@dataclass(frozen=True)
class RunResult:
    diff: str
    grade: GradeResult


def run_agentclinic_phase1(
    model: str = "omlx/gemma-4-12B-it-MLX-8bit",
    timeout: int = 600,
) -> RunResult:
    check_model_server_alive()

    with prepare_workspace(PHASE_1 / "empty") as workspace:
        initial_commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=workspace,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

        prompt = TASK_SPEC.read_text()
        subprocess.run(
            [
                "pi",
                "--model", model,
                "--no-extensions",
                "--extension", str(EXTENSION),
                "--no-skills",
                "--no-prompt-templates",
                "--no-themes",
                "--no-context-files",
                "--approve",
                "--",
                prompt,
            ],
            cwd=workspace,
            timeout=timeout,
            check=False,
        )

        # Stage everything before diffing: plain `git diff <commit>` never
        # shows untracked files, and the model's new files (app.py, etc.)
        # start out untracked. `git add -A` first, then diff the initial
        # commit against the index, so new files appear as additions.
        subprocess.run(
            ["git", "add", "-A"], cwd=workspace, check=True, capture_output=True
        )
        diff = subprocess.run(
            ["git", "diff", "--cached", initial_commit],
            cwd=workspace,
            check=True,
            capture_output=True,
            text=True,
        ).stdout

        grade_result = grade(workspace, PHASE_1 / "acceptance" / "test_acceptance.py")

    return RunResult(diff=diff, grade=grade_result)

import hashlib
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

from harness.grading import GradeResult, grade
from harness.liveness import check_model_server_alive
from harness.processes import run_process
from harness.workspace import prepare_workspace

REPO_ROOT = Path(__file__).resolve().parents[1]
PHASE_1 = REPO_ROOT / "examples" / "agentclinic" / "phase-1"
TASK_SPEC = REPO_ROOT / "examples" / "agentclinic" / "specs" / "roadmap.md"
EXTENSION = REPO_ROOT / ".pi" / "extensions" / "hello-world.ts"
DEFAULT_MODEL = "omlx/gemma-4-12B-it-MLX-8bit"


@dataclass(frozen=True)
class RunConditions:
    model: str
    pi_command: tuple[str, ...]
    pi_version: str
    task_spec_sha256: str
    harness_revision: str
    run_timeout: int
    grade_timeout: int | float


@dataclass(frozen=True)
class RunResult:
    diff: str
    grade: GradeResult
    pi_stdout: str
    pi_stderr: str
    pi_returncode: int | None
    pi_timed_out: bool = False
    conditions: RunConditions | None = None

    @property
    def accepted(self) -> bool:
        return not self.pi_timed_out and self.grade.accepted


def run_agentclinic_phase1(
    model: str = DEFAULT_MODEL,
    timeout: int = 600,
) -> RunResult:
    check_model_server_alive()

    with prepare_workspace() as workspace:
        initial_commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=workspace,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

        prompt = TASK_SPEC.read_text()
        command = _pi_command(model, prompt)
        pi_proc = run_process(
            command,
            timeout=timeout,
            cwd=workspace,
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

    return RunResult(
        diff=diff,
        grade=grade_result,
        pi_stdout=pi_proc.stdout,
        pi_stderr=pi_proc.stderr,
        pi_returncode=pi_proc.returncode,
        pi_timed_out=pi_proc.timed_out,
        conditions=_conditions(model, command, timeout),
    )


def _pi_command(model: str, prompt: str) -> list[str]:
    return [
        "pi", "--print", "--mode", "json", "--no-session", "--model", model,
        "--no-extensions", "--extension", str(EXTENSION), "--no-skills",
        "--no-prompt-templates", "--no-themes", "--no-context-files",
        "--approve", prompt,
    ]


def _conditions(model: str, command: list[str], timeout: int) -> RunConditions:
    revision = subprocess.run(
        ["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True
    ).stdout.strip()
    version = subprocess.run(
        ["pi", "--version"], check=True, capture_output=True, text=True
    ).stdout.strip()
    normalized = tuple("<task-spec>" if item == command[-1] else item for item in command)
    return RunConditions(
        model=model, pi_command=normalized, pi_version=version,
        task_spec_sha256=hashlib.sha256(TASK_SPEC.read_bytes()).hexdigest(),
        harness_revision=revision, run_timeout=timeout, grade_timeout=30,
    )


def preflight_model(model: str = "omlx/gemma-4-12B-it-MLX-8bit") -> None:
    """Require one real assistant message from the final Pi invocation."""
    check_model_server_alive()
    with prepare_workspace() as workspace:
        result = run_process(_pi_command(model, "Reply with exactly SATYRN."), cwd=workspace, timeout=60)
    if result.timed_out or result.returncode != 0 or not _has_assistant_content(result.stdout):
        raise RuntimeError("model preflight produced no usable assistant output")


def _has_assistant_content(output: str) -> bool:
    for line in output.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        message = event.get("message", event)
        content = message.get("content") if isinstance(message, dict) else None
        if isinstance(content, str) and content.strip():
            return True
    return False


def run_batch(
    checkpoint_path: Path,
    *,
    target: int = 16,
    model: str = DEFAULT_MODEL,
) -> list[RunResult]:
    """Run sequential attempts until the requested checkpoint length."""
    from harness.checkpoint import append_checkpoint, load_checkpoint

    if target < 0:
        raise ValueError("target must not be negative")
    records = load_checkpoint(checkpoint_path)
    command = _pi_command(model, TASK_SPEC.read_text())
    requested = _conditions(model, command, 600)
    for record in records:
        if record.conditions != requested:
            raise ValueError("checkpoint conditions do not match this batch")
    if len(records) >= target:
        return records[:target]

    preflight_model(model)
    while len(records) < target:
        result = run_agentclinic_phase1(model=model)
        if result.conditions != requested:
            raise RuntimeError("run conditions changed during batch")
        append_checkpoint(checkpoint_path, result)
        records.append(result)
    return records

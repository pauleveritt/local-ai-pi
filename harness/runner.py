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
EXAMPLES = REPO_ROOT / "examples"
EXTENSIONS: tuple[Path, ...] = (REPO_ROOT / ".pi" / "extensions" / "hello-world.ts",)
DEFAULT_MODEL = "omlx/gemma-4-12B-it-MLX-8bit"
EXPECTED_PI_VERSION = "0.83.0"


@dataclass(frozen=True)
class Suite:
    """One workload the harness can run: the prompt a model is given, the
    harness-owned contract it is graded against, and which model-written
    paths are copied out of the workspace for grading.

    Known-good and known-broken solutions are deliberately absent. A *run*
    never needs them; only the evidence-floor tests do, and those name the
    paths directly. `Suite` carries what a run requires and nothing else.

    Seeding is likewise absent. `prepare_workspace` already accepts a
    `source_dir`, but no suite uses it, and a field no caller sets is
    machinery ahead of the contract it serves.
    """

    name: str
    task_spec: Path
    acceptance: Path
    source_allowlist: tuple[str, ...]


AGENTCLINIC_PHASE_1 = Suite(
    name="agentclinic-phase-1",
    task_spec=EXAMPLES / "agentclinic" / "specs" / "roadmap.md",
    acceptance=EXAMPLES / "agentclinic" / "phase-1" / "acceptance" / "test_acceptance.py",
    source_allowlist=("app.py", "templates"),
)

DURATION = Suite(
    name="duration",
    task_spec=EXAMPLES / "duration" / "spec.md",
    acceptance=EXAMPLES / "duration" / "acceptance" / "test_acceptance.py",
    source_allowlist=("duration.py",),
)


@dataclass(frozen=True)
class RunConditions:
    """The conditions a run happened under, compared for equality by
    `run_batch` before resuming a checkpoint.

    `pi_command` records extension *paths*. `extension_digests` records
    their *contents*, and exists because without it, editing an
    extension leaves these conditions byte-identical — so a batch would
    silently resume a checkpoint whose earlier runs used different code.

    Records written before this field load with the sentinel
    `("<pre-cycle1>",)`. They stay readable and recomputable; no
    SHA-256 can equal the sentinel, so `run_batch` refuses to resume
    them. Unreadable is a different, worse failure than unresumable.
    """

    model: str
    pi_command: tuple[str, ...]
    pi_version: str
    task_spec_sha256: str
    harness_revision: str
    run_timeout: int
    grade_timeout: int | float
    extension_digests: tuple[str, ...]


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
        return not self.pi_timed_out and self.pi_returncode == 0 and self.grade.accepted


def run_suite(
    suite: Suite,
    *,
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

        prompt = suite.task_spec.read_text()
        extensions = EXTENSIONS
        command = _pi_command(model, prompt, extensions)
        conditions = _conditions(suite, model, command, timeout, extensions)
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

        grade_result = grade(
            workspace,
            suite.acceptance,
            source_allowlist=suite.source_allowlist,
        )

    return RunResult(
        diff=diff,
        grade=grade_result,
        pi_stdout=pi_proc.stdout,
        pi_stderr=pi_proc.stderr,
        pi_returncode=pi_proc.returncode,
        pi_timed_out=pi_proc.timed_out,
        conditions=conditions,
    )


def _pi_command(
    model: str, prompt: str, extensions: tuple[Path, ...] = EXTENSIONS
) -> list[str]:
    command = [
        "pi", "--print", "--mode", "json", "--no-session", "--model", model,
        "--no-extensions",
    ]
    for extension in extensions:
        command += ["--extension", str(extension)]
    # `--approve` is not an isolation flag: Pi's help defines it as "Trust
    # project-local files for this run" (cli/args.js:263). It widens trust.
    # Project-local extensions are excluded by `--no-extensions` above, not
    # by anything here -- so removing that flag would make a model-written
    # `.pi/extensions/*.ts` in the workspace loadable.
    command += [
        "--no-skills", "--no-prompt-templates", "--no-themes",
        "--no-context-files", "--approve", prompt,
    ]
    return command


def _extension_digest(path: Path) -> str:
    """SHA-256 of one extension file.

    Raises on a directory rather than hashing something plausible: Pi's
    shipped subagent extension is a directory tree, and how a tree is
    hashed is a decision for the cycle that needs it.
    """
    if path.is_dir():
        raise ValueError(f"extension is a directory, not a file: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _conditions(
    suite: Suite,
    model: str,
    command: list[str],
    timeout: int,
    extensions: tuple[Path, ...] = EXTENSIONS,
) -> RunConditions:
    """The conditions a run of `suite` happens under.

    `suite.task_spec`'s digest is load-bearing beyond recording the
    prompt: it is the **only** field of `RunConditions` that differs
    between two suites. `pi_command` normalizes the prompt away to
    `"<task-spec>"`, and model, Pi version, harness revision, both
    timeouts, and the extension digests are shared. Hash the suite that
    was passed in, never a module-level constant -- otherwise two suites'
    checkpoints become mutually resumable and runs graded against
    different contracts accumulate in one file looking like data.
    """
    revision = subprocess.run(
        ["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True
    ).stdout.strip()
    version = subprocess.run(
        ["pi", "--version"], check=True, capture_output=True, text=True
    ).stdout.strip()
    normalized = tuple("<task-spec>" if item == command[-1] else item for item in command)
    return RunConditions(
        model=model, pi_command=normalized, pi_version=version,
        task_spec_sha256=hashlib.sha256(suite.task_spec.read_bytes()).hexdigest(),
        harness_revision=revision, run_timeout=timeout, grade_timeout=30,
        extension_digests=tuple(_extension_digest(path) for path in extensions),
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
        if not isinstance(message, dict) or message.get("role") != "assistant":
            continue
        content = message.get("content") if isinstance(message, dict) else None
        if isinstance(content, str) and content.strip():
            return True
        if isinstance(content, list) and any(
            isinstance(part, dict)
            and isinstance(part.get("text"), str)
            and part["text"].strip()
            for part in content
        ):
            return True
    return False


def run_batch(
    checkpoint_path: Path,
    *,
    suite: Suite,
    target: int = 16,
    model: str = DEFAULT_MODEL,
) -> list[RunResult]:
    """Run sequential attempts until the requested checkpoint length.

    `suite` is required and undefaulted on purpose. A default would let a
    caller record a batch under a workload they never named, and since
    `task_spec_sha256` is the only condition that distinguishes two
    suites, that mistake produces a checkpoint that looks valid.
    """
    from harness.checkpoint import append_checkpoint, load_checkpoint

    if target < 0:
        raise ValueError("target must not be negative")
    records = load_checkpoint(checkpoint_path)
    extensions = EXTENSIONS
    command = _pi_command(model, suite.task_spec.read_text(), extensions)
    requested = _conditions(suite, model, command, 600, extensions)
    if requested.pi_version != EXPECTED_PI_VERSION:
        raise RuntimeError(
            f"this harness pins Pi {EXPECTED_PI_VERSION}, but {requested.pi_version} "
            f"is installed. Batches are pinned so that runs stay comparable "
            f"between contributors. Either install Pi {EXPECTED_PI_VERSION}, or "
            f"bump EXPECTED_PI_VERSION in harness/runner.py -- and if you bump it, "
            f"re-check docs/setup.md, which names the version twice, and the "
            f"documentation that cites Pi by file and line, because neither "
            f"survives an upgrade and no test catches them."
        )
    for record in records:
        if record.conditions != requested:
            raise ValueError("checkpoint conditions do not match this batch")
    if len(records) >= target:
        return records[:target]

    preflight_model(model)
    while len(records) < target:
        result = run_suite(suite, model=model)
        if result.conditions != requested:
            raise RuntimeError("run conditions changed during batch")
        append_checkpoint(checkpoint_path, result)
        records.append(result)
    return records

import hashlib
import json
import os
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
LOOP_BREAKER = REPO_ROOT / ".pi" / "extensions" / "loop-breaker.ts"
AGENT_DIR = REPO_ROOT / "pi-agent-dir"
AGENT_DIR_FILES: tuple[str, ...] = (
    "README.md",
    "settings.json",
    "models.json",
    "extensions/loop-breaker.ts",
)
DEFAULT_MODEL = "omlx/gemma-4-12B-it-MLX-8bit"
EXPECTED_PI_VERSION = "0.83.0"


def pi_env() -> dict[str, str]:
    """The environment every Pi process the harness starts runs under.

    `PI_CODING_AGENT_DIR` points Pi at `pi-agent-dir/` instead of
    `~/.pi/agent`. The parent does not need this -- it already passes
    `--no-extensions --no-skills --no-prompt-templates --no-themes
    --no-context-files` and is hermetic. **The child does.**

    The delegated child is spawned by Pi's shipped subagent extension as
    `pi --mode json -p --no-session [...]`, carrying none of those flags,
    and user-scope resources load unconditionally -- so before phase 5
    cycle 9 the child loaded the operator's own `~/.pi/agent/extensions/`
    and packages. That was not a theory: recorded child transcripts show
    `ls -R` returning the output of `rtk ls -R`, because the operator's
    `rtk.ts` rewrites bash commands on `tool_call`.

    An environment variable is the only seam that reaches the child. The
    shipped extension calls `spawn` without an `env` argument, so the child
    inherits ours; its *arguments* are fixed and its project-local resources
    are trust-gated away in a headless run.
    """
    return {**os.environ, "PI_CODING_AGENT_DIR": str(AGENT_DIR)}


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

AGENTCLINIC_PHASE_1_USER_STORY = Suite(
    name="agentclinic-phase-1-user-story",
    task_spec=EXAMPLES / "agentclinic" / "specs" / "roadmap-user-story.md",
    # Deliberately the *same* acceptance file and allowlist as
    # AGENTCLINIC_PHASE_1. The user-story document describes the identical
    # application, so grading both against one contract is what makes the
    # two comparable: the description varies and nothing else. Only
    # `task_spec_sha256` distinguishes their conditions, which is the
    # property `test_every_suites_task_spec_digest_is_pairwise_distinct`
    # exists to protect.
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
class Improvement:
    """A named, optional change to how a run is steered.

    A descriptor rather than a manifest file, following `Suite`: a parser,
    a schema, and an error path have no present caller. If a contributor
    ever needs to add an improvement without editing Python, that is the
    cycle that adds the manifest.

    `seed_dir` is copied into the workspace *before* git-init, so the files
    it carries land in the initial commit and never appear in the run diff.
    That is what makes `.pi/agents/implementer.md` placeable without
    polluting the record of what the model wrote.

    `system_prompt` is passed by flag and must **not** live under
    `.pi/agents/`: any `.md` there carrying `name:`/`description:`
    frontmatter is discovered as a callable specialist, so an orchestrator
    kept there could delegate to itself with no depth cap.

    A run has exactly one improvement or none. Nothing composes two.
    """

    name: str
    seed_dir: Path | None
    extensions: tuple[Path, ...]
    system_prompt: Path | None


IMPROVEMENTS = REPO_ROOT / "improvements"


def pi_package_root() -> Path:
    """Where Pi's installed package lives, so its shipped examples can be
    referenced by path rather than forked.

    **Not** resolved from `$(which pi)`, which is the recipe the prior
    project published. Under volta -- this project's setup -- `which pi`
    returns a shim: verified 2026-08-04, it gave
    `~/.volta/bin/pi`, whose realpath is `~/.volta/bin/volta-shim`, a
    binary that says nothing about which package it dispatches to.
    `npm root -g` is no better; it answered
    `~/.volta/tools/image/node/25.8.1/lib/node_modules`, which does not
    contain the package at all.

    Checked in order: `$SATYRN_PI_PACKAGE`, then volta's package layout.
    Both are paths rather than discovery logic, because a wrong answer here
    is expensive and silent -- the improvement would point at nothing and
    every orchestrated run would quietly be a bare run.
    """
    override = os.environ.get("SATYRN_PI_PACKAGE")
    if override:
        return Path(override)
    volta = (
        Path.home() / ".volta" / "tools" / "image" / "packages"
        / "@earendil-works" / "pi-coding-agent" / "lib" / "node_modules"
        / "@earendil-works" / "pi-coding-agent"
    )
    if volta.is_dir():
        return volta
    raise RuntimeError(
        "cannot locate Pi's installed package. Set SATYRN_PI_PACKAGE to the "
        "directory containing examples/extensions/subagent -- find it with "
        "`find ~ -maxdepth 8 -type d -name pi-coding-agent`. Resolving from "
        "`which pi` does not work under volta, and `npm root -g` points at "
        "the node image rather than the package."
    )


def sdd_orchestrator() -> Improvement:
    """Improvement #1: delegate to an `implementer` specialist instead of
    writing the solution directly.

    Two authored markdown files plus Pi's *shipped* subagent extension. No
    TypeScript, and no fork -- the fork was proposed and rejected on
    2026-08-03 because it freezes our copy against a substrate that keeps
    moving. Referencing the shipped tree by path and digesting its contents
    means a Pi upgrade changes the digest and `run_batch` refuses to
    resume, so drift is loud rather than silent.

    A function rather than a module-level constant: it resolves Pi's
    install location, and a constant would make `import harness.runner`
    fail on a machine without Pi. The suite must stay runnable for a
    contributor who has not installed it.

    **The extension is `index.ts`, not the `subagent/` directory.** This
    cost a live run to learn, on 2026-08-04. Pointing `--extension` at the
    directory produces no error, no stderr, and no warning -- Pi starts
    normally, our own hello-world extension still loads and emits its
    entry, and the only symptom appears much later, when the model calls
    the tool and gets `"Tool subagent not found"` with `isError: true`.
    The same probe with `index.ts` registered the tool and the delegation
    succeeded. Pi's own README for the example documents installation by
    symlinking `index.ts` into `~/.pi/agent/extensions/subagent/` and never
    mentions passing a directory.

    **Known residual gap.** `extension_digests` therefore covers
    `index.ts` only, while the extension really is a tree -- `index.ts`
    imports `agents.ts` beside it, and neither `agents/` nor `prompts/`
    is hashed. Left open deliberately rather than papered over with a
    guess about which parent directory to hash: the shipped tree changes
    only when Pi itself changes, and `EXPECTED_PI_VERSION` already refuses
    a batch on a different Pi. That is a different mechanism from a
    digest, and a weaker one -- it would miss a contributor editing the
    installed package in place -- so it is recorded here as a gap rather
    than claimed as coverage.
    """
    return Improvement(
        name="sdd-orchestrator",
        seed_dir=IMPROVEMENTS / "sdd-orchestrator" / "seed",
        extensions=(
            pi_package_root() / "examples" / "extensions" / "subagent" / "index.ts",
        ),
        system_prompt=IMPROVEMENTS / "sdd-orchestrator" / "orchestrator.md",
    )


def sdd_orchestrator_guarded() -> Improvement:
    """Improvement #2: `sdd-orchestrator` plus the loop-breaker extension.

    A separate improvement rather than a composition mechanism. The phase's
    binding rule is that a run has exactly one improvement or none, and
    `Improvement.extensions` is already a tuple -- so carrying two
    extensions needs no new machinery, and the unguarded improvement stays
    available as the comparison cycle 8 needs.
    """
    base = sdd_orchestrator()
    return Improvement(
        name="sdd-orchestrator-guarded",
        seed_dir=base.seed_dir,
        extensions=base.extensions + (LOOP_BREAKER,),
        system_prompt=base.system_prompt,
    )


def tech_stack_only() -> Improvement:
    """Improvement #4: the two facts, and nothing else.

    The control the phase's headline needs. Cycle 10 reported 13/16 against
    cycle 4's 0/16, but four changes separate those arms and one of them --
    cycle 7's Technology section -- was the single change that took the suite
    off the floor. So "orchestration works" and "we told it the framework"
    are not yet distinguishable, and the honest reading of 13/16 depends on
    which it is.

    This arm carries the Technology section **verbatim** and no orchestrator
    prose, no seeded specialist, and no delegation. Against cycle 10 it
    isolates orchestration; against a bare arm it isolates the two facts.

    It keeps the loop-breaker, because cycle 10 had it: dropping it here
    would put two differences between the arms instead of one. The guard
    costs nothing on a run that does not loop.
    """
    return Improvement(
        name="tech-stack-only",
        seed_dir=None,
        extensions=(LOOP_BREAKER,),
        system_prompt=IMPROVEMENTS / "tech-stack-only" / "stack.md",
    )


def sdd_orchestrator_guarded_stack() -> Improvement:
    """Improvement #3: the guarded orchestrator, told the technology stack.

    Phase 5 cycle 7's lever. Identical to `sdd_orchestrator_guarded` except
    for the system prompt, which is that prompt verbatim plus a Technology
    section naming FastAPI and `app.py`.

    Those are the two facts the acceptance contract genuinely requires. The
    suite disclaims file layout in its own docstring and couples only to
    `from app import app`; every run that wrote `app.py` and still failed did
    so with `TypeError: Flask.__call__() missing 1 required positional
    argument: 'start_response'`, because the model chose a WSGI framework and
    the suite drives ASGI. The module name is required separately because
    `source_allowlist` copies `app.py` and `templates` only -- a solution
    under `app/main.py` never reaches the grading directory at all.
    """
    base = sdd_orchestrator_guarded()
    return Improvement(
        name="sdd-orchestrator-guarded-stack",
        seed_dir=base.seed_dir,
        extensions=base.extensions,
        system_prompt=IMPROVEMENTS / "sdd-orchestrator" / "orchestrator-with-stack.md",
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

    The four phase-5 fields follow that precedent with `"<pre-phase5>"`
    (and `("<pre-phase5>",)` for the allowlist). They were added in one
    break rather than two: every added field costs the existing evidence
    its resumability, so the improvement digest -- which this cycle needed
    -- carried the two the Backlog already owed while the price was zero.

    `acceptance_sha256` and `source_allowlist` close a gap
    `harness_revision` cannot. It is `git rev-parse HEAD`, so an
    *uncommitted* edit to an acceptance file, or a changed allowlist,
    would otherwise leave these conditions byte-identical while the
    contract being graded against had moved. The allowlist is recorded
    verbatim rather than digested: it is a handful of short strings, and a
    reader of a checkpoint should be able to see them.

    `agent_dir_digest` (phase 5 cycle 9, sentinel `"<pre-cycle9>"`) records
    the tree `PI_CODING_AGENT_DIR` points at. It closes the widest gap this
    dataclass has had: the *child's* resources were never a recorded
    condition at all, so two runs could differ by an extension the operator
    happened to have installed while every field here stayed byte-identical.
    They did differ that way -- see `pi_env`.
    """

    model: str
    pi_command: tuple[str, ...]
    pi_version: str
    task_spec_sha256: str
    harness_revision: str
    run_timeout: int
    grade_timeout: int | float
    extension_digests: tuple[str, ...]
    improvement_name: str
    improvement_digest: str
    acceptance_sha256: str
    source_allowlist: tuple[str, ...]
    agent_dir_digest: str


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
    improvement: Improvement | None = None,
) -> RunResult:
    check_model_server_alive()

    with prepare_workspace(None if improvement is None else improvement.seed_dir) as workspace:
        initial_commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=workspace,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

        prompt = suite.task_spec.read_text()
        extensions = EXTENSIONS + (() if improvement is None else improvement.extensions)
        system_prompt = None if improvement is None else improvement.system_prompt
        command = _pi_command(model, prompt, extensions, system_prompt)
        conditions = _conditions(suite, model, command, timeout, extensions, improvement)
        pi_proc = run_process(
            command,
            timeout=timeout,
            cwd=workspace,
            env=pi_env(),
        )

        # Stage everything before diffing: plain `git diff <commit>` never
        # shows untracked files, and the model's new files (app.py, etc.)
        # start out untracked. `git add -A` first, then diff the initial
        # commit against the index, so new files appear as additions.
        #
        # Best-effort, because the diff is *diagnostic* and the verdict does
        # not depend on it -- `grade` copies allowlisted files into a fresh
        # directory and never reads this. A model that runs `git init` in a
        # subdirectory makes `git add -A` fail outright ("does not have a
        # commit checked out", exit 128), and before phase 5 cycle 4 that
        # aborted the whole batch: one completed run discarded, every queued
        # run cancelled, over a step that only produces a record of what was
        # written. Observed live on the user-story suite, whose spec names no
        # file layout, so scaffolding a repo is a reasonable thing to try.
        try:
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
        except subprocess.CalledProcessError as error:
            # Recorded rather than swallowed: a run whose diff is missing must
            # say so in the checkpoint, or a later reader counts it as a run
            # that wrote nothing.
            stderr = (error.stderr or b"").decode(errors="replace").strip()
            diff = f"<diff unavailable: {' '.join(error.cmd)} exited {error.returncode}: {stderr}>"

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
    model: str,
    prompt: str,
    extensions: tuple[Path, ...] = EXTENSIONS,
    system_prompt: Path | None = None,
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
        "--no-context-files", "--approve",
    ]
    # Before the prompt, never after: `_conditions` normalizes the *last*
    # element to "<task-spec>", so a flag appended after the prompt would
    # be hashed as the prompt and the real prompt recorded verbatim.
    if system_prompt is not None:
        command += ["--append-system-prompt", str(system_prompt)]
    command.append(prompt)
    return command


def _path_digest(path: Path) -> str:
    """SHA-256 of one file, or of a directory tree's contents.

    A tree is hashed as the sorted list of `<relative path> <file digest>`
    lines. Each half of that is load-bearing:

    - **Sorted**, because filesystem iteration order is not guaranteed and
      the same extension must digest identically on two machines.
    - **Relative to the tree root**, because Pi's shipped subagent
      extension lives at a different absolute path on every contributor's
      machine and moves on every Pi upgrade. An absolute-path-sensitive
      digest would report drift that is not there, and `run_batch` would
      refuse to resume a checkpoint that is still valid.
    - **Path *and* digest**, because two trees holding the same bytes at
      different paths are different extensions. Hashing the file digests
      alone would call them equal.

    Phase 4 cycle 1 raised on a directory and left the decision to "the
    cycle that needs it". This is that cycle: the shipped subagent
    extension is a directory, and an improvement's seed is one too.
    """
    if path.is_dir():
        entries = sorted(
            f"{child.relative_to(path).as_posix()} "
            f"{hashlib.sha256(child.read_bytes()).hexdigest()}"
            for child in path.rglob("*")
            if child.is_file()
        )
        return hashlib.sha256("\n".join(entries).encode()).hexdigest()
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _agent_dir_digest() -> str:
    """`AGENT_DIR`'s digest over the files the *harness* owns.

    `_path_digest` cannot be used directly here. Pi **writes into** the
    directory it is pointed at: the first invocation under a fresh agent dir
    creates an empty `auth.json`, and a run configured differently could
    leave sessions or caches. Hashing the whole tree therefore digests Pi's
    own runtime state alongside the resources this field exists to pin.

    Found by review before it cost a batch, and it would have. `run_batch`
    computes the conditions it enforces *before* `preflight_model`, so on any
    machine without that `auth.json` yet, the preflight would create it and
    run 1 would abort with "run conditions changed during batch". A
    checkpoint recorded on one machine would also be unresumable on a clean
    clone. Cycles 9 and 10 escaped only because the file already existed with
    constant contents before either batch started, which is luck rather than
    design.

    The owned files are **declared** in `AGENT_DIR_FILES` rather than
    discovered, so this stays a pure function of the filesystem: no
    subprocess, and no way for a file appearing in the directory to change a
    recorded condition by accident. `test_the_declared_agent_dir_files_are_
    exactly_what_git_tracks` cross-checks the declaration against
    `git ls-files`, so adding a file without declaring it fails a test rather
    than going silently unhashed.
    """
    entries = sorted(
        f"{name} {hashlib.sha256((AGENT_DIR / name).read_bytes()).hexdigest()}"
        for name in AGENT_DIR_FILES
    )
    return hashlib.sha256("\n".join(entries).encode()).hexdigest()


def _improvement_digest(improvement: Improvement | None) -> str:
    """Contents of everything an improvement carries, as one digest.

    The improvement's *extensions* are deliberately absent: they already
    reach `RunConditions` through `extension_digests`, and hashing them
    twice would make one edit look like two changes.
    """
    if improvement is None:
        return "<none>"
    parts = [
        _path_digest(path)
        for path in (improvement.seed_dir, improvement.system_prompt)
        if path is not None
    ]
    return hashlib.sha256("\n".join(parts).encode()).hexdigest()


def _conditions(
    suite: Suite,
    model: str,
    command: list[str],
    timeout: int,
    extensions: tuple[Path, ...] = EXTENSIONS,
    improvement: Improvement | None = None,
) -> RunConditions:
    """The conditions a run of `suite` happens under.

    `suite.task_spec`'s digest is load-bearing beyond recording the
    prompt, because `pi_command` normalizes the prompt away to
    `"<task-spec>"`. Hash the suite that was passed in, never a
    module-level constant -- otherwise two suites' checkpoints become
    mutually resumable and runs graded against different contracts
    accumulate in one file looking like data.

    **Corrected phase 5 cycle 1.** This docstring previously said
    `task_spec_sha256` was the *only* field distinguishing two suites.
    That was true when written and is not any more: `acceptance_sha256`
    and `source_allowlist` also come from the suite, so two suites now
    differ in three fields rather than one. The correction matters because
    the old claim was the stated reason several tests asserted what they
    did, and a reader reasoning from it would conclude that a shared
    task-spec file makes two suites indistinguishable. It no longer does
    on its own -- it makes them *less* distinguishable, which is still
    worth preventing.
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
        extension_digests=tuple(_path_digest(path) for path in extensions),
        improvement_name="none" if improvement is None else improvement.name,
        improvement_digest=_improvement_digest(improvement),
        acceptance_sha256=hashlib.sha256(suite.acceptance.read_bytes()).hexdigest(),
        source_allowlist=suite.source_allowlist,
        agent_dir_digest=_agent_dir_digest(),
    )


def preflight_model(model: str = "omlx/gemma-4-12B-it-MLX-8bit") -> None:
    """Require one real assistant message from the final Pi invocation."""
    check_model_server_alive()
    with prepare_workspace() as workspace:
        result = run_process(
            _pi_command(model, "Reply with exactly SATYRN."),
            cwd=workspace,
            timeout=60,
            env=pi_env(),
        )
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
    improvement: Improvement | None = None,
    timeout: int = 600,
) -> list[RunResult]:
    """Run sequential attempts until the requested checkpoint length.

    `suite` is required and undefaulted on purpose. A default would let a
    caller record a batch under a workload they never named, and the
    conditions that distinguish two suites all come *from* the suite --
    `task_spec_sha256`, `acceptance_sha256`, and `source_allowlist` --
    so that mistake produces a checkpoint that looks valid.

    `improvement` is defaulted, unlike `suite`, because "no improvement"
    is a real and common condition rather than an unnamed one, and it is
    recorded explicitly as `improvement_name="none"`.

    `timeout` must reach both `_conditions` and `run_suite`. It was
    hardcoded to 600 here while `run_suite` recorded whatever it was
    handed, so a batch at any other cap aborted on its first run with
    "run conditions changed during batch" -- the guard working correctly
    on a mismatch this function created. A reduced cap could not be
    expressed at all, which the phase 5 testing-economics plan depended
    on. `run_timeout` is part of `RunConditions`, so batches at different
    caps remain non-comparable by construction; this makes the cheap one
    *possible*, not equivalent.
    """
    from harness.checkpoint import append_checkpoint, load_checkpoint

    if target < 0:
        raise ValueError("target must not be negative")
    records = load_checkpoint(checkpoint_path)
    extensions = EXTENSIONS + (() if improvement is None else improvement.extensions)
    system_prompt = None if improvement is None else improvement.system_prompt
    command = _pi_command(model, suite.task_spec.read_text(), extensions, system_prompt)
    requested = _conditions(suite, model, command, timeout, extensions, improvement)
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
        result = run_suite(
            suite, model=model, timeout=timeout, improvement=improvement
        )
        if result.conditions != requested:
            raise RuntimeError("run conditions changed during batch")
        append_checkpoint(checkpoint_path, result)
        records.append(result)
    return records

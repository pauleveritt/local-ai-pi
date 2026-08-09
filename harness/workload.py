"""Primitives for commit-replay workloads.

Workload-agnostic by construction: everything here takes SHAs and paths
from a manifest and knows nothing about `svcs` specifically, so the
postponed application cohort needs no change in this module.
"""

import hashlib
import os
import shutil
import subprocess
import tarfile
import tempfile
import time
import tomllib
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

import harness.workload_plugin as workload_plugin
from harness.processes import run_process
from harness.workspace import GIT_ENV, disposable_dir, git_init_commit


class WorkloadError(RuntimeError):
    """Any failure that makes a workload operation untrustworthy.

    Deliberately one type. A caller cannot usefully recover from "the
    oracle hash drifted" differently from "the base SHA is missing" --
    both mean the instrument is not in the state its manifest claims,
    and the only correct response is to stop and show the operator why.
    """


def ensure_clone(upstream: str, cache_root: Path) -> Path:
    """Return a bare clone of `upstream` under `cache_root`, creating it once.

    Bare rather than a working clone: nothing ever checks out here.
    Trees are exported into disposable workspaces, so the cache stays a
    read-only object store that no task can perturb.

    The directory is named from the upstream URL, not hardcoded -- this
    module is workload-agnostic, and the postponed application cohort
    will point it somewhere else entirely.
    """
    cache_root.mkdir(parents=True, exist_ok=True)
    name = upstream.rstrip("/").rsplit("/", 1)[-1].removesuffix(".git")
    clone = cache_root / f"{name}.git"
    if clone.is_dir():
        return clone
    result = subprocess.run(
        ["git", "clone", "--bare", "-q", upstream, str(clone)],
        capture_output=True,
        text=True,
        env=GIT_ENV,
    )
    if result.returncode != 0:
        shutil.rmtree(clone, ignore_errors=True)
        raise WorkloadError(f"cloning {upstream} failed: {result.stderr.strip()}")
    return clone


def _require_sha(clone: Path, sha: str) -> None:
    probe = subprocess.run(
        ["git", "cat-file", "-e", f"{sha}^{{commit}}"],
        cwd=clone,
        capture_output=True,
        env=GIT_ENV,
    )
    if probe.returncode == 0:
        return
    subprocess.run(
        ["git", "fetch", "-q", "origin", "+refs/heads/*:refs/heads/*", "--tags"],
        cwd=clone,
        capture_output=True,
        env=GIT_ENV,
    )
    retry = subprocess.run(
        ["git", "cat-file", "-e", f"{sha}^{{commit}}"],
        cwd=clone,
        capture_output=True,
        env=GIT_ENV,
    )
    if retry.returncode != 0:
        raise WorkloadError(f"commit {sha} is not present in {clone} after a fetch")


def _export_subst_paths(clone: Path, sha: str, destination: Path) -> list[str]:
    """Paths in the tree at `sha` that carry the `export-subst` attribute.

    `check-attr` is pointed at `destination` as the work tree, not run
    bare. A bare repository has no working tree, so the commit's own
    `.gitattributes` is never consulted and every query silently returns
    "unspecified" -- which reads exactly like "no file needs fixing" and
    is how this leak stays invisible.
    """
    listing = subprocess.run(
        ["git", "ls-tree", "-r", "--name-only", "-z", sha],
        cwd=clone,
        capture_output=True,
        env=GIT_ENV,
    )
    if listing.returncode != 0:
        raise WorkloadError(
            f"git ls-tree {sha} failed: {listing.stderr.decode(errors='replace')}"
        )
    attrs = subprocess.run(
        [
            "git",
            "--git-dir",
            str(clone.resolve()),
            "--work-tree",
            str(destination.resolve()),
            "check-attr",
            "--stdin",
            "-z",
            "export-subst",
        ],
        cwd=destination,
        input=listing.stdout,
        capture_output=True,
        env=GIT_ENV,
    )
    if attrs.returncode != 0:
        raise WorkloadError(
            f"git check-attr failed: {attrs.stderr.decode(errors='replace')}"
        )
    # -z output is a flat NUL-separated stream of (path, attribute, value).
    fields = attrs.stdout.decode(errors="replace").split("\0")
    return [
        fields[i]
        for i in range(0, len(fields) - 2, 3)
        if fields[i + 1] == "export-subst" and fields[i + 2] == "set"
    ]


def _undo_export_subst(clone: Path, sha: str, destination: Path) -> None:
    """Restore `export-subst` files to their raw blob contents.

    `git archive` expands `$Format:...$` placeholders in any file marked
    `export-subst`. `svcs` marks `.git_archival.txt`, so an exported
    workspace would contain::

        node: 816403b5c1d3b9fff22bd9141fe836221dfe9d9c
        describe-name: 25.1.0-121-g816403b

    -- the exact upstream commit the base came from, sitting in the
    workspace. The history invariant would survive that (the target
    object is still absent), but the stated obligation is workspaces
    whose *layout* does not hand anyone the answer, and an upstream SHA
    is one `git log` away from the answer for anything with network
    access or public-history priors.

    Writing the blob back is also strictly more faithful than what
    archive produced: a real checkout of this commit contains the
    unexpanded template, which is what a bounded executor would see.
    """
    for relative in _export_subst_paths(clone, sha, destination):
        blob = subprocess.run(
            ["git", "cat-file", "blob", f"{sha}:{relative}"],
            cwd=clone,
            capture_output=True,
            env=GIT_ENV,
        )
        if blob.returncode != 0:
            raise WorkloadError(f"cannot read {relative} at {sha} to undo export-subst")
        (destination / relative).write_bytes(blob.stdout)


def export_tree(clone: Path, sha: str, destination: Path) -> None:
    """Extract the tree at `sha` into `destination`, creating it if needed.

    Via `git archive` rather than a checkout so the destination never
    receives git metadata from the clone -- that absence is what the
    history invariant rests on. `export-subst` expansions are then undone
    so the result matches a checkout rather than an archive.
    """
    _require_sha(clone, sha)
    destination.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(suffix=".tar") as archive:
        result = subprocess.run(
            ["git", "archive", "--format=tar", sha],
            cwd=clone,
            stdout=archive,
            stderr=subprocess.PIPE,
            env=GIT_ENV,
        )
        if result.returncode != 0:
            detail = result.stderr.decode(errors="replace").strip()
            raise WorkloadError(f"git archive {sha} failed: {detail}")
        archive.flush()
        with tarfile.open(archive.name) as tar:
            tar.extractall(destination, filter="data")
    _undo_export_subst(clone, sha, destination)
    _normalize_mtimes(destination)


# An arbitrary fixed instant (2000-01-01T00:00:00Z). Any constant does;
# what matters is that it carries no information.
_FIXED_MTIME = 946684800


def _normalize_mtimes(root: Path) -> None:
    """Stamp every extracted path with one fixed time.

    `git archive` sets each file's mtime to the *commit timestamp*, which
    identifies the base commit in public history almost as precisely as
    the SHA that `_undo_export_subst` removes -- the same provenance
    channel wearing different clothes. Restoring an export-subst file
    then gives it the current time, which is its own tell: the one file
    whose timestamp differs is the one that was rewritten.

    Normalising both away costs a `utime` per path and makes materialized
    trees reproducible stat-for-stat as well as byte-for-byte.
    """
    for path in sorted(root.rglob("*"), reverse=True):
        os.utime(path, (_FIXED_MTIME, _FIXED_MTIME), follow_symlinks=False)
    os.utime(root, (_FIXED_MTIME, _FIXED_MTIME))


@contextmanager
def materialize(clone: Path, sha: str) -> Iterator[Path]:
    """Yield a synthetic single-commit git repository holding the tree at `sha`.

    The workspace is a real, committable repo -- a later cycle turns
    candidate work into a commit here -- but its object store contains
    exactly one commit, the one `git_init_commit` just wrote. The
    upstream history, and therefore every target commit and hidden
    oracle, is absent from *this* object store, and the repo has no
    remote and no alternates pointing back at the clone.

    That is the whole claim. It is not confinement: nothing here stops a
    process from reading the clone cache by path.

    Disposable-dir and init-commit semantics are shared with
    `prepare_workspace` rather than reimplemented, so there is one
    definition of what a harness workspace is, and no second copy to
    drift from it.

    Removed on exit, including on exception.
    """
    with disposable_dir("satyrn-workload-") as workspace:
        export_tree(clone, sha, workspace)
        git_init_commit(workspace, f"materialized base {sha}")
        yield workspace


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


@dataclass(frozen=True)
class CohortEnv:
    """The one interpreter every workload suite runs under."""

    python: Path
    lock_sha256: str
    python_version: str
    platform: str


def _verify_interpreter(python: Path, require_python: str | None) -> tuple[str, str]:
    """Return (version, platform) for `python`, refusing an unexpected version.

    A lock pins *packages*, not the interpreter that reads them.
    `requires-python = ">=3.14,<3.15"` admits 3.14.0 and 3.14.7 alike,
    and two independent resolutions of one dependency list have already
    produced different test collections in this cohort. The interpreter
    is part of the freeze, so a manifest may name it exactly.
    """
    probe = subprocess.run(
        [
            str(python),
            "-c",
            "import platform, sys; print(platform.python_version()); print(sys.platform)",
        ],
        capture_output=True,
        text=True,
    )
    if probe.returncode != 0:
        raise WorkloadError(
            f"interpreter {python} is not runnable: {probe.stderr.strip()}"
        )
    version, _, plat = probe.stdout.strip().partition("\n")
    if require_python is not None and version != require_python:
        raise WorkloadError(
            f"interpreter is {version}, but {require_python} is required"
        )
    return version, plat


def ensure_cohort_env(
    env_source: Path,
    cache_root: Path,
    require_python: str | None = None,
) -> CohortEnv:
    """Sync the frozen cohort environment and return its interpreter.

    `uv sync --locked` refuses to update the lockfile, so a drifted
    declaration fails loudly here rather than quietly producing a
    different environment than the one every recorded result was
    measured against.

    `--no-install-project` is what makes PYTHONPATH the single source of
    the library under test: the environment carries dependencies only,
    so a materialized workspace is the only place `svcs` can come from.

    The venv is placed under the cache, not inside `env_source`, so the
    committed declaration directory stays free of build output.
    """
    lock = env_source / "uv.lock"
    if not lock.is_file():
        raise WorkloadError(f"no uv.lock in {env_source}; run `uv lock` there first")

    venv = (cache_root / "env").resolve()
    venv.parent.mkdir(parents=True, exist_ok=True)
    environ = dict(os.environ)
    environ["UV_PROJECT_ENVIRONMENT"] = str(venv)
    result = subprocess.run(
        ["uv", "sync", "--locked", "--no-install-project", "-q"],
        cwd=env_source,
        capture_output=True,
        text=True,
        env=environ,
    )
    if result.returncode != 0:
        raise WorkloadError(f"cohort env sync failed: {result.stderr.strip()}")

    python = venv / "bin" / "python"
    if not python.is_file():
        raise WorkloadError(f"cohort env has no interpreter at {python}")
    version, plat = _verify_interpreter(python, require_python)
    return CohortEnv(
        python=python,
        lock_sha256=sha256_file(lock),
        python_version=version,
        platform=plat,
    )


REASON_CLASSES = ("pass", "collection-error", "assertion-failure", "error", "timeout")

# pytest's documented exit codes. Reading these is far more robust than
# matching summary-line prose, which changes between pytest releases and
# which the code under test can write into directly.
_PYTEST_OK = 0
_PYTEST_TESTS_FAILED = 1
_PYTEST_INTERRUPTED = 2
_PYTEST_NO_TESTS = 5


@dataclass(frozen=True)
class SuiteResult:
    """One suite run, described by what pytest's own hooks reported.

    `outcomes` maps node id to `"phase:outcome"`, read from the results
    file `harness.workload_plugin` writes through pytest's own hooks.
    That is trustworthy in a way parsing stdout is not: hooks fire only
    when pytest actually ran a test, while stdout can be written to by
    the code under test. The phase is carried because a `setup` failure
    means the test never ran -- a different fact about a task than an
    assertion that ran and was wrong.

    `collection_errors` maps a collecting node to the exception that
    stopped it. A collection error records no test outcomes at all, so
    without this two collection errors are indistinguishable however
    differently they were caused.

    `fingerprint` is the stable comparison key -- two runs that fail
    *different* assertions, or fail to collect for *different* reasons,
    must not compare equal, or a suite failing randomly would look
    perfectly stable.
    """

    returncode: int | None
    reason_class: str
    outcomes: dict[str, str]
    collection_errors: dict[str, str]
    tests_passed: int
    wall_seconds: float
    timed_out: bool
    stdout_tail: str
    output: str = field(default="", repr=False)

    @property
    def failures(self) -> dict[str, str]:
        """Node id -> "phase:outcome" for everything that did not pass."""
        return {
            node: outcome
            for node, outcome in self.outcomes.items()
            if not outcome.endswith(":passed")
        }

    @property
    def fingerprint(self) -> tuple[object, ...]:
        return (
            self.reason_class,
            self.returncode,
            tuple(sorted(self.outcomes.items())),
            tuple(sorted(self.collection_errors.items())),
        )

    @property
    def fingerprint_sha256(self) -> str:
        return hashlib.sha256(repr(self.fingerprint).encode()).hexdigest()


def _read_outcomes(path: Path) -> tuple[dict[str, str], dict[str, str], bool]:
    """Parse the workload plugin's results file.

    Returns phase-tagged outcomes ("call:failed"), structured collection
    failures, and whether the session finished.

    Last line wins per nodeid. That is deliberate and matches
    `harness/grading.py`: a test whose call phase passed but whose
    teardown then failed appends a second, later `failed` line, and the
    later one is the truth.
    """
    outcomes: dict[str, str] = {}
    collection_errors: dict[str, str] = {}
    done = False
    if not path.is_file():
        return outcomes, collection_errors, done
    for line in path.read_text().splitlines():
        if line == workload_plugin.DONE_MARKER:
            done = True
            continue
        fields = line.split("\t")
        if fields[0] == workload_plugin.TEST_PREFIX and len(fields) == 4:
            _, nodeid, phase, outcome = fields
            outcomes[nodeid] = f"{phase}:{outcome}"
        elif fields[0] == workload_plugin.COLLECT_PREFIX and len(fields) == 3:
            collection_errors[fields[1]] = fields[2]
    return outcomes, collection_errors, done


def classify(
    returncode: int | None,
    outcomes: dict[str, str],
    done: bool,
    timed_out: bool,
) -> str:
    """Name *how* a suite failed, not merely that it did.

    A base that fails at collection because the API does not exist yet
    is the evidence a replay task needs. A base that collects and fails
    an assertion is a different -- often broken -- task. Both exit
    non-zero, so an exit code alone cannot qualify a task, and an import
    typo in an oracle would otherwise sail through as a valid rejection.

    Decided from pytest's exit code and the plugin's recorded outcomes,
    never from summary prose. Exit 2 is pytest interrupting itself,
    which is what a collection error produces -- and the session still
    finishes there, so `done` is true while `outcomes` is empty. Exit 5
    means nothing was collected at all: a mistyped command rather than a
    rejection, and it must never be mistaken for one.
    """
    if timed_out:
        return "timeout"
    if returncode == _PYTEST_INTERRUPTED:
        return "collection-error"
    if returncode == _PYTEST_NO_TESTS:
        return "error"
    if returncode == _PYTEST_OK and done:
        return "pass"
    if returncode == _PYTEST_TESTS_FAILED:
        # Only a *call*-phase failure is an assertion failure. A setup
        # failure means the test never ran -- a missing fixture, an
        # erroring conftest -- and a task declaring "assertion-failure"
        # must not be satisfied by one. Both arrive as `failed`, so
        # without the phase they are indistinguishable.
        if any(o == "call:failed" for o in outcomes.values()):
            return "assertion-failure"
        return "error"
    return "error"


def run_suite(
    workspace: Path,
    command: Sequence[str],
    env: CohortEnv,
    timeout: float = 300.0,
) -> SuiteResult:
    """Run one suite in `workspace` under the cohort interpreter.

    `command` is argv *after* `python -m`, so a manifest's
    `["pytest", "-q"]` becomes `<cohort python> -m pytest -q`.

    The grading plugin is staged into a temp directory *outside* the
    workspace, along with its results file. Two reasons: the workspace
    must stay byte-identical to the base tree, and pointing PYTHONPATH
    at this project's `harness/` would make every harness module
    importable from inside a suite under test.

    The child environment is built from nothing rather than inherited.
    The cohort env supplies dependencies, PYTHONPATH supplies exactly
    one copy of the project under test, and HOME and TMPDIR point into
    the *staging* directory -- not the workspace, and not the operator's
    home. Pointing TMPDIR at the workspace leaves `pytest-of-<user>/`
    behind on any suite that uses `tmp_path`, which a later cycle
    diffing a workspace would read as candidate output. No proxy
    variables are passed through, which is most of what "no network"
    means in practice, and is hygiene rather than a guarantee.

    Timed here rather than read off `ProcessResult`, which on this
    branch carries no duration.
    """
    with disposable_dir("satyrn-suite-") as staging:
        plugin_dir = staging / "plugin"
        plugin_dir.mkdir()
        shutil.copy2(Path(workload_plugin.__file__), plugin_dir / "workload_plugin.py")
        home = staging / "home"
        home.mkdir()
        tmp = staging / "tmp"
        tmp.mkdir()
        results = staging / "results.txt"
        results.touch()
        child_env = {
            "PATH": os.defpath,
            "PYTHONPATH": os.pathsep.join([str(workspace / "src"), str(plugin_dir)]),
            "PYTHONDONTWRITEBYTECODE": "1",
            "HOME": str(home),
            "LANG": "C.UTF-8",
            "LC_ALL": "C.UTF-8",
            "TMPDIR": str(tmp),
            workload_plugin.RESULTS_ENV_VAR: str(results),
        }
        started = time.monotonic()
        result = run_process(
            [str(env.python), "-m", *command, "-p", "workload_plugin"],
            cwd=workspace,
            timeout=timeout,
            env=child_env,
        )
        wall_seconds = time.monotonic() - started
        outcomes, collection_errors, done = _read_outcomes(results)

    output = result.stdout + result.stderr
    return SuiteResult(
        returncode=result.returncode,
        reason_class=classify(result.returncode, outcomes, done, result.timed_out),
        outcomes=outcomes,
        collection_errors=collection_errors,
        tests_passed=sum(
            1 for outcome in outcomes.values() if outcome.endswith(":passed")
        ),
        wall_seconds=wall_seconds,
        timed_out=result.timed_out,
        stdout_tail=output[-4000:],
        output=output,
    )


@dataclass(frozen=True)
class Manifest:
    """One task's frozen claim about itself."""

    task_id: str
    role: str
    axes: tuple[str, ...]
    upstream: str
    base_sha: str
    target_sha: str
    brief_path: Path
    contract_path: Path | None
    contract_version: int
    readable: tuple[str, ...]
    writable: tuple[str, ...]
    candidate_output: tuple[str, ...]
    oracle_files: tuple[str, ...]
    oracle_files_sha256: dict[str, str]
    oracle_command: tuple[str, ...]
    base_rejection: str
    rejection_missing_symbols: tuple[str, ...]
    rejection_failing_nodes: tuple[str, ...]
    preservation_command: tuple[str, ...]
    deselects: tuple[str, ...]
    deselect_reason: str
    env_id: str
    env_python: str
    env_lock_sha256: str
    attestations: dict[str, str]
    task_dir: Path


REQUIRED_ATTESTATIONS = (
    "behavior_not_structure",
    "statable_behaviorally",
    "substantive",
    "writable_bounded",
    "adaptations",
)


def _table(data: Mapping[str, object], key: str, where: str) -> dict[str, object]:
    value = data.get(key)
    if not isinstance(value, dict):
        raise WorkloadError(f"manifest is missing the [{where}] table")
    return dict(value)


def _string(table: Mapping[str, object], key: str, where: str) -> str:
    if key not in table:
        raise WorkloadError(f"manifest is missing {where}.{key}")
    return str(table[key])


def _strings(table: Mapping[str, object], key: str, where: str) -> tuple[str, ...]:
    if key not in table:
        raise WorkloadError(f"manifest is missing {where}.{key}")
    value = table[key]
    if not isinstance(value, list):
        raise WorkloadError(f"{where}.{key} must be a list")
    return tuple(str(item) for item in value)


def _optional_strings(
    table: Mapping[str, object], key: str, where: str
) -> tuple[str, ...]:
    return _strings(table, key, where) if key in table else ()


def _require_full_sha(label: str, value: str) -> None:
    if len(value) != 40 or not all(c in "0123456789abcdef" for c in value):
        raise WorkloadError(f"{label} must be a full 40-character SHA, got {value!r}")


def _require_relative(label: str, patterns: tuple[str, ...]) -> None:
    for pattern in patterns:
        if pattern.startswith("/") or ".." in pattern:
            raise WorkloadError(
                f"policy.{label} entry {pattern!r} must be repository-relative with no '..'"
            )


def load_manifest(task_dir: Path) -> Manifest:
    """Read and validate one task manifest.

    Validation is not politeness. A manifest is the frozen claim a task
    makes about itself, and every field here is something a later result
    is reported against -- so a missing field, a drifted brief, an
    abbreviated SHA, or an attestation nobody wrote has to stop the run
    rather than be filled in with a default.
    """
    path = task_dir / "manifest.toml"
    if not path.is_file():
        raise WorkloadError(f"no manifest.toml in {task_dir}")
    data = tomllib.loads(path.read_text())

    manifest_task_id = _string(data, "task_id", "manifest")
    source = _table(data, "source", "source")
    task = _table(data, "task", "task")
    policy = _table(data, "policy", "policy")
    oracle = _table(data, "oracle", "oracle")
    rejection = _table(oracle, "rejection", "oracle.rejection")
    preservation = _table(data, "preservation", "preservation")
    environment = _table(data, "environment", "environment")

    raw_attestations = data.get("attestations", {})
    attestations = (
        {str(k): str(v) for k, v in raw_attestations.items()}
        if isinstance(raw_attestations, dict)
        else {}
    )
    for key in REQUIRED_ATTESTATIONS:
        if not attestations.get(key, "").strip():
            raise WorkloadError(
                f"attestation {key!r} is missing or empty. Five rubric items are "
                "curator judgment rather than machine checks, and an attestation "
                "that silently defaults to absent is the same as no attestation "
                "while still looking like one."
            )

    brief_path = task_dir / _string(task, "brief", "task")
    if not brief_path.is_file():
        raise WorkloadError(f"brief {brief_path} does not exist")
    declared_brief = _string(task, "brief_sha256", "task")
    actual_brief = sha256_file(brief_path)
    if declared_brief != actual_brief:
        raise WorkloadError(
            f"brief.md drift in {task_dir}: manifest says {declared_brief[:12]}, "
            f"file is {actual_brief[:12]}"
        )

    contract_path: Path | None = None
    if "contract" in task:
        contract_path = task_dir / _string(task, "contract", "task")
        if not contract_path.is_file():
            raise WorkloadError(f"contract {contract_path} does not exist")
        declared_contract = _string(task, "contract_sha256", "task")
        actual_contract = sha256_file(contract_path)
        if declared_contract != actual_contract:
            raise WorkloadError(
                f"contract drift in {task_dir}: manifest says {declared_contract[:12]}, "
                f"file is {actual_contract[:12]}"
            )

    base_rejection = _string(rejection, "class", "oracle.rejection")
    if base_rejection not in REASON_CLASSES:
        raise WorkloadError(
            f"oracle.rejection.class {base_rejection!r} is not one of {REASON_CLASSES}"
        )
    if base_rejection == "pass":
        raise WorkloadError(
            "oracle.rejection.class cannot be 'pass' -- the oracle must reject the base"
        )
    missing_symbols = _optional_strings(
        rejection, "missing_symbols", "oracle.rejection"
    )
    failing_nodes = _optional_strings(rejection, "failing_nodes", "oracle.rejection")
    if not missing_symbols and not failing_nodes:
        raise WorkloadError(
            "oracle.rejection needs missing_symbols or failing_nodes -- a bare class "
            "does not distinguish 'this API does not exist yet' from 'the oracle has a typo'"
        )

    base_sha = _string(source, "base_sha", "source")
    target_sha = _string(source, "target_sha", "source")
    _require_full_sha("base_sha", base_sha)
    _require_full_sha("target_sha", target_sha)

    readable = _strings(policy, "readable", "policy")
    writable = _strings(policy, "writable", "policy")
    _require_relative("readable", readable)
    _require_relative("writable", writable)

    deselects = _optional_strings(preservation, "deselects", "preservation")
    deselect_reason = str(preservation.get("deselect_reason", ""))
    if deselects and not deselect_reason.strip():
        raise WorkloadError("a deselect list requires a written deselect_reason")

    env_python = _string(environment, "python", "environment")
    env_lock = _string(environment, "lock_sha256", "environment")
    if not env_lock.strip():
        raise WorkloadError(
            "environment.lock_sha256 must be a real hash. A blank one silently "
            "accepts whatever environment happens to be present, which is the "
            "opposite of a freeze."
        )
    if not env_python.strip():
        raise WorkloadError("environment.python must name an exact interpreter version")

    _require_relative("oracle.files", _strings(oracle, "files", "oracle"))
    _require_relative(
        "candidate_output", _optional_strings(policy, "candidate_output", "policy")
    )
    _require_relative("task.brief", (_string(task, "brief", "task"),))
    if "contract" in task:
        _require_relative("task.contract", (_string(task, "contract", "task"),))

    if manifest_task_id != task_dir.name:
        raise WorkloadError(
            f"task_id {manifest_task_id!r} does not match its directory {task_dir.name!r}"
        )

    raw_hashes = oracle.get("files_sha256", {})
    oracle_hashes = (
        {str(k): str(v) for k, v in raw_hashes.items()}
        if isinstance(raw_hashes, dict)
        else {}
    )

    return Manifest(
        task_id=manifest_task_id,
        role=_string(data, "role", "manifest"),
        axes=_optional_strings(data, "axes", "manifest"),
        upstream=_string(source, "upstream", "source"),
        base_sha=base_sha,
        target_sha=target_sha,
        brief_path=brief_path,
        contract_path=contract_path,
        contract_version=int(str(task.get("contract_version", 1))),
        readable=readable,
        writable=writable,
        candidate_output=_optional_strings(policy, "candidate_output", "policy"),
        oracle_files=_strings(oracle, "files", "oracle"),
        oracle_files_sha256=oracle_hashes,
        oracle_command=_strings(oracle, "command", "oracle"),
        base_rejection=base_rejection,
        rejection_missing_symbols=missing_symbols,
        rejection_failing_nodes=failing_nodes,
        preservation_command=_strings(preservation, "command", "preservation"),
        deselects=deselects,
        deselect_reason=deselect_reason,
        env_id=_string(environment, "id", "environment"),
        env_python=env_python,
        env_lock_sha256=env_lock,
        attestations=attestations,
        task_dir=task_dir,
    )


def overlay_oracle(clone: Path, manifest: Manifest, destination: Path) -> None:
    """Copy the hidden oracle files from the target commit into `destination`.

    Called only on a grading *copy*, never on a workspace an executor
    will touch -- so no candidate workspace contains an oracle file at
    any point in its life.

    Oracle content is verified against the manifest's hashes. Drift is
    an error and never a silent re-baseline: an oracle that changed
    under a frozen manifest means every earlier result for this task was
    measured against different tests.
    """
    with disposable_dir("satyrn-oracle-") as staging:
        export_tree(clone, manifest.target_sha, staging)
        for relative in manifest.oracle_files:
            source = staging / relative
            if not source.is_file():
                raise WorkloadError(
                    f"oracle file {relative} is not present at target {manifest.target_sha}"
                )
            declared = manifest.oracle_files_sha256.get(relative)
            if declared is None:
                raise WorkloadError(f"no recorded hash for oracle file {relative}")
            actual = sha256_file(source)
            if declared != actual:
                raise WorkloadError(
                    f"oracle drift in {relative}: manifest says {declared[:12]}, "
                    f"target has {actual[:12]}"
                )
            target_path = destination / relative
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target_path)


CONDITIONS = (
    "base_preservation",
    "base_oracle",
    "target_preservation",
    "target_oracle",
)

# A qualified task means something only if the run that qualified it was
# at full strength. Callers may make qualification *harder* (more
# repeats, a tighter budget) but never easier.
MIN_REPEATS = 3
MAX_SECONDS_CEILING = 60.0


@dataclass(frozen=True)
class ConditionRun:
    """One condition, run `repeats` times, each in its own materialization."""

    name: str
    results: tuple[SuiteResult, ...]

    @property
    def first(self) -> SuiteResult:
        return self.results[0]

    @property
    def stable(self) -> bool:
        return all(r.fingerprint == self.results[0].fingerprint for r in self.results)

    @property
    def slowest(self) -> float:
        return max(r.wall_seconds for r in self.results)

    def payload(self) -> dict[str, object]:
        """The committed evidence for one condition.

        Every non-passing node is listed by name and phase, and every
        repeat contributes a fingerprint hash. Together those make
        "exactly the pre-registered failures, three times" auditable
        from the committed record without rerunning anything. Passing
        nodes are summarised by count rather than enumerated -- naming
        all 137 of them would bury the three that matter.
        """
        return {
            "reason_class": self.first.reason_class,
            "returncode": self.first.returncode,
            "tests_passed": self.first.tests_passed,
            "runs": len(self.results),
            "stable": self.stable,
            "wall_seconds": [round(r.wall_seconds, 3) for r in self.results],
            "node_count": len(self.first.outcomes),
            "nodes": sorted(self.first.outcomes),
            "failures": dict(sorted(self.first.failures.items())),
            "collection_errors": dict(sorted(self.first.collection_errors.items())),
            "fingerprint_sha256": [r.fingerprint_sha256 for r in self.results],
        }


def _run_condition(
    name: str,
    clone: Path,
    sha: str,
    command: Sequence[str],
    env: CohortEnv,
    manifest: Manifest,
    overlay: bool,
    repeats: int,
    timeout: float,
) -> ConditionRun:
    """Run one condition `repeats` times, each in a fresh materialization.

    Freshness is the point. Repeating inside a single workspace tells
    you whether a suite is idempotent within a directory -- a weaker and
    different property than whether two independent runs of the same
    commit agree, which is what a replay task needs.
    """
    results = []
    for _ in range(repeats):
        with materialize(clone, sha) as workspace:
            if overlay:
                overlay_oracle(clone, manifest, workspace)
            results.append(run_suite(workspace, command, env, timeout))
    return ConditionRun(name=name, results=tuple(results))


def _rejection_mismatch(manifest: Manifest, observed: SuiteResult) -> str | None:
    """Compare the observed base rejection against the pre-registered fingerprint.

    A class alone is not evidence. `collection-error` is produced both
    by "the API this task adds does not exist yet" and by "the oracle
    file has a typo in an unrelated import", and only the first is a
    task. So the manifest names either the symbols expected to be
    missing or the nodes expected to fail, and both are checked.

    Searched against full output rather than the tail: a verbose
    collection error can push a symbol name past the last 4000
    characters and disqualify a task that was fine.
    """
    if observed.reason_class != manifest.base_rejection:
        return f"base was {observed.reason_class}, manifest declares {manifest.base_rejection}"

    if manifest.rejection_missing_symbols:
        # Searched in the *collection failures* only, not anywhere in
        # output. A symbol name appears in stdout merely by being on the
        # source line pytest echoes back, which proves nothing about
        # what caused the error.
        if not observed.collection_errors:
            return (
                "manifest declares missing symbols, but the run recorded no "
                "collection failure to attribute them to"
            )
        reasons = " ".join(observed.collection_errors.values())
        for symbol in manifest.rejection_missing_symbols:
            if symbol not in reasons:
                return (
                    f"expected the collection failure to name {symbol!r}, "
                    f"but it says: {reasons[:200]}"
                )

    if manifest.rejection_failing_nodes:
        # Exact equality, not a subset. A base that fails the three
        # declared nodes *and* four undeclared ones is not the task the
        # manifest describes, and admitting it would let unrelated
        # breakage ride along inside a qualified task.
        failed = set(observed.failures)
        expected = set(manifest.rejection_failing_nodes)
        if failed != expected:
            missing = sorted(expected - failed)
            extra = sorted(failed - expected)
            return (
                "declared failing nodes do not match observed; "
                f"missing={missing} unexpected={extra}"
            )
    return None


def qualify(
    manifest: Manifest,
    clone: Path,
    env: CohortEnv,
    repeats: int = 3,
    timeout: float = 300.0,
    max_seconds: float = 60.0,
) -> dict[str, object]:
    """Prove one task is a real replay task. No model calls.

    Four conditions, in the only order that makes sense: a base that
    cannot pass its own suite is not a starting point; an oracle that
    does not reject that base for the pre-registered reason is not
    measuring the task; a target that cannot pass both is not a
    solution. Each runs `repeats` times in fresh materializations, and
    all runs must agree at node level.

    `max_seconds` enforces the sub-minute validation the design
    requires. `timeout` is the far larger backstop that kills a hung
    child; a suite landing between the two is a qualification failure,
    not a crash.

    Refuses weakened parameters outright rather than returning a weaker
    verdict. `repeats=1` would make every task trivially "stable", and a
    raised `max_seconds` would retire the threshold the design commits
    to -- and both would still emit `status="qualified"`, which is the
    word the whole cohort is reported under.
    """
    if repeats < MIN_REPEATS:
        raise WorkloadError(
            f"repeats={repeats} cannot qualify anything: {MIN_REPEATS} is the minimum, "
            "and one run makes every task trivially stable"
        )
    if max_seconds > MAX_SECONDS_CEILING:
        raise WorkloadError(
            f"max_seconds={max_seconds} exceeds the {MAX_SECONDS_CEILING}s ceiling the "
            "design commits to; a tighter budget is allowed, a looser one is not"
        )
    report: dict[str, object] = {
        "task_id": manifest.task_id,
        "role": manifest.role,
        "base_sha": manifest.base_sha,
        "target_sha": manifest.target_sha,
        "manifest_sha256": sha256_file(manifest.task_dir / "manifest.toml"),
        "env_id": manifest.env_id,
        "env_lock_sha256": env.lock_sha256,
        "env_python": env.python_version,
        "manifest_env_python": manifest.env_python,
        "env_platform": env.platform,
        "preservation_command": list(manifest.preservation_command),
        "oracle_command": list(manifest.oracle_command),
        "deselects": list(manifest.deselects),
        "recorded_at": datetime.now(UTC).isoformat(),
        "repeats": repeats,
        "max_seconds": max_seconds,
        "conditions": {},
    }

    def _disqualify(gate: str, detail: str) -> dict[str, object]:
        report["status"] = "disqualified"
        report["failed_gate"] = gate
        report["detail"] = detail
        return report

    if manifest.env_lock_sha256 != env.lock_sha256:
        return _disqualify(
            "environment",
            f"manifest declares lock {manifest.env_lock_sha256[:12]}, "
            f"cohort env is {env.lock_sha256[:12]}",
        )
    if manifest.env_python != env.python_version:
        # Always compared, never opt-in. Leaving this to a CLI flag meant
        # the freeze held only when someone remembered to ask for it.
        return _disqualify(
            "environment",
            f"manifest declares Python {manifest.env_python}, "
            f"cohort env is {env.python_version}",
        )

    conditions = report["conditions"]
    assert isinstance(conditions, dict)
    # Deselects are applied here, not merely recorded. load_manifest
    # validated them and the report lists them; a manifest whose list was
    # silently ignored would run the full suite and then disqualify for a
    # failure it had already declared out of scope.
    preservation = tuple(manifest.preservation_command) + tuple(
        argument for entry in manifest.deselects for argument in ("--deselect", entry)
    )
    report["effective_preservation_command"] = list(preservation)
    plan = (
        ("base_preservation", manifest.base_sha, preservation, False),
        ("base_oracle", manifest.base_sha, manifest.oracle_command, True),
        ("target_preservation", manifest.target_sha, preservation, False),
        ("target_oracle", manifest.target_sha, manifest.oracle_command, True),
    )

    runs: dict[str, ConditionRun] = {}
    for name, sha, command, overlay in plan:
        run = _run_condition(
            name, clone, sha, command, env, manifest, overlay, repeats, timeout
        )
        runs[name] = run
        conditions[name] = run.payload()

        if name == "base_oracle":
            # Every repeat, not just the first. A collection error records
            # no nodes, so its fingerprint is ("collection-error", 2, ())
            # and any two collection errors compare stable no matter what
            # caused them. Checking only run one would let a base reject
            # for the pre-registered symbol once and for something else
            # twice and still qualify -- in the exact condition this
            # instrument exists to establish.
            for index, attempt in enumerate(run.results):
                mismatch = _rejection_mismatch(manifest, attempt)
                if mismatch is not None:
                    report["base_oracle_tail"] = attempt.stdout_tail
                    return _disqualify("base_rejection", f"run {index + 1}: {mismatch}")
        elif run.first.reason_class != "pass":
            report[f"{name}_tail"] = run.first.stdout_tail
            return _disqualify(
                name, f"{name} is {run.first.reason_class}, expected pass"
            )

    unstable = [name for name, run in runs.items() if not run.stable]
    if unstable:
        return _disqualify("stability", f"runs disagreed at node level for: {unstable}")

    slow = {
        name: round(run.slowest, 3)
        for name, run in runs.items()
        if run.slowest > max_seconds
    }
    if slow:
        return _disqualify("runtime", f"conditions exceeded {max_seconds}s: {slow}")

    report["status"] = "qualified"
    return report


@dataclass(frozen=True)
class Cohort:
    """A candidate ladder plus the frozen record of what survived it."""

    name: str
    upstream: str
    env_dir: Path
    tasks: tuple[str, ...]
    included: tuple[str, ...]
    excluded: dict[str, str]
    root: Path

    def task_dir(self, task_id: str) -> Path:
        return self.root / "tasks" / task_id

    @property
    def unaccounted(self) -> tuple[str, ...]:
        settled = set(self.included) | set(self.excluded)
        return tuple(task for task in self.tasks if task not in settled)


def load_cohort(path: Path, require_accounting: bool = False) -> Cohort:
    """Read `cohort.toml`, refusing shapes that would lose an exclusion.

    `require_accounting` is the freeze check: every candidate must appear
    in exactly one of `included` or `excluded`. It is off during
    curation, when both lists are legitimately incomplete, and on once
    the cohort is frozen -- which is the moment a silently dropped
    candidate stops being work-in-progress and starts being a gap in the
    record.
    """
    if not path.is_file():
        raise WorkloadError(f"no cohort file at {path}")
    data = tomllib.loads(path.read_text())

    tasks = _strings(data, "tasks", "cohort")
    included = _optional_strings(data, "included", "cohort")
    raw_excluded = data.get("excluded", {})
    excluded = (
        {str(k): str(v) for k, v in raw_excluded.items()}
        if isinstance(raw_excluded, dict)
        else {}
    )

    known = set(tasks)
    for task in included:
        if task not in known:
            raise WorkloadError(
                f"included task {task!r} is not in the candidate ladder"
            )
    for task, reason in excluded.items():
        if task not in known:
            raise WorkloadError(
                f"excluded task {task!r} is not in the candidate ladder"
            )
        if not reason.strip():
            raise WorkloadError(
                f"excluded task {task!r} has no reason. An exclusion without prose is "
                "indistinguishable from a candidate someone forgot."
            )
    both = set(included) & set(excluded)
    if both:
        raise WorkloadError(f"tasks are both included and excluded: {sorted(both)}")

    cohort = Cohort(
        name=_string(data, "name", "cohort"),
        upstream=_string(data, "upstream", "cohort"),
        env_dir=path.parent / _string(data, "env", "cohort"),
        tasks=tasks,
        included=included,
        excluded=excluded,
        root=path.parent,
    )
    if require_accounting and cohort.unaccounted:
        raise WorkloadError(
            f"frozen cohort does not account for: {list(cohort.unaccounted)}. "
            "Every candidate must be included or excluded with a reason."
        )
    return cohort

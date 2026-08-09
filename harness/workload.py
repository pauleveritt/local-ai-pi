"""Primitives for commit-replay workloads.

Workload-agnostic by construction: everything here takes SHAs and paths
from a manifest and knows nothing about `svcs` specifically, so the
postponed application cohort needs no change in this module.
"""

import shutil
import subprocess
import tarfile
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

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


def export_tree(clone: Path, sha: str, destination: Path) -> None:
    """Extract the tree at `sha` into `destination`, creating it if needed.

    Via `git archive` rather than a checkout so the destination never
    receives git metadata from the clone -- that absence is what the
    history invariant rests on.
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

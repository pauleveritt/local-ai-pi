"""Task qualification: is this task well-formed enough to measure against?

Split out of `tests/test_workload.py` alongside `harness/qualification.py`
(2026-08-12). The module under test has no caller on the product path --
only `tools/qualify_workload.py` and these tests -- and keeping its
tests inside a 1,320-line file that also covered clone materialization,
manifest parsing and pytest classification was part of what made the
product boundary hard to see.

Shared fixtures still come from `tests/test_workload.py`; splitting
those too would duplicate a synthetic-repository builder for no gain,
and `tests/test_screen.py` already imports from there for the same
reason.
"""

import json
import platform
import shutil
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import pytest

import harness.qualification as qualification_module
import harness.workload as workload_module
from harness.qualification import qualify
from harness.workload import WorkloadError, load_manifest, materialize, sha256_file
from tests.test_workload import (
    SyntheticClone,
    _condition_of,
    _fake_env,
    _manifest_with_real_oracle_hash,
    _suite_result,
    _write_cohort,
    _write_manifest,
)
from tools.qualify_workload import main as qualify_main


def test_qualify_accepts_a_well_formed_task(
    tmp_path: Path, synthetic_clone: SyntheticClone
) -> None:
    task_dir, bare = _manifest_with_real_oracle_hash(tmp_path, synthetic_clone)
    report = qualify(load_manifest(task_dir), bare, _fake_env())
    assert report["status"] == "qualified"
    assert _condition_of(report, "base_preservation")["reason_class"] == "pass"
    assert _condition_of(report, "base_oracle")["reason_class"] == "collection-error"
    assert _condition_of(report, "target_preservation")["reason_class"] == "pass"
    assert _condition_of(report, "target_oracle")["reason_class"] == "pass"


def test_qualify_runs_every_condition_three_times(
    tmp_path: Path, synthetic_clone: SyntheticClone
) -> None:
    """Including target preservation, which an earlier draft ran only once."""
    task_dir, bare = _manifest_with_real_oracle_hash(tmp_path, synthetic_clone)
    report = qualify(load_manifest(task_dir), bare, _fake_env())
    for condition in (
        "base_preservation",
        "base_oracle",
        "target_preservation",
        "target_oracle",
    ):
        assert _condition_of(report, condition)["runs"] == 3


def test_qualify_uses_a_fresh_materialization_per_run(
    tmp_path: Path, synthetic_clone: SyntheticClone, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Repeating inside one workspace measures idempotence, not determinism."""
    task_dir, bare = _manifest_with_real_oracle_hash(tmp_path, synthetic_clone)
    seen: list[Path] = []
    original = materialize

    @contextmanager
    def counting(clone_path: Path, sha: str) -> Iterator[Path]:
        with original(clone_path, sha) as workspace:
            seen.append(workspace)
            yield workspace

    monkeypatch.setattr(workload_module, "materialize", counting)
    qualify(load_manifest(task_dir), bare, _fake_env())
    assert len(seen) == 12
    assert len(set(seen)) == 12


def test_qualify_disqualifies_a_wrong_reason_class(
    tmp_path: Path, synthetic_clone: SyntheticClone
) -> None:
    """The import-typo case: the base is rejected, but not for the declared reason."""
    task_dir, bare = _manifest_with_real_oracle_hash(tmp_path, synthetic_clone)
    text = (task_dir / "manifest.toml").read_text()
    (task_dir / "manifest.toml").write_text(
        text.replace(
            'class           = "collection-error"',
            'class           = "assertion-failure"',
        )
    )
    report = qualify(load_manifest(task_dir), bare, _fake_env())
    assert report["status"] == "disqualified"
    assert report["failed_gate"] == "base_rejection"


def test_qualify_disqualifies_a_missing_expected_symbol(
    tmp_path: Path, synthetic_clone: SyntheticClone
) -> None:
    """The class matched, but not for the reason the manifest pre-registered."""
    task_dir, bare = _manifest_with_real_oracle_hash(tmp_path, synthetic_clone)
    text = (task_dir / "manifest.toml").read_text()
    (task_dir / "manifest.toml").write_text(
        text.replace('missing_symbols = ["mul"]', 'missing_symbols = ["divide"]')
    )
    report = qualify(load_manifest(task_dir), bare, _fake_env())
    assert report["status"] == "disqualified"
    assert report["failed_gate"] == "base_rejection"
    assert "divide" in str(report["detail"])


def test_qualify_disqualifies_an_unstable_suite(
    tmp_path: Path, synthetic_clone: SyntheticClone, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Three runs, identical node-level outcomes required.

    The flaky module keys off a marker kept OUTSIDE the workspace --
    fresh materializations mean anything written inside one is gone by
    the next run, which is exactly the property being tested.
    """
    task_dir, bare = _manifest_with_real_oracle_hash(tmp_path, synthetic_clone)
    marker = tmp_path / "flaky-counter"
    flaky = (
        "import pathlib\n\n\n"
        "def test_flaky():\n"
        f"    marker = pathlib.Path({str(marker)!r})\n"
        "    seen = len(marker.read_text()) if marker.exists() else 0\n"
        "    marker.write_text('x' * (seen + 1))\n"
        "    assert seen % 2 == 0\n"
    )
    original = materialize

    @contextmanager
    def patched(clone_path: Path, sha: str) -> Iterator[Path]:
        with original(clone_path, sha) as workspace:
            if sha == synthetic_clone.base_sha:
                (workspace / "tests" / "test_flaky.py").write_text(flaky)
            yield workspace

    monkeypatch.setattr(workload_module, "materialize", patched)
    report = qualify(load_manifest(task_dir), bare, _fake_env())

    assert report["status"] == "disqualified"
    assert report["failed_gate"] == "stability"


def test_qualify_disqualifies_a_slow_suite(
    tmp_path: Path, synthetic_clone: SyntheticClone
) -> None:
    """The sub-minute threshold is enforced, not merely stated."""
    task_dir, bare = _manifest_with_real_oracle_hash(tmp_path, synthetic_clone)
    report = qualify(load_manifest(task_dir), bare, _fake_env(), max_seconds=0.0)
    assert report["status"] == "disqualified"
    assert report["failed_gate"] == "runtime"


def test_qualify_refuses_a_mismatched_environment(
    tmp_path: Path, synthetic_clone: SyntheticClone
) -> None:
    """A manifest naming a different lock must not be graded against this one."""
    task_dir, bare = _manifest_with_real_oracle_hash(tmp_path, synthetic_clone)
    text = (task_dir / "manifest.toml").read_text()
    (task_dir / "manifest.toml").write_text(
        text.replace('lock_sha256 = "synthetic"', 'lock_sha256 = "deadbeef"')
    )
    report = qualify(load_manifest(task_dir), bare, _fake_env())
    assert report["status"] == "disqualified"
    assert report["failed_gate"] == "environment"


def test_qualification_records_provenance(
    tmp_path: Path, synthetic_clone: SyntheticClone
) -> None:
    """Evidence must name the exact manifest and environment it came from."""
    task_dir, bare = _manifest_with_real_oracle_hash(tmp_path, synthetic_clone)
    report = qualify(load_manifest(task_dir), bare, _fake_env())
    assert report["manifest_sha256"] == sha256_file(task_dir / "manifest.toml")
    assert report["env_python"] == platform.python_version()
    assert report["base_sha"] == synthetic_clone.base_sha
    assert report["target_sha"] == synthetic_clone.target_sha


def test_qualify_checks_the_rejection_fingerprint_on_every_repeat(
    tmp_path: Path, synthetic_clone: SyntheticClone, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The rejection fingerprint is checked on every repeat, not just the first.

    The motivating hazard: a collection error records no nodes, so its
    fingerprint is ("collection-error", 2, ()) and the stability gate
    cannot tell two collection errors apart by cause.

    What this test actually pins down is narrower and worth stating. The
    sabotage here changes the reason class too, so *stability* would also
    catch it -- but it would report `failed_gate == "stability"`, naming
    the wrong problem. With the per-repeat check the run is attributed to
    `base_rejection` and names which repeat diverged. Constructing a true
    same-class-different-cause collision synthetically is awkward, since
    overlay_oracle rewrites the oracle file after any sabotage; that case
    is argued from the fingerprint's shape rather than demonstrated.
    """
    task_dir, bare = _manifest_with_real_oracle_hash(tmp_path, synthetic_clone)
    calls = {"n": 0}
    original = materialize

    @contextmanager
    def sabotage_later_runs(clone_path: Path, sha: str) -> Iterator[Path]:
        with original(clone_path, sha) as workspace:
            if sha == synthetic_clone.base_sha:
                calls["n"] += 1
                # Runs 4 and 5 are base_oracle's second and third; break
                # them for a reason that is NOT the pre-registered symbol.
                if calls["n"] > 4:
                    (workspace / "conftest.py").write_text(
                        "import nonexistent_module_xyz\n"
                    )
            yield workspace

    monkeypatch.setattr(workload_module, "materialize", sabotage_later_runs)
    report = qualify(load_manifest(task_dir), bare, _fake_env())

    assert report["status"] == "disqualified"
    assert report["failed_gate"] == "base_rejection"
    assert "run 2" in str(report["detail"])


def test_qualify_applies_declared_deselects(
    tmp_path: Path, synthetic_clone: SyntheticClone
) -> None:
    """A deselect that is validated and reported but never applied is a lie."""
    task_dir, bare = _manifest_with_real_oracle_hash(tmp_path, synthetic_clone)
    text = (task_dir / "manifest.toml").read_text()
    (task_dir / "manifest.toml").write_text(
        text.replace(
            "deselects = []", 'deselects = ["tests/test_add.py::test_add"]'
        ).replace(
            'deselect_reason = ""',
            'deselect_reason = "exercised by the oracle instead"',
        )
    )
    manifest = load_manifest(task_dir)
    report = qualify(manifest, bare, _fake_env())
    assert report["effective_preservation_command"] == [
        *manifest.preservation_command,
        "--deselect",
        "tests/test_add.py::test_add",
    ]
    # With its only test deselected, the base suite collects nothing.
    assert report["status"] == "disqualified"
    assert report["failed_gate"] == "base_preservation"


def test_qualify_refuses_fewer_than_three_repeats(
    tmp_path: Path, synthetic_clone: SyntheticClone
) -> None:
    """One run makes every task trivially stable, and still says "qualified"."""
    task_dir, bare = _manifest_with_real_oracle_hash(tmp_path, synthetic_clone)
    with pytest.raises(WorkloadError, match="minimum"):
        qualify(load_manifest(task_dir), bare, _fake_env(), repeats=1)


def test_qualify_refuses_a_raised_time_ceiling(
    tmp_path: Path, synthetic_clone: SyntheticClone
) -> None:
    task_dir, bare = _manifest_with_real_oracle_hash(tmp_path, synthetic_clone)
    with pytest.raises(WorkloadError, match="ceiling"):
        qualify(load_manifest(task_dir), bare, _fake_env(), max_seconds=600.0)


def test_qualify_refuses_a_mismatched_interpreter(
    tmp_path: Path, synthetic_clone: SyntheticClone
) -> None:
    """Always compared -- not opt-in behind a flag someone must remember."""
    task_dir, bare = _manifest_with_real_oracle_hash(tmp_path, synthetic_clone)
    text = (task_dir / "manifest.toml").read_text()
    (task_dir / "manifest.toml").write_text(
        text.replace(f'python = "{platform.python_version()}"', 'python = "3.99.0"')
    )
    report = qualify(load_manifest(task_dir), bare, _fake_env())
    assert report["status"] == "disqualified"
    assert report["failed_gate"] == "environment"
    assert "3.99.0" in str(report["detail"])


def test_rejection_matches_when_the_failures_are_exactly_declared(
    tmp_path: Path, synthetic_clone: SyntheticClone
) -> None:
    task_dir = _write_manifest(tmp_path / "tasks" / "s", synthetic_clone)
    text = (task_dir / "manifest.toml").read_text()
    (task_dir / "manifest.toml").write_text(
        text.replace(
            'class           = "collection-error"',
            'class           = "assertion-failure"',
        )
        .replace('missing_symbols = ["mul"]', "missing_symbols = []")
        .replace("failing_nodes   = []", 'failing_nodes   = ["a::one"]')
    )
    manifest = load_manifest(task_dir)
    observed = _suite_result(
        "assertion-failure", {"a::one": "call:failed", "b::two": "call:passed"}
    )
    assert qualification_module._rejection_mismatch(manifest, observed) is None


def test_rejection_refuses_an_undeclared_extra_failure(
    tmp_path: Path, synthetic_clone: SyntheticClone
) -> None:
    """Exact equality, not a subset.

    A base failing the declared node AND an unrelated one is not the
    task the manifest describes; admitting it would let unrelated
    breakage ride along inside a qualified task.
    """
    task_dir = _write_manifest(tmp_path / "tasks" / "s", synthetic_clone)
    text = (task_dir / "manifest.toml").read_text()
    (task_dir / "manifest.toml").write_text(
        text.replace(
            'class           = "collection-error"',
            'class           = "assertion-failure"',
        )
        .replace('missing_symbols = ["mul"]', "missing_symbols = []")
        .replace("failing_nodes   = []", 'failing_nodes   = ["a::one"]')
    )
    manifest = load_manifest(task_dir)
    observed = _suite_result(
        "assertion-failure", {"a::one": "call:failed", "b::two": "call:failed"}
    )
    detail = qualification_module._rejection_mismatch(manifest, observed)
    assert detail is not None
    assert "unexpected=['b::two']" in detail


def test_rejection_refuses_a_symbol_absent_from_the_collection_failure(
    tmp_path: Path, synthetic_clone: SyntheticClone
) -> None:
    """A symbol echoed in stdout proves nothing about what caused the error.

    The declared symbol must appear in the recorded collection failure
    itself, not merely somewhere in pytest's output.
    """
    task_dir = _write_manifest(tmp_path / "tasks" / "s", synthetic_clone)
    manifest = load_manifest(task_dir)  # declares missing_symbols = ["mul"]
    observed = _suite_result(
        "collection-error",
        {},
        collection_errors={
            "tests/test_mul.py": "ImportError: cannot import name 'other'"
        },
        returncode=2,
    )
    detail = qualification_module._rejection_mismatch(manifest, observed)
    assert detail is not None
    assert "mul" in detail


def test_rejection_refuses_missing_symbols_with_no_collection_failure(
    tmp_path: Path, synthetic_clone: SyntheticClone
) -> None:
    task_dir = _write_manifest(tmp_path / "tasks" / "s", synthetic_clone)
    manifest = load_manifest(task_dir)
    observed = _suite_result("collection-error", {}, collection_errors={}, returncode=2)
    detail = qualification_module._rejection_mismatch(manifest, observed)
    assert detail is not None
    assert "no collection failure" in detail


def test_cli_writes_a_qualification_report(
    tmp_path: Path, synthetic_clone: SyntheticClone, monkeypatch: pytest.MonkeyPatch
) -> None:
    task_dir, _ = _manifest_with_real_oracle_hash(tmp_path, synthetic_clone)
    cohort_root = tmp_path / "cohort"
    (cohort_root / "tasks").mkdir(parents=True)
    shutil.copytree(task_dir, cohort_root / "tasks" / "synthetic")
    _write_cohort(cohort_root, synthetic_clone)

    monkeypatch.setattr(
        workload_module, "ensure_cohort_env", lambda *a, **k: _fake_env()
    )
    exit_code = qualify_main(
        [
            "--cohort",
            str(cohort_root / "cohort.toml"),
            "--cache",
            str(tmp_path / "cache"),
        ]
    )
    assert exit_code == 0

    report = json.loads(
        (cohort_root / "tasks" / "synthetic" / "qualification.json").read_text()
    )
    assert report["status"] == "qualified"


def test_cli_records_a_task_whose_manifest_will_not_load(
    tmp_path: Path, synthetic_clone: SyntheticClone, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An unreadable task must not be quieter than a failing one."""
    cohort_root = tmp_path / "cohort"
    (cohort_root / "tasks" / "synthetic").mkdir(parents=True)
    _write_cohort(cohort_root, synthetic_clone)

    monkeypatch.setattr(
        workload_module, "ensure_cohort_env", lambda *a, **k: _fake_env()
    )
    exit_code = qualify_main(
        [
            "--cohort",
            str(cohort_root / "cohort.toml"),
            "--cache",
            str(tmp_path / "cache"),
        ]
    )
    assert exit_code == 1

    report = json.loads(
        (cohort_root / "tasks" / "synthetic" / "qualification.json").read_text()
    )
    assert report["status"] == "disqualified"
    assert report["failed_gate"] == "manifest"


def test_frozen_run_covers_the_included_set_not_the_whole_ladder(
    tmp_path: Path, synthetic_clone: SyntheticClone, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An excluded candidate is excluded because it does not qualify.

    Rerunning it under --frozen would fail the verification run for the
    very reason its exclusion already documents.
    """
    task_dir, _ = _manifest_with_real_oracle_hash(tmp_path, synthetic_clone)
    cohort_root = tmp_path / "cohort"
    (cohort_root / "tasks").mkdir(parents=True)
    shutil.copytree(task_dir, cohort_root / "tasks" / "synthetic")
    (cohort_root / "cohort.toml").write_text(
        f'''name = "synthetic"
upstream = "{synthetic_clone.bare}"
env = "env"
tasks = ["synthetic", "hopeless"]
included = ["synthetic"]

[excluded]
hopeless = "its base passes its own oracle, so there is nothing to fix"
'''
    )
    monkeypatch.setattr(
        workload_module, "ensure_cohort_env", lambda *a, **k: _fake_env()
    )
    exit_code = qualify_main(
        [
            "--cohort",
            str(cohort_root / "cohort.toml"),
            "--cache",
            str(tmp_path / "cache"),
            "--frozen",
        ]
    )
    assert exit_code == 0
    assert not (cohort_root / "tasks" / "hopeless" / "qualification.json").exists()

"""tools/run_cycle7_confirmatory_batch.py: argument parsing and reporting,
the parts this module can exercise without a live Pi/model server.

`run_batch`/`run_one` drive real attempts through `deliver_candidate.main`
against a live cell and are deliberately not unit-tested here -- see that
module's own docstring for how to run it for real.
"""

import pytest

import tools.run_cycle7_confirmatory_batch as batch


def test_the_cell_and_clone_paths_resolve_from_the_repository_not_a_hardcoded_worktree():
    # The original scratchpad script hardcoded an absolute worktree path;
    # this checked-in version must derive everything from its own file
    # location instead (2026-08-11 distribution brief, step 4).
    assert batch.CELL.is_file()
    assert batch.CELL.name == "gemma12b-implementer-v1.toml"
    assert batch.CLONE == batch.REPO / ".workloads" / "svcs.git"


def test_frozen_task_cohort_matches_the_preregistration():
    # A value-level pin: if this tuple ever drifts from the four tasks and
    # base SHAs the pre-registration names, this test names exactly what
    # changed rather than a batch silently running a different cohort.
    assert batch.TASKS == (
        ("flask-extensions", "85827a173fd7b9952abf34a8f198c7d1fb40f43d"),
        ("stringified-annotations", "4b05ab8465f3d9a5ce7d1e40eaf808b0cb92a26c"),
        ("local-pings", "31bc6dfd5d1a570b3b96cfefd878ccc686bde980"),
        ("autowire", "816403b5c1d3b9fff22bd9141fe836221dfe9d9c"),
    )
    assert batch.ARMS == ("brief", "locating-contract")


def test_out_dir_is_required():
    with pytest.raises(SystemExit):
        batch.main([])


def test_task_restricts_to_one_known_task(tmp_path, monkeypatch):
    captured = {}

    def fake_run_batch(tasks, n_per_arm, out_dir):
        captured["tasks"] = tasks
        captured["n_per_arm"] = n_per_arm
        return []

    monkeypatch.setattr(batch, "run_batch", fake_run_batch)
    # Not optional politeness. main() calls bootstrap_cache(), which clones
    # the cohort upstream over the network and runs `uv sync --locked`. Left
    # unstubbed this test does real network I/O on a fresh machine and adds
    # a `uv sync` to every run on a provisioned one. Stubbed with a raiser
    # rather than a no-op so that if the call ever moves somewhere this
    # patch does not cover, the test fails loudly instead of silently going
    # back online.
    monkeypatch.setattr(batch, "bootstrap_cache", lambda: None)
    batch.main(["--out-dir", str(tmp_path), "--task", "autowire", "--n", "2"])

    assert captured["tasks"] == (
        ("autowire", "816403b5c1d3b9fff22bd9141fe836221dfe9d9c"),
    )
    assert captured["n_per_arm"] == 2


def test_bootstrap_cache_is_the_only_network_path_and_main_calls_it_once(
    tmp_path, monkeypatch
):
    """Pin the property the test above depends on.

    That test stubs `bootstrap_cache`; if `main()` ever grew a second
    provisioning call, or reached `ensure_clone` directly, the stub would
    silently stop covering it and the suite would go back to cloning over
    the network. This fails in that case instead.
    """
    calls = []
    monkeypatch.setattr(batch, "run_batch", lambda *a, **k: [])
    monkeypatch.setattr(batch, "bootstrap_cache", lambda: calls.append("bootstrap"))

    def forbidden(*args, **kwargs):
        raise AssertionError(
            "main() reached a provisioning helper outside bootstrap_cache()"
        )

    monkeypatch.setattr(batch, "ensure_clone", forbidden)
    monkeypatch.setattr(batch, "ensure_cohort_env", forbidden)

    batch.main(["--out-dir", str(tmp_path), "--task", "autowire", "--n", "1"])
    assert calls == ["bootstrap"]


def test_an_unknown_task_is_refused_at_the_cli(tmp_path):
    with pytest.raises(SystemExit):
        batch.main(["--out-dir", str(tmp_path), "--task", "not-a-real-task"])


def test_report_flags_the_pooled_verdict_for_a_synthetic_separation(capsys, tmp_path):
    # Synthetic, not live data -- exercises report()'s own arithmetic and
    # verdict wiring against harness.intervals (tested independently in
    # tests/test_intervals.py), not a claim about any real batch.
    tasks = (("flask-extensions", "deadbeef"),)
    results = [
        {
            "task": "flask-extensions",
            "arm": "brief",
            "void": False,
            "outcome": "candidate-created",
            "oracle_passed": i < 2,
        }
        for i in range(8)
    ] + [
        {
            "task": "flask-extensions",
            "arm": "locating-contract",
            "void": False,
            "outcome": "candidate-created",
            "oracle_passed": True,
        }
        for _ in range(8)
    ]
    batch.report(tasks, results, tmp_path)
    out = capsys.readouterr().out
    assert "flask-extensions" in out
    assert "SUPERIORITY (contract > brief)" in out


def test_parser_help_does_not_crash():
    # main() builds its own parser internally; this just guards against a
    # description string that breaks argparse's formatter (RawDescription
    # requires no un-escaped % literals, for one).
    with pytest.raises(SystemExit):
        batch.main(["--help"])

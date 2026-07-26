# harness/runner.py
"""n=4 baseline loop, aggregation, and report generation."""
import dataclasses
import json
import shutil
import statistics
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from harness.session import InvocationProfile, SessionResult, run_session
from harness.telemetry import (
    RunTelemetry, ToolCall,
    detect_overreach, detect_validation_drift, subagent_stats_from,
)
from harness.workspace import prepare_workspace

PI_EVAL_KEEP_WORKSPACES = "PI_EVAL_KEEP_WORKSPACES"


def _pi_version() -> str | None:
    """The pi CLI's own version string, for report provenance -- a schema
    or behavior change between pi versions (e.g. the 0.81.1 -> 0.82.0 skew
    that removed per-event timestamps from --mode json) should be visible
    on the report that used it, not silently assumed. None if pi is not on
    PATH; write_report must not fail just because provenance is missing."""
    path = shutil.which("pi")
    if not path:
        return None
    try:
        proc = subprocess.run(
            [path, "--version"], capture_output=True, text=True, timeout=10,
        )
        return proc.stdout.strip() or None
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Batch durability (Task 8 precondition, grading-path reboot plan). Three
# batches were lost mid-run on 2026-07-24 (killed at run 8/16, between arms,
# and at run 1) because run_baseline only wrote its report after every run
# completed. The artifacts already survive a kill; the aggregation did not.
# Checkpointing to a JSONL file, one line per completed run, closes that --
# a killed batch resumes from its last completed run instead of restarting.
# ---------------------------------------------------------------------------

def _append_checkpoint(path: Path, result: SessionResult) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a") as f:
        f.write(json.dumps(dataclasses.asdict(result)) + "\n")


def _load_checkpoint(path: Path) -> list[SessionResult]:
    """Reconstruct already-completed SessionResults from a checkpoint file.
    Returns [] if the file doesn't exist -- a fresh batch, not an error.

    A process killed mid-write (the exact scenario this mechanism exists
    for) can leave a truncated final line. That must not crash the resume
    it exists to enable -- the whole point is recovering from a kill, not
    failing louder at the recovery step (Rule 8 review, 2026-07-26 --
    Fable). A truncated line means that run never finished, so dropping it
    is the correct semantics: it gets re-run. A malformed line that is NOT
    the last one indicates something is wrong with the checkpoint file
    itself, not just an in-flight write -- that still raises."""
    if not path.is_file():
        return []
    lines = [line.strip() for line in path.read_text().splitlines() if line.strip()]
    results: list[SessionResult] = []
    for i, line in enumerate(lines):
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            if i == len(lines) - 1:
                print(f"  checkpoint: dropping truncated final line in {path} "
                      f"(that run did not finish; it will be re-run)")
                break
            raise
        telemetry_data = data.pop("telemetry")
        telemetry = RunTelemetry(
            prompts=telemetry_data.get("prompts", []),
            tool_calls=[ToolCall(**tc) for tc in telemetry_data.get("tool_calls", [])],
            turns=telemetry_data.get("turns", 0),
        )
        results.append(SessionResult(telemetry=telemetry, **data))
    return results


@dataclass
class BaselineReport:
    phase: str
    n: int
    model: str
    results: list[SessionResult]
    # Amendment 1: every report states its starting state; a report without
    # one is not citable.
    start_state: str = "empty (no seed)"

    @property
    def success_rate(self) -> float:
        return sum(1 for r in self.results if r.is_success) / max(len(self.results), 1)

    @property
    def success_count(self) -> int:
        return sum(1 for r in self.results if r.is_success)

    @property
    def hang_count(self) -> int:
        """Number of runs that succeeded after a prior attempt was killed (exited-with-hang)."""
        return sum(1 for r in self.results if r.outcome == "exited-with-hang")

    @property
    def mean_wall_time_s(self) -> float | None:
        """Mean task duration (artifact first-to-terminal timestamp) for
        success-eligible outcomes (exited, exited-with-hang). Timeout and
        no-delegation runs are excluded — they have no meaningful task duration."""
        times = [r.task_duration_s for r in self.results
                 if r.outcome in ("exited", "exited-with-hang") and r.task_duration_s is not None]
        return statistics.mean(times) if times else None

    @property
    def mean_process_wall_time_s(self) -> float | None:
        """Fallback duration metric: harness-side subprocess wall time (this
        process's own clock around the pi invocation), for success-eligible
        outcomes. Used when task_duration_s cannot be computed from the
        artifact — as of pi 0.82.0, --mode json events carry a top-level
        "timestamp" only on the initial "session" event, so no per-event
        duration is recoverable from the stream. Unlike task_duration_s this
        includes any dead time from a killed-then-retried attempt, so it is
        reported separately and labeled, never silently substituted."""
        times = [r.wall_time_s for r in self.results
                 if r.outcome in ("exited", "exited-with-hang") and r.wall_time_s is not None]
        return statistics.mean(times) if times else None

    @property
    def mean_turns(self) -> float | None:
        turns = [r.telemetry.turns for r in self.results if r.telemetry and r.telemetry.turns > 0]
        return statistics.mean(turns) if turns else None

    @property
    def phase_num(self) -> int | None:
        """Extract phase number from phase name (e.g. 'Phase 2 — Complaints')."""
        import re
        m = re.search(r'Phase (\d+)', self.phase)
        return int(m.group(1)) if m else None

    @property
    def overreach_count(self) -> int:
        """Runs where the implementer created files from wrong phases."""
        pn = self.phase_num
        if pn is None:
            return 0
        return sum(1 for r in self.results
                   if detect_overreach(r.changed_files, pn))

    @property
    def validation_drift_count(self) -> int:
        """Runs where the implementer ran a different pytest command than
        the packet-specified `uv run pytest -q`."""
        return sum(1 for r in self.results
                   if detect_validation_drift(r.artifact_path))

    @property
    def drift_count(self) -> int:
        """Runs with any form of drift (overreach OR validation drift)."""
        pn = self.phase_num
        if pn is None:
            return 0
        return sum(1 for r in self.results
                   if (detect_overreach(r.changed_files, pn)
                       or detect_validation_drift(r.artifact_path)))

    # -- Task 7: standing behavioral instrumentation (Amendment 2) --------

    @property
    def inherited_write_attempt_count(self) -> int:
        """Runs where the model attempted a whole-file `write` on at least
        one file it inherited from the phase seed (always 0 for an
        unseeded phase-1 batch)."""
        return sum(1 for r in self.results if r.inherited_write_attempts)

    @property
    def shared_file_replace_count(self) -> int:
        """Runs classified 'replace' -- an inherited file was targeted by a
        whole-file `write` attempt, blocked or not. See
        InheritedFileActivity.classification for the scope of the
        2026-07-24 forensics report's 8/8 correlation, which was measured
        on the inherited test suite specifically, not this run-level any-
        inherited-file classification (Rule 8 review, 2026-07-26)."""
        return sum(1 for r in self.results if r.shared_file_classification == "replace")

    @property
    def shared_file_extend_count(self) -> int:
        """Runs classified 'extend' -- inherited files were touched only
        via incremental `edit`, never whole-file `write`."""
        return sum(1 for r in self.results if r.shared_file_classification == "extend")

    @property
    def false_self_report_count(self) -> int:
        """Runs where the model's own suite passed but the harness's
        independent acceptance grade disagreed (Amendment 2's motivating
        incident)."""
        return sum(1 for r in self.results if r.false_self_report)


def run_baseline(
    phase_prompt: str,
    app_source: str | Path,
    model: str,
    profile: InvocationProfile,
    n: int = 4,
    timeout: int = 300,
    phase_name: str | None = None,
    research_dir: Path | None = None,
    seed: str | Path | None = None,
    acceptance_suite: str | Path | None = None,
    checkpoint_path: str | Path | None = None,
) -> BaselineReport:
    """Run n independent sessions against one phase, return aggregated report.

    Each run gets a fresh workspace. Runs are sequential to avoid model
    contention. Timeout + token limits apply per run.
    Workspaces are cleaned up unless PI_EVAL_KEEP_WORKSPACES is set.

    phase_name is used in the report heading. If None, attempts to extract
    from the prompt text (first ## Phase line).

    checkpoint_path, when given, persists each completed SessionResult to a
    JSONL file as it finishes. A batch killed mid-run (agent-session
    teardown reaping child processes; setsid unavailable on macOS -- both
    documented causes of three lost batches on 2026-07-24) resumes from its
    last completed run on the next call with the same checkpoint_path,
    instead of restarting from run 1. The caller is responsible for using a
    checkpoint_path unique to this batch -- reusing one across a genuinely
    different batch (different model, phase, or seed) would silently
    resume with the wrong runs.
    """
    import os

    app_source = Path(app_source).resolve()
    checkpoint = Path(checkpoint_path) if checkpoint_path is not None else None
    results: list[SessionResult] = _load_checkpoint(checkpoint) if checkpoint is not None else []
    if len(results) > n:
        # Cheap guard (Rule 8 review, 2026-07-26 -- Fable): the caller is
        # responsible for using a checkpoint_path unique to this batch, but
        # this mechanism is meant to run unsupervised overnight -- silently
        # producing a report with more results than n (negative "untouched"
        # counts, a wrong n in every ratio) on a stale or mismatched
        # checkpoint is exactly the kind of fiction this project's evidence
        # policy exists to prevent. Loud failure, not a guess.
        raise ValueError(
            f"checkpoint at {checkpoint} has {len(results)} results but n={n} "
            f"was requested -- this looks like a checkpoint from a different "
            f"batch. Use a checkpoint_path unique to this batch."
        )
    start = len(results) + 1
    if start > 1:
        print(f"  resuming from checkpoint: {len(results)}/{n} runs already complete")
    keep = bool(os.environ.get(PI_EVAL_KEEP_WORKSPACES))

    for i in range(start, n + 1):
        print(f"  run {i}/{n}...", end=" ", flush=True)
        ws_path, pristine_hash = prepare_workspace(app_source, seed=seed)
        try:
            result = run_session(
                ws_path, phase_prompt, model,
                pristine_hash=pristine_hash,
                profile=profile,
                timeout=timeout,
                research_dir=research_dir,
                acceptance_suite=acceptance_suite,
                seed=seed,
            )
            print(f"{result.outcome} ({result.wall_time_s:.0f}s, {result.telemetry.turns}turns, {'PASS' if result.tests_pass else 'FAIL'})")
            results.append(result)
            if checkpoint is not None:
                _append_checkpoint(checkpoint, result)
        finally:
            if not keep:
                shutil.rmtree(ws_path.parent, ignore_errors=True)

    # Use provided phase_name or extract from prompt.
    if phase_name is None:
        phase_name = "Unknown"
        for line in phase_prompt.splitlines():
            if line.startswith("## Phase ") and not line.startswith("### "):
                phase_name = line[3:].strip()
                break

    if seed is not None:
        seed_path = Path(seed).resolve()
        repo_root = Path(__file__).resolve().parent.parent
        try:
            label = str(seed_path.relative_to(repo_root))
        except ValueError:
            label = str(seed_path)
        start_state = f"seeded: {label}"
    else:
        start_state = "empty (no seed)"

    return BaselineReport(
        phase=phase_name,
        n=n,
        model=model,
        results=results,
        start_state=start_state,
    )


def write_report(report: BaselineReport, output_path: str | Path) -> None:
    """Write a markdown evidence report from a BaselineReport."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    lines = [
        f"# Baseline: {report.phase}",
        f"",
        f"**Date:** {today}",
        f"**Model:** {report.model}",
        f"**Start state:** {report.start_state}",
    ]
    version = _pi_version()
    if version is not None:
        lines.append(f"**pi version:** `{version}`")
    lines.extend([
        f"**Runs:** n={report.n}",
        f"**Success rate:** {report.success_count}/{report.n} ({report.success_rate:.0%})",
        f"",
    ])

    if report.mean_wall_time_s is not None:
        lines.append(f"**Mean task duration:** {report.mean_wall_time_s:.0f}s "
                     f"(over success-eligible runs; timeout/no-delegation excluded)")
    elif report.mean_process_wall_time_s is not None:
        lines.append(f"**Mean process wall time:** {report.mean_process_wall_time_s:.0f}s "
                     f"(harness-side subprocess timing, not artifact task duration — "
                     f"this pi version's --mode json stream has no per-event timestamps "
                     f"to compute the latter; over success-eligible runs, timeout/"
                     f"no-delegation excluded)")
    if report.mean_turns is not None:
        lines.append(f"**Mean turns:** {report.mean_turns:.1f}")
    if report.hang_count > 0:
        lines.append(f"**Hang incidence:** {report.hang_count}/{report.n} runs "
                     f"required a retry after a killed attempt (exited-with-hang)")
    if report.overreach_count > 0 or report.validation_drift_count > 0:
        parts = []
        if report.overreach_count > 0:
            parts.append(f"overreach={report.overreach_count}")
        if report.validation_drift_count > 0:
            parts.append(f"validation-drift={report.validation_drift_count}")
        lines.append(f"**Drift incidence:** {report.drift_count}/{report.n} runs "
                     f"({' ,'.join(parts)})")
    # No "Oracle validated" line: write_report never runs tests/test_oracle.py
    # itself, so it cannot honestly claim the oracle is green. That claim is
    # made separately, by whoever runs the oracle, and cited in the commit or
    # prose that publishes this report — never fabricated here (closes F4).
    lines.append("")
    lines.append("| # | Outcome | Success | Turns | Wall Time | Changed Files | Artifact |")
    lines.append("|---|---------|---------|-------|-----------|---------------|----------|")

    for i, r in enumerate(report.results, 1):
        success_icon = "✅" if r.is_success else "❌"
        turns = str(r.telemetry.turns) if r.telemetry else "—"
        wt = f"{r.wall_time_s:.0f}s"
        files = ", ".join(r.changed_files[:3]) or "—"
        if len(r.changed_files) > 3:
            files += f" (+{len(r.changed_files) - 3})"
        lines.append(
            f"| {i} | {r.outcome} | {success_icon} | {turns} | {wt} | {files} | "
            f"`{r.run_id}` |"
        )

    lines.append("")
    # Session IDs are cited as plain text, never linked: transcripts are
    # gitignored, so links resolve locally and 404 on the published site.
    # See policies/evidence.md#artifact-retention.
    lines.append(
        "*Session transcripts are retained locally at "
        "`research/sessions/<id>.jsonl` and are not published — see "
        "[artifact retention](../../superpowers/policies/evidence.md#artifact-retention).*"
    )
    lines.append("")
    lines.append("## Subagent delegation metrics")
    lines.append("")

    # Collect subagent stats from each run's artifact.
    total_invocations = 0
    total_packet_size = 0
    runs_with_delegation = 0
    per_run_lines: list[str] = []
    for i, r in enumerate(report.results, 1):
        stats = subagent_stats_from(r.artifact_path)
        if stats.invocations > 0:
            runs_with_delegation += 1
            total_invocations += stats.invocations
            total_packet_size += stats.packet_size_total
            per_run_lines.append(
                f"| {i} | {stats.invocations} | {stats.packet_size_total:,} |"
            )
        else:
            per_run_lines.append(f"| {i} | — | — |")

    if runs_with_delegation > 0:
        lines.append("| # | Subagent calls | Packet size (bytes) |")
        lines.append("|---|---------------|---------------------|")
        lines.extend(per_run_lines)
        mean_invocations = total_invocations / runs_with_delegation
        mean_packet = total_packet_size / runs_with_delegation
        lines.append(
            f"| **Agg** | μ={mean_invocations:.1f} "
            f"(in {runs_with_delegation}/{report.n} runs) | "
            f"μ={mean_packet:,.0f} |"
        )
        lines.append("")
        lines.append("*Packet fidelity (verbatim literal matching) and implementer self-report")
        lines.append("vs harness verdict agreement are deferred to a future harness iteration.*")
    else:
        lines.append("No subagent delegations detected in any run.")

    lines.append("")
    lines.append("## Behavioral instrumentation")
    lines.append("")
    no_seed_note = "" if report.start_state.startswith("seeded") else " (no seed -- not applicable)"
    lines.append(
        f"**Inherited-file write attempts:** {report.inherited_write_attempt_count}/{report.n} "
        f"runs{no_seed_note}"
    )
    lines.append(
        f"**Shared-file replace-vs-extend:** replace={report.shared_file_replace_count} "
        f"extend={report.shared_file_extend_count} "
        f"untouched={report.n - report.shared_file_replace_count - report.shared_file_extend_count}"
        f"{no_seed_note}"
    )
    lines.append(
        f"**False self-report:** {report.false_self_report_count}/{report.n} runs "
        f"(model's own suite passed; harness acceptance disagreed)"
    )

    lines.append("")
    lines.append("## Evidence tier")
    lines.append("")
    has_subagent = runs_with_delegation > 0
    has_timing_data = report.mean_wall_time_s is not None or report.mean_process_wall_time_s is not None

    # Outcome mix — a real fact from this run, not template text, so the
    # tier lines below can be checked against it rather than taken on faith.
    outcome_counts: dict[str, int] = {}
    for r in report.results:
        outcome_counts[r.outcome] = outcome_counts.get(r.outcome, 0) + 1
    mix = ", ".join(f"{count} {outcome}" for outcome, count in sorted(outcome_counts.items()))
    lines.append(f"- **Outcome mix:** {mix or 'no runs recorded'}.")

    if report.n > 0 and len(report.results) > 0:
        lines.append(
            f"- **Success rate:** artifact-backed — n={report.n} dated session files "
            f"(GREEN per [evidence policy](../../superpowers/policies/evidence.md))."
        )
    else:
        lines.append("- **Success rate:** no runs recorded — not assessable.")
    if has_subagent:
        lines.append(
            f"- **Delegation metrics:** artifact-backed — subagent call counts "
            f"and packet sizes extracted from parent JSONLs (GREEN)."
        )
    if has_timing_data:
        lines.append(
            f"- **Timing / turns:** real but noisy — n={report.n}, single-model, "
            f"single-provider (YELLOW). Compare deltas at n=4 with caution."
        )
    else:
        lines.append(
            "- **Timing / turns:** no success-eligible runs — no timing data to report."
        )
    if report.n <= 8:
        lines.append(
            f"- **Statistical note:** n={report.n} — per-run success-rate deltas "
            f"of ±1 run are within noise at this sample size. "
            f"Cite structural claims, not small-sample tuning deltas."
        )

    output_path.write_text("\n".join(lines) + "\n")

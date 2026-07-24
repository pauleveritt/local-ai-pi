# harness/runner.py
"""n=8 baseline loop, aggregation, and report generation."""
import statistics
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from harness.session import InvocationProfile, SessionResult, run_session
from harness.telemetry import subagent_stats_from
from harness.workspace import prepare_workspace

PI_EVAL_KEEP_WORKSPACES = "PI_EVAL_KEEP_WORKSPACES"


@dataclass
class BaselineReport:
    phase: str
    n: int
    model: str
    results: list[SessionResult]

    @property
    def success_rate(self) -> float:
        return sum(1 for r in self.results if r.is_success) / max(len(self.results), 1)

    @property
    def success_count(self) -> int:
        return sum(1 for r in self.results if r.is_success)

    @property
    def mean_wall_time_s(self) -> float | None:
        times = [r.wall_time_s for r in self.results if r.outcome == "exited"]
        return statistics.mean(times) if times else None

    @property
    def mean_turns(self) -> float | None:
        turns = [r.telemetry.turns for r in self.results if r.telemetry and r.telemetry.turns > 0]
        return statistics.mean(turns) if turns else None


def run_baseline(
    phase_prompt: str,
    app_source: str | Path,
    model: str,
    profile: InvocationProfile,
    n: int = 8,
    timeout: int = 300,
    phase_name: str | None = None,
    research_dir: Path | None = None,
) -> BaselineReport:
    """Run n independent sessions against one phase, return aggregated report.

    Each run gets a fresh workspace. Runs are sequential to avoid model
    contention. Timeout + token limits apply per run.
    Workspaces are cleaned up unless PI_EVAL_KEEP_WORKSPACES is set.

    phase_name is used in the report heading. If None, attempts to extract
    from the prompt text (first ## Phase line).
    """
    import os

    app_source = Path(app_source).resolve()
    results: list[SessionResult] = []
    keep = bool(os.environ.get(PI_EVAL_KEEP_WORKSPACES))

    for i in range(1, n + 1):
        ws_path, pristine_hash = prepare_workspace(app_source)
        try:
            result = run_session(
                ws_path, phase_prompt, model,
                pristine_hash=pristine_hash,
                profile=profile,
                timeout=timeout,
                research_dir=research_dir,
            )
            results.append(result)
        finally:
            if not keep:
                import shutil
                shutil.rmtree(ws_path.parent, ignore_errors=True)

    # Use provided phase_name or extract from prompt.
    if phase_name is None:
        phase_name = "Unknown"
        for line in phase_prompt.splitlines():
            if line.startswith("## Phase ") and not line.startswith("### "):
                phase_name = line[3:].strip()
                break

    return BaselineReport(
        phase=phase_name,
        n=n,
        model=model,
        results=results,
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
        f"**Runs:** n={report.n}",
        f"**Success rate:** {report.success_count}/{report.n} ({report.success_rate:.0%})",
        f"",
    ]

    if report.mean_wall_time_s is not None:
        lines.append(f"**Mean wall time:** {report.mean_wall_time_s:.0f}s")
    if report.mean_turns is not None:
        lines.append(f"**Mean turns:** {report.mean_turns:.1f}")

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
            f"[{r.run_id}.jsonl](sessions/{r.run_id}.jsonl) |"
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
    lines.append("## Evidence tier")
    lines.append("")
    has_subagent = runs_with_delegation > 0
    lines.append(
        f"- **Success rate:** artifact-backed — n={report.n} dated session files "
        f"(GREEN per [evidence policy](../superpowers/policies/evidence.md))."
    )
    if has_subagent:
        lines.append(
            f"- **Delegation metrics:** artifact-backed — subagent call counts "
            f"and packet sizes extracted from parent JSONLs (GREEN)."
        )
    lines.append(
        f"- **Timing / turns:** real but noisy — n={report.n}, single-model, "
        f"single-provider (YELLOW). Compare deltas at n=8 with caution."
    )
    if report.n <= 8:
        lines.append(
            f"- **Statistical note:** n={report.n} — per-run success-rate deltas "
            f"of ±1 run are within noise (Fisher exact p≈1.0 at 3/8 vs 4/8). "
            f"Cite the structural claim (0/8 → 3–4/8), not the tuning delta."
        )

    output_path.write_text("\n".join(lines) + "\n")

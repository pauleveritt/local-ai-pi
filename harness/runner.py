# harness/runner.py
"""n=8 baseline loop, aggregation, and report generation."""
import statistics
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from harness.session import InvocationProfile, SessionResult, run_session
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
    lines.append("## Evidence tier")
    lines.append("")
    lines.append(f"- **Success rate:** GREEN — n={report.n} artifact-backed runs")
    lines.append(f"- **Timing / turns:** YELLOW — real but noisy (n={report.n}, single-model, single-provider)")

    output_path.write_text("\n".join(lines) + "\n")

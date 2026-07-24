(part2c-smoking-gun)=

# The Smoking Gun

You have a telemetry reader. You have an eval session. Now run it 4 times
and see whether the unsteered SLM can build Phase 1 of the AgentClinic
complaints board.

This chapter produces the first dated evidence report in
`docs/superpowers/research/`. Every claim later in the course — "guardrail X
reduced failures by Y" — links back to what you establish here.

## Why n=4?

A small local model is non-deterministic. One run might succeed by luck.
One run might fail for a transient reason. You need enough runs to see a
real signal. Four is a practical compromise: enough to surface the primary failure
modes, not so many that each baseline takes hours. At n=8 you get better
statistics but pay double the time — for this course's teaching goals,
n=4 is sufficient.

At roughly 30-90 seconds per run (for a 12B model on Apple Silicon), n=4
completes in 2-7 minutes.

## The runner

`run_baseline()` loops n times with fresh workspaces, aggregates the results,
and returns a `BaselineReport`:

```python
def run_baseline(phase_prompt, app_source, model, n=4, timeout=300):
    results: list[SessionResult] = []
    keep = bool(os.environ.get("PI_EVAL_KEEP_WORKSPACES"))

    for i in range(1, n + 1):
        ws_path, _ = prepare_workspace(app_source)
        try:
            result = run_session(ws_path, phase_prompt, model, timeout=timeout)
            results.append(result)
        finally:
            if not keep:
                shutil.rmtree(ws_path.parent, ignore_errors=True)

    return BaselineReport(phase=phase_name, n=n, results=results)
```

Set `PI_EVAL_KEEP_WORKSPACES=1` to leave failed workspaces in place for
debugging.

## Running the baseline

```bash
uv run python -c "
from harness.runner import run_baseline, write_report
from pathlib import Path

app_source = Path('examples/agentclinic')
roadmap = (app_source / 'specs' / 'roadmap.md').read_text()

# Extract Phase 1 prompt verbatim from the roadmap
lines = roadmap.splitlines()
start = next(i for i, l in enumerate(lines) if l.startswith('## Phase 1 '))
body = []
for line in lines[start+1:]:
    if line.startswith('## Phase '):
        break
    body.append(line)
prompt = '\n'.join(body).strip()

report = run_baseline(
    prompt, app_source,
    'omlx/gemma-4-12B-it-MLX-8bit',
    n=4, timeout=300,
)
write_report(report, f'docs/superpowers/research/$(date +%Y-%m-%d)-baseline-phase-1.md')
print(f'Success: {report.success_count}/{report.n} ({report.success_rate:.0%})')
"
```

## The report

Here is a sample report with n=3 for illustration — your actual report will
have n=4:

```markdown
# Baseline: Phase 1 — Home Page

**Date:** 2026-07-24
**Model:** omlx/gemma-4-12B-it-MLX-8bit
**Runs:** n=3
**Success rate:** 1/3 (33%)

**Mean wall time:** 45s
**Mean turns:** 8.0

| # | Outcome | Success | Turns | Wall Time | Changed Files | Artifact |
|---|---------|---------|-------|-----------|---------------|----------|
| 1 | exited  | ✅       | 8     | 42s       | app.py, templates/base.html, templates/home.html, tests/test_app.py | [a1b2c3.jsonl](sessions/a1b2c3.jsonl) |
| 2 | exited  | ❌       | 12    | 67s       | app.py, templates/base.html | [d4e5f6.jsonl](sessions/d4e5f6.jsonl) |
| 3 | timeout | ❌       | —     | 300s      | — | [g7h8i9.jsonl](sessions/g7h8i9.jsonl) |

## Evidence tier

- **Success rate:** GREEN — n=4 artifact-backed runs
- **Timing / turns:** YELLOW — real but noisy (n=4, single-model, single-provider)
```

## What the numbers mean

**Success rate below 50%** is the smoking gun: the unsteered SLM cannot
reliably complete this phase. Parts III and IV of the course will measure how
much steering and guardrails improve this number.

**All timeouts, all test failures** — something is broken. Check that oMLX is
running, the model is loaded, and the prompt is correct.

**All successes** — the phase is too easy for this model. The runner
automatically escalates to Phase 2, then Phase 3, until a failure surface
appears. If all three phases pass, that is itself a finding — record it
honestly and consider a harder task.

## If the SLM passes Phase 1

The runner tries each phase in order and stops at the first phase where
success rate drops below 50%:

```python
for phase_num in (1, 2, 3):
    prompt = extract_phase(roadmap, phase_num)
    report = run_baseline(prompt, app_source, model, n=4)
    write_report(report, f"research/{today}-baseline-phase-{phase_num}.md")
    if report.success_rate < 0.5:
        print(f"Smoking gun found at Phase {phase_num}!")
        break
```

This prevents the course premise from resting on a phase that might be too
simple for the SLM to fail. The report the course cites should show the
model struggling.

## What you built

A repeatable measurement loop. `harness/runner.py` runs any phase n=4 times,
aggregates the results, and writes a dated evidence report. You now have the
tool that Parts III and IV will use to prove every improvement they claim.

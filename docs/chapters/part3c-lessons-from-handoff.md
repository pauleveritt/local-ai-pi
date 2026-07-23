(part3c-lessons-from-handoff)=

# Lessons from the Handoff

Chapter 2 gave you a parent+implementer shape and a measured baseline. Now you'll
examine what went wrong, tune the packet and prompts, and re-measure. This is
where "structure beats strings" stops being a principle and becomes a practice.

## What the first baseline revealed

The SP2 baseline (Chapter 2) produced a per-phase success rate. The session
JSONLs tell a richer story than the pass/fail columns. For each run, examine:

1. **Was the subagent called at all?** Check for `tool_execution_end` events
   with `toolName == "subagent"`. A `no-delegation` outcome means the parent
   never delegated — it either built the code itself (SP1 rerun) or gave up.

2. **Did the parent construct a valid packet?** Look at the `task` field in the
   subagent call. Does it contain the acceptance strings verbatim? The
   allowed-files list? Or did the parent paraphrase?

3. **Did the implementer write code?** Check `changed_files`. An empty list
   means the implementer received the packet but produced nothing — possibly
   confused, possibly the packet was too vague.

4. **Did the implementer's self-report match the harness verdict?** The
   implementer might claim success while the harness shows test failures.
   Disagreement is a metric — it means the implementer either didn't run
   validation or reported dishonestly.

```bash
# Quick analysis of a session
python3 -c "
import json, sys
path = sys.argv[1]
subagent_calls = 0
for line in open(path):
    ev = json.loads(line.strip())
    if ev.get('toolName') == 'subagent':
        subagent_calls += 1
        if ev.get('type') == 'tool_execution_start':
            task = str(ev.get('args', {}).get('task', ''))
            print(f'Packet size: {len(task)} chars')
            print(f'Has acceptance strings: {\"verbtim text\" in task}')
print(f'Subagent calls: {subagent_calls}')
" docs/superpowers/research/sessions/<run-id>.jsonl
```

## Common failure patterns

Based on the SP2 baseline — and consistent with LESSONS #4's findings about
handoff drift — expect these patterns:

| Pattern | Symptom | Root cause |
|---------|---------|------------|
| **Paraphrase drift** | Packet is a summary, not verbatim | Parent rewrote the phase in its own words; acceptance strings lost |
| **Over-narrowing** | Packet only includes 1-2 checklist items | Parent "simplified" the phase, omitting deliverables |
| **Implementer overreach** | Implementer built Phase 2-3 features during Phase 1 | Specialist prompt too permissive; "do not redesign" wasn't strong enough |
| **Validation skipped** | Tests fail but implementer reported success | Implementer didn't run `uv run pytest` before reporting |
| **No delegation** | Parent built everything itself | Parent ignored the orchestrator prompt entirely |

## Tuning the packet format

Each failure pattern suggests a specific fix. The boundary with Part IV is
important here: **prompt and packet tuning only** — no mechanism-level guardrails
(turn cap, output cap, path guard). Those come later.

### If the parent paraphrases (packet drift)

Tighten the orchestrator prompt. Add explicit "do not paraphrase" language and
an example of a good vs. bad packet. The `task` field must be copy-pasted from
the roadmap:

```markdown
## Task
- Create `app.py` with the FastAPI application instance
- Create `templates/` directory
...
```

Not:

```
## Task
Build a FastAPI app with a home page
```

### If the packet is too narrow

Add a completeness check to the orchestrator prompt: "Verify your packet
contains every checklist item from the phase before dispatching."

### If the implementer overreaches

Strengthen the implementer specialist prompt. Add:

```
6. **Build only the phase specified.** If the packet says Phase 1, do not
   create Phase 2 or Phase 3 files (no models.py, no complaints.html).
   The allowed files list tells you what to touch.
```

### If validation is skipped

Make validation explicit in the implementer prompt:

```
After writing all files, you MUST run the validation command. Report the
exact command you ran and its output. If tests fail, you MUST fix the
code and re-run validation before reporting completion.
```

## Re-measuring

After tuning, re-run the baseline. The table below compares three data points:

```{eval-rst}
.. list-table:: Handoff Tuning Results
   :header-rows: 1
   :widths: 20 15 15 15 35

   * - Baseline
     - Success Rate
     - Mean Turns
     - Mean Wall Time
     - Subagent Calls (mean)
   * - SP1 (unsteered)
     - 0/8 (0%)
     - 6.4
     - 45s
     - N/A (no delegation)
   * - SP2 Ch2 (pre-tuning)
     - ?/8
     - ?
     - ?
     - ?
   * - SP2 Ch3 (post-tuning)
     - ?/8
     - ?
     - ?
     - ?
```

The delta between pre- and post-tuning is what "structure beats strings" looks
like in practice. The prompt got tighter, the packet got more structured, and the
implementer got clearer boundaries — no mechanism change, just better
specification. Each row links to a dated artifact in
``docs/superpowers/research/``. The prompt got tighter, the packet got more structured, and the
implementer got clearer boundaries — no mechanism change, just better
specification.

```{note}
If a failure pattern persists after prompt tuning, it becomes the motivating
evidence for the corresponding Part IV mechanism. "Implementer still overreaches
after prompt tightening" → path guard. "Still runs infinite loops" → turn cap or
repeat breaker. The pattern is always: measure the failure, try the lightest fix
first, escalate to mechanism only when needed.
```

## What you built

A repeatable process: measure → examine failure patterns → tune → re-measure.
This is the method Part IV inherits. Every guardrail in Part IV will be justified
by the same kind of evidence you just produced — a dated report, a before/after
comparison, and a specific lesson addressed.

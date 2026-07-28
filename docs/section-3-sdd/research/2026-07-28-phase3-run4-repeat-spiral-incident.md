# Repeat-Spiral Incident: `follow_redirects` Trap Under Delegation

**Date:** 2026-07-28
**Status:** observed once, single run (Phase 3 steered batch, run 4/16). Recorded
as a finding; not yet weighed against the full n=16 or the unsteered baseline's
own hang rate.
**Context:** Section III steered batch, Phase 3 (rewritten spec), run 4/16 —
checkpoint run_id `0e8057a50162`, outcome `exited-with-hang` at the 900s
timeout, 2 parent turns.

## What happened

The delegated implementer wrote correct application code — a real 303
redirect via `RedirectResponse(url="/complaints", status_code=303)`. To
verify it, it abandoned the packet's specified validation command
(`uv run pytest -q`) after one initial run and switched to a self-invented
ad-hoc check:

```python
python3 -c "from fastapi.testclient import TestClient; from app import app; \
client = TestClient(app); \
response = client.post('/complaints', data={'agent_name': 'TestAgent', 'text': 'Test complaint.'}); \
print(f'Status: {response.status_code}, Location: {response.headers.get(\"location\")}')"
```

`TestClient` follows redirects by default. So this check always printed
`Status: 200, Location: None` — not because the 303 was missing, but because
the client silently followed it before the implementer could observe it. This
is exactly the `follow_redirects` trap `lessons.md` #13 already names.

The implementer read the (correct, unchanged) result as evidence its code was
wrong, then rewrote **byte-for-byte identical** `app.py` content and re-ran
the identical check. This cycle repeated at least 15 times, each iteration
producing the same misleading result, until the 900s harness timeout killed
the run. It never returned to `uv run pytest -q` — the packet's actual
validation command — after the first attempt.

Two distinct, compounding failures, not one:

1. **The trap itself** (`lessons.md` #13) — a testing methodology that can't
   see the thing it's checking for.
2. **Validation-command drift** (this project's documented gap #2/#4) — the
   implementer substituted its own check for the packet's specified one, and
   never recovered.

## How this was reconstructed

The child's own session JSONL is not captured (standing telemetry gap #1 —
see the roadmap backlog). This reconstruction instead came from the parent's
`tool_execution_update` events on the `subagent` tool call: the shipped
extension periodically snapshots the child's in-progress message history into
`partialResult.details.results[0].messages`, and those snapshots survived in
the parent's own artifact even though the call never returned. That's a
partial mitigation for gap #1, not a fix — it only works because the run
hung long enough to accumulate many snapshots, and it required manually
walking the parent artifact rather than reading a first-class child log.

## Artifacts

- Parent session: `docs/section-3-sdd/research/sessions/0e8057a50162.jsonl`
  (230 lines; retained locally, not published — see
  [artifact retention](../../superpowers/policies/evidence.md#artifact-retention)).
- Checkpoint entry 4 of `.pi-eval-checkpoints/steered-tuned-phase3-n16.jsonl`
  (gitignored, local only).

## Why it matters

Directly relevant to Section IV's speed/reliability candidate (hang
incidence): this is a concrete, traced instance of that aggregate failure
mode, not just a count. It also suggests a specific, narrow mechanism
candidate — detecting or preventing validation-command drift, or catching the
`follow_redirects` trap structurally — that's sharper than a generic turn cap
would be, since the implementer wasn't thrashing broadly, it was stuck
re-deriving the same wrong conclusion from the same flawed check.

## Disposition

One run out of the pre-registered n=16. Folds into the aggregate Phase 3
report once that batch completes (in progress as of this writing). Not, by
itself, evidence that delegation *causes* this trap more often than
unsteered — that requires comparing Phase 3's full steered hang incidence
against the unsteered rewritten-spec baseline's own 6/16 hang rate, which is
what the eventual Phase 3 report and Claim 2 disposition owe.

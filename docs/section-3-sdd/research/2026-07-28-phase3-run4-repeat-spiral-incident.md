# Repeat-Spiral Incident: `follow_redirects` Trap Under Delegation

**Date:** 2026-07-28 (updated after the full n=16 batch completed)
**Status:** traced in all four hangs of the Phase 3 steered batch — **not an
isolated incident, the dominant/exclusive cause of every hang in this batch.**
**Context:** Section III steered batch, Phase 3 (rewritten spec), n=16.
Hang incidence 4/16 (runs 4, 8, 9, 11). All four traced; all four share the
identical root cause.

## What happened, in every one of the four hangs

The delegated implementer writes correct application code — a real 303
redirect via `RedirectResponse(url="/complaints", status_code=303)`. To
verify it, it probes with a self-invented `TestClient` check instead of (or,
in one case, in addition to) the packet's specified `uv run pytest -q`:

```python
python3 -c "from fastapi.testclient import TestClient; from app import app; \
client = TestClient(app); \
response = client.post('/complaints', data={'agent_name': 'TestAgent', 'text': 'Test complaint.'}); \
print(f'Status: {response.status_code}, Location: {response.headers.get(\"location\")}')"
```

`TestClient` follows redirects by default. The check always prints `Status:
200, Location: None` — not because the 303 is missing, but because the
client silently follows it before the implementer can observe it. This is
exactly the `follow_redirects` trap `lessons.md` #13 already names.

Each run reads the (correct, unchanged) result as evidence its own code is
wrong, then re-writes effectively identical `app.py` content and re-probes.
The loop repeats until the 900s timeout kills it. The four runs vary in
texture but not in cause:

- **Run 4** (`0e8057a50162`, 2 parent turns): abandons `uv run pytest -q`
  after one attempt, loops on the ad-hoc probe ~15+ times.
- **Run 8** (`1549ed13a963`, 31 parent turns — the longest struggle): keeps
  running `uv run pytest -q` between attempts, and at one point **correctly
  self-diagnoses the trap** — its own bash-command comment reads *"It's
  always 200. This is because Starlette's TestClient follows redirects by
  default."* — yet still cannot escape the loop, because the test file it
  authored has the same unguarded assertion baked into it.
- **Run 9** (`22d0bd36d34b`): runs `uv run pytest -q` early (passes, but only
  2 tests — the redirect isn't asserted yet), then hits the same ad-hoc probe
  once it adds the redirect test, and spirals on repeated `write` calls
  rewriting near-identical file content rather than re-probing.
- **Run 11** (`1cfed3cd58c5`, 2 parent turns): same ad-hoc-probe-then-rewrite
  loop as run 4, from the first attempt.

One structural variable, not four different bugs: whether the implementer
ever returns to the packet's specified validation command. Runs that keep
running `uv run pytest -q` (8, 9) still get caught, because their own
`test_app.py` inherits the same unguarded assertion — the trap isn't only in
the ad-hoc probe, it's latent in how an agent writes a redirect test at all
unless told otherwise. Runs that abandon it entirely (4, 11) are pure
validation-command drift compounding the same trap.

## How this was reconstructed

The child's own session JSONL is not captured (standing telemetry gap #1 —
see the roadmap backlog). All four traces came from the parent's
`tool_execution_update` events on the `subagent` tool call: the shipped
extension periodically snapshots the child's in-progress message history into
`partialResult.details.results[0].messages`, and those snapshots survived in
the parent's own artifact even though the call never returned. That's a
partial mitigation for gap #1, not a fix — it only works because each run
hung long enough to accumulate many snapshots, and it required manually
walking the parent artifact rather than reading a first-class child log.

## Artifacts

- Parent sessions: `docs/section-3-sdd/research/sessions/{0e8057a50162,
  1549ed13a963, 22d0bd36d34b, 1cfed3cd58c5}.jsonl` (retained locally, not
  published — see
  [artifact retention](../../superpowers/policies/evidence.md#artifact-retention)).
- Checkpoint entries 4, 8, 9, 11 of
  `.pi-eval-checkpoints/steered-tuned-phase3-n16.jsonl` (gitignored, local
  only).

## Why it matters

This is not a diffuse "the model sometimes hangs" finding — it is one
specific, well-understood trap accounting for 100% of this batch's hangs.
That sharpens the mechanism candidate considerably: a guardrail that catches
the `follow_redirects` pattern specifically (or, more generally, detects a
redirect test asserting `status_code` without `follow_redirects=False`) would
plausibly eliminate this batch's entire hang incidence, which a generic turn
cap or repeat breaker would only band-aid — the implementer isn't malfunctioning,
it's confidently, repeatedly correct about code that its own test methodology
can't observe.

Also worth weighing against the unsteered comparison: the unsteered
rewritten-spec baseline hit 6/16 hangs on the *identical* spec. Whether those
are the same trap has not been checked — that would tell us whether
delegation changes the *rate* of this specific failure, or just inherits it
unchanged from the base model's behavior on this spec.

## Disposition

Folded into Phase 3's committed report
(`2026-07-28-post-repair-sp2-phase3-tuned.md`) and Section 3's Claim 2
disposition. All four of Phase 3's steered hangs are now accounted for by
this single cause — this is a corroborated pattern, not a single anecdote.

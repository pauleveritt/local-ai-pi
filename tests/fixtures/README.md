# Test fixtures

## `author_contract_drafts/`

Eight byte-identical copies of the real overnight-authoring drafts, added
2026-08-11 so `tests/test_screen.py` no longer needs
`workloads/svcs/overnight/drafts/` (7.9 MiB, mostly raw authoring
transcripts irrelevant to the assertions) as a runtime dependency of the
default suite.

Per-file source paths and SHA-256s are in that directory's own
`PROVENANCE.txt`, which also records that the originals remain tracked and
untouched — these are additional copies, not a relocation.

## `pi-run-0.82.0.jsonl`

One real `pi --mode json` stdout stream, 179 KB, 123 lines, captured from a
genuine model run — not synthesized.

**Provenance.** It is `pi_stdout` from the first record of the supervised
n=16 batch described in
[`docs/superpowers/research/2026-08-01-phase1-n16-batch-evidence.md`](../../docs/superpowers/research/2026-08-01-phase1-n16-batch-evidence.md).
That checkpoint lived at `/tmp/satyrn-cycle14-checkpoint-v2.jsonl`
(SHA-256 `ef0a7b9f…`, matching the evidence record) and `/tmp` is transient.
This extraction was verified against that checksum before copying.

- Fixture SHA-256: `770007c197a3a63fec350360ecab06c6553cdaa3ce73a5aa43946d194c4a0ea3`
- Conditions: `omlx/gemma-4-12B-it-MLX-8bit`, pi 0.82.0, run accepted
  (`returncode=0`, not timed out)
- Known-good values: 6 turns; 5 tool calls (`bash` ×1, `write` ×4), all
  matched, none errored; input 7,068 / output 933 / cacheRead 6,144 /
  cacheWrite 0; context processed 13,212

**Why this is committed when raw model output generally is not.** Cycle 16
deliberately declined to commit the batch's raw output — 4.5 MB of *evidence*
for a published result. This is a different artifact for a different purpose:
a 179 KB **parser fixture** pinning what pi 0.82.0 actually emitted.

That distinction matters because the schema drifts across pi versions. The
pre-restructure `harness/telemetry.py` documented, for pi 0.81.1, that token
usage was absent from `--mode json` and that `isError` was a string. Both are
false in 0.82.0: usage is present on `turn_end`, and `isError` is a real
boolean. A synthetic fixture would test the parser against its author's belief
about the schema — and that belief is exactly what went stale before. Only a
captured stream is evidence.

Replacing this data would cost another supervised 16-run batch.

**What it cannot test.** All 123 lines are valid JSON, so this fixture cannot
exercise malformed-line tolerance. Tests needing that build a small synthetic
string inline.

## `pi-run-0.82.0-entry-appended.jsonl`

One real `pi --mode json` stdout stream, 224 KB, 157 lines, captured from a
genuine model run against `omlx/gemma-4-12B-it-MLX-8bit` under Pi 0.82.0 —
not synthesized.

**Provenance.** It is `pi_stdout` from a live `run_agentclinic_phase1()` call
(Phase 3, Task 1), run immediately after
`test_the_extension_emits_an_evidence_entry_into_captured_stdout` passed
against the same server and model. It is the first fixture captured with the
`.pi/extensions/hello-world.ts` extension appending its evidence entry from
`agent_start` rather than `session_start` — the change that lets the entry
survive past the point where `--mode json` attaches its session-event
subscriber.

- Fixture SHA-256:
  `f04dfdf0005927acfd5252fb85b31f66ac958a58007f948f3b22b57e8e330ba5`
- Line and byte counts: 157 lines, 229,266 bytes
- Conditions: `omlx/gemma-4-12B-it-MLX-8bit`, pi 0.82.0, run accepted
  (`returncode=0`, not timed out)
- `entry_appended` events: 1, with `entry.customType == "evidence"`

## `phase1-n48-telemetry-summary.json`

48 `{"turns": int, "context_processed": int}` pairs — the derived
telemetry summary of every run in two real batches, not raw model
output. In checkpoint order: the 16 preserved runs from the supervised
n=16 batch, then 32 more run specifically to extend this baseline
(Phase 2 cycle 2).

**Provenance.** Computed via `harness.telemetry.read_telemetry` from:

- `~/local-ai-pi-evidence/satyrn-cycle14-checkpoint-v2.jsonl` (16 records,
  SHA-256 `ef0a7b9fc80b8c33fbe619ecf6fbef03edd98fad2209431b4af6febee1c26c8e`,
  the same checkpoint `pi-run-0.82.0.jsonl` above was extracted from).
- `~/local-ai-pi-evidence/satyrn-phase2-cycle2-extension-n32.jsonl` (32
  records, SHA-256
  `66acdc5a272a45a8e94e040594e7e6821597944ea686bb98cf39d098a07edcce`).

Both files are outside Git, per the same reasoning as the n=16 batch's raw
output (see `docs/superpowers/research/2026-08-01-phase1-n16-batch-evidence.md`).
The full per-run detail (tool calls, errors, timing) and the reasoning for
treating the two checkpoints as one comparable batch are in
`docs/superpowers/research/2026-08-02-phase2-cycle2-precision-baseline.md`.

- Fixture SHA-256: `a384468da474952e0035f1c977a5a4323eb99bb1170eea8b12bf6608d464b153`
- Turn-count distribution: 6×20, 8×9, 9×7, 10×4, 11×7, 12×1
- All 48 runs accepted, `returncode=0`, not timed out, `complete=True`

## `pi-run-0.83.0-delegation.jsonl`

One **orchestrated** run's stream, trimmed. Source: run 1 of
`~/local-ai-pi-evidence/satyrn-phase5-cycle2-sdd-orchestrator-n16.jsonl`
(phase 5 cycle 2's `sdd-orchestrator` arm), Pi 0.83.0,
`omlx/gemma-4-12B-it-MLX-8bit`.

Kept: every `turn_end`, and the `subagent` `tool_execution_start` /
`tool_execution_end` pair. **Dropped from the end payload:** each result's
`messages` and `task` fields, which are hundreds of KB of prose nothing
parses. `agent`, `agentSource`, `exitCode`, `usage`, `model` and
`stopReason` are untouched.

Trimmed *real* output rather than a synthetic payload, deliberately. Phase 5
cycle 2 published a wrong headline because telemetry counted only the parent;
a hand-written fixture would keep passing while Pi's actual payload shape
drifted underneath it, which is precisely the failure being guarded against.

- Fixture SHA-256: `9850e7ac7e427d3f7212af84107f3fedb1d8f0b1fc6858ca5d0470996d5d4ee7`
- Parent: 6 turns, 18,553 `context_processed`
- Child, as the parent's stream reports it: 29 turns, 197,011 context
  processed — about 10.6x the parent, which is why the distinction matters

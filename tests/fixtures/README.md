# Test fixtures

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

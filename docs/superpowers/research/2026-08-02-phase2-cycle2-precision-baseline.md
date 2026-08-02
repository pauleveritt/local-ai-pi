# Phase 2, Cycle 2 — Precision baseline

Verified 2026-08-02 against two checkpoints: the preserved n=16 supervised
batch, and 32 more runs executed specifically to extend it (see the
[design spec](../specs/2026-08-02-phase2-cycle2-precision-baseline-design.md)
for why the extension was necessary before trusting any recommendation).

## Raw checkpoints

| | Path | Records | SHA-256 |
|---|---|---|---|
| Preserved | `~/local-ai-pi-evidence/satyrn-cycle14-checkpoint-v2.jsonl` | 16 | `ef0a7b9fc80b8c33fbe619ecf6fbef03edd98fad2209431b4af6febee1c26c8e` |
| Extension | `~/local-ai-pi-evidence/satyrn-phase2-cycle2-extension-n32.jsonl` | 32 | `66acdc5a272a45a8e94e040594e7e6821597944ea686bb98cf39d098a07edcce` |

Neither lives in `/tmp` (the preserved one did, transiently, before being
copied out — see `docs/superpowers/research/2026-08-01-phase1-n16-batch-evidence.md`).
Neither is committed to Git or archived elsewhere; this record and the
small derived fixture (`tests/fixtures/phase1-n48-telemetry-summary.json`)
are what survive if either is lost.

Recomputed by `2026-08-02-phase2-cycle2-recompute-summary.py`, alongside
this file.

## Why two checkpoints, treated as one batch

`run_batch()` refused to extend the preserved checkpoint directly — its
`conditions` (git revision, and an absolute extension path through
`.worktrees/restructure/`) no longer match the current checkout. Verified
before combining them anyway: the only `harness/` change between the
preserved checkpoint's revision and the extension's is the addition of
`harness/telemetry.py` (imported by nothing in `runner.py`) plus two
`runner.py` corrections (the pi-exit veto on `RunResult.accepted`, and a
role-check guard in `_has_assistant_content` used only by
`preflight_model`) — neither touches how `pi` is invoked. The extension
file is byte-identical at both paths. The task spec's SHA-256 is
unchanged. Full reasoning in the design spec.

## Conditions shared by all 48 records

| Field | Value |
|---|---|
| Model | `omlx/gemma-4-12B-it-MLX-8bit` |
| Pi version | `0.82.0` |
| Task-spec SHA-256 | `db17991e47b1b3dd5df18df08ff8939ed7924b81422a84cdb196dd0c51381c84` |
| Accepted | 48 of 48 |
| Pi return codes | all 0 |
| Timed out | none |
| `complete` (telemetry) | `True` for all 48 |

## Per-run table

Runs 1–16 are the preserved checkpoint; 17–48 are the extension. `tools`
is total tool calls (`turns - 1` in every row); `err` is how many of those
were `bash` errors (`write` never errored); `ctx` is `context_processed`;
`span` is seconds between the first and last `message_start` timestamp — a
lower bound on wall-clock, not a true duration (see `ROADMAP.md`'s Backlog
note on wall-clock timing).

| run | turns | tools | err | ctx | span(s) |
|---|---|---|---|---|---|
| 1 | 6 | 5 | 0 | 13212 | 35.2 |
| 2 | 9 | 8 | 2 | 22188 | 42.1 |
| 3 | 11 | 10 | 3 | 28557 | 53.1 |
| 4 | 6 | 5 | 0 | 12884 | 38.8 |
| 5 | 8 | 7 | 1 | 19501 | 51.4 |
| 6 | 6 | 5 | 0 | 12894 | 42.0 |
| 7 | 8 | 7 | 1 | 19419 | 49.5 |
| 8 | 6 | 5 | 0 | 12896 | 51.8 |
| 9 | 9 | 8 | 2 | 22224 | 59.7 |
| 10 | 11 | 10 | 3 | 28830 | 69.0 |
| 11 | 6 | 5 | 0 | 12896 | 41.8 |
| 12 | 6 | 5 | 0 | 12990 | 40.8 |
| 13 | 6 | 5 | 0 | 12948 | 39.6 |
| 14 | 6 | 5 | 0 | 12804 | 39.9 |
| 15 | 6 | 5 | 0 | 12918 | 47.1 |
| 16 | 9 | 8 | 2 | 22205 | 54.5 |
| 17 | 10 | 9 | 3 | 25084 | 45.1 |
| 18 | 8 | 7 | 2 | 18317 | 40.8 |
| 19 | 6 | 5 | 0 | 12982 | 41.2 |
| 20 | 12 | 11 | 4 | 31710 | 57.8 |
| 21 | 6 | 5 | 0 | 12862 | 44.1 |
| 22 | 8 | 7 | 1 | 19377 | 46.6 |
| 23 | 9 | 8 | 2 | 22279 | 67.8 |
| 24 | 8 | 7 | 1 | 19591 | 57.4 |
| 25 | 9 | 8 | 2 | 22239 | 61.9 |
| 26 | 11 | 10 | 3 | 28639 | 70.9 |
| 27 | 10 | 9 | 3 | 24998 | 58.2 |
| 28 | 11 | 10 | 3 | 28635 | 69.6 |
| 29 | 8 | 7 | 2 | 18587 | 50.3 |
| 30 | 10 | 9 | 3 | 25091 | 90.1 |
| 31 | 6 | 5 | 0 | 12850 | 39.8 |
| 32 | 6 | 5 | 0 | 12862 | 47.8 |
| 33 | 6 | 5 | 0 | 12868 | 67.8 |
| 34 | 6 | 5 | 0 | 12908 | 44.1 |
| 35 | 6 | 5 | 0 | 12912 | 43.9 |
| 36 | 6 | 5 | 0 | 12934 | 48.9 |
| 37 | 10 | 9 | 3 | 25322 | 45.5 |
| 38 | 8 | 7 | 2 | 18316 | 38.9 |
| 39 | 6 | 5 | 0 | 12950 | 35.6 |
| 40 | 6 | 5 | 0 | 12858 | 34.2 |
| 41 | 9 | 8 | 2 | 22228 | 40.1 |
| 42 | 8 | 7 | 2 | 18349 | 37.8 |
| 43 | 9 | 8 | 2 | 22206 | 40.0 |
| 44 | 11 | 10 | 3 | 28690 | 49.4 |
| 45 | 11 | 10 | 3 | 28849 | 50.1 |
| 46 | 6 | 5 | 0 | 12874 | 34.7 |
| 47 | 8 | 7 | 2 | 18316 | 38.2 |
| 48 | 11 | 10 | 3 | 28617 | 49.0 |

All 48 runs: `complete=True`. This table is real data, not retyped by
hand — it matches the recompute script's output exactly.

## Aggregates

| Metric | n=16 (original) | n=48 (this cycle) |
|---|---|---|
| Mean turns | 7.4375 | 8.0 |
| Turn distribution | 6×9, 8×2, 9×3, 11×2 | 6×20, 8×9, 9×7, 10×4, 11×7, 12×1 |
| Distinct turn values | {6, 8, 9, 11} | {6, 8, 9, 10, 11, 12} |
| `tool_calls == turns - 1` | holds, all 16 | holds, all 48 |
| Tool errors | 14/103, all `bash` | 65/336, all `bash` |
| `context_processed` range | 12804–28830 | 12804–31710 |

**New turn-count values appeared: 10 and 12, neither seen in the original
16.** This is the concrete evidence that motivated the extension in the
first place — the n=16 sample's support was incomplete, not just noisy.

## Stability: did extending actually help?

| | n=16 | n=48 | change |
|---|---|---|---|
| `leave_one_out_spread` (turns) | 0.333 | 0.128 | −61.7% |
| Hypothetical +1 run at 20 turns, halfwidth ratio at n=16 | ×1.93 (0.84375→1.625, seed=0, matching the spec) | ×1.37 (seed=0, n=16 within the n=48 sample) | improved |
| Hypothetical +1 run at 20 turns, halfwidth ratio at n=48/n=64 | — | ×1.35 (seed=0) | — |

The jackknife spread tightened substantially — a real, meaningful
improvement by the spec's own stated gate. The tail-sensitivity check also
improved: one hypothetical unseen run now moves the estimate by ~35%
rather than roughly doubling it.

**But read this alongside a second fact the spec's gate didn't explicitly
check: the mean itself moved by 0.5625 turns between n=16 and n=48** — larger
than two of the three candidate precision targets below (0.5 and 0.25).
The *estimate* got more stable; the *value it is converging toward* has
already moved by more than a 0.25-turn or 0.5-turn precision claim would
promise to resolve. This is not a contradiction of the tightening finding —
it is exactly what "n=16 was too thin" predicts — but it means: treat a
0.25-turn precision claim built from this n=48 sample with real skepticism
about whether even n=48 has converged, not just whether its own bootstrap
half-width looks small.

## How many runs do you need? (95% confidence, `seed=0`)

**Turn count:**

| Target half-width | Minimum n |
|---|---|
| 1.0 turn (coarse) | 14 |
| 0.5 turns | 56 |
| 0.25 turns (fine) | 237 |

**`context_processed`:**

| Target half-width | Minimum n |
|---|---|
| 1500 (coarse) | 64 |
| 1000 | 144 |
| 500 (fine) | 574 (corrected — see note below) |

**A bug in `minimum_n_for_precision`'s search, caught by Fable's review, is
why the 500 row above isn't "not reachable within 1000 runs" as this
record first published.** The search doubled `n` past `max_n` and gave up
without ever testing `max_n` itself or anything between the last
power-of-2 and it — but `max_n=1000` easily satisfies this target
(halfwidth 374.3 there). The true first-satisfying n is 567, though real
resampling noise near that boundary (567 and 568 satisfy; 569 doesn't;
570–571 do again) means binary search over that noise lands on 574, not
567 — both are correct answers in the sense the module actually promises
(the returned n is checked directly, not merely inferred), just not
necessarily the literal smallest one when the underlying function isn't
cleanly monotonic at that resolution. Fixed in `harness/precision.py`;
`tests/test_precision.py` now pins this case directly.

**Read in runs, not minutes, on purpose** — a contributor on any hardware
uses this table by timing one `run_agentclinic_phase1()` call on their own
machine (one line, no new tooling — see the design spec's "Deliberate
exclusions") and multiplying. On the owner's machine, the measured n=48
median span was **46.1 seconds** per run (min 34.2s, max 90.1s, total
2343.7s across all 48) — so n=56 is roughly 43 minutes of model time
there; elsewhere, it depends entirely on that machine's own one-run timing.

**n=48 already covers the coarsest target for both metrics.** It sits just
short of the middle turn-count target (56 vs. 48 in hand) and well short of
the finer ones. Whether closing that gap is worth another batch, versus
accepting a coarser precision target, versus a cheaper task slice, is
cycle 3's decision — not this cycle's (see the design spec, "Not cycle 3").

## Operational note: an environment drift the liveness check caught correctly

Running the extension batch hit two real failures before any run
succeeded, both caught by existing safeguards rather than producing a
silent bad result:

1. **The local `omlx` server wasn't running.** `preflight_model()` raised
   `ModelServerDown` before spending any batch time, per `BRIEF.md`'s
   explicit warning about this exact failure mode.
2. **After starting it, the server rejected requests with HTTP 401.**
   `~/.omlx/settings.json` had drifted to `"api_key": "evalkey"`,
   `"skip_api_key_verification": false` — no longer matching
   `harness/liveness.py`'s documented default (`"not-needed"`) or
   `BRIEF.md`'s stated environment. Resolved by resetting the server
   config back to `skip_api_key_verification: true` (the owner's choice,
   preferring to match the documented environment over changing harness
   code), verified via `curl` and then via `preflight_model()` itself
   before relaunching.

A third, unrelated failure came from this session's own process: a `git
commit` landed while the batch's first attempt was running in the
background. `run_batch()`'s `_conditions()` reads `git rev-parse HEAD`
live, so the commit invalidated every run still in flight —
`RuntimeError: run conditions changed during batch`, after 3 records had
already been appended under the pre-commit revision. Those 3 records were
discarded (not comparable to a fresh run under the new HEAD) and the
extension was relaunched cleanly, with no further commits until it
finished. Worth naming as an operational rule for any future batch: **do
not commit to the repository while a `run_batch()` call is in flight.**

## Verification method

Both checkpoints were parsed with `harness.telemetry.read_telemetry`
(already fixture-proven; see cycle 1) via the recompute script above, not
hand-aggregated. The precision analysis was performed with
`harness.precision` (this cycle), against the derived turn-count and
`context_processed` samples — both committed as
`tests/fixtures/phase1-n48-telemetry-summary.json` and pinned by
`tests/test_precision.py`.

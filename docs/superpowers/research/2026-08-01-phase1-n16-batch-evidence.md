# Phase 1 — n=16 batch evidence

Verified 2026-08-01 from the completed supervised batch checkpoint. This
compact record identifies the raw artifact and states the result read from it;
the raw model diffs and process output are intentionally not committed.

## Raw checkpoint at verification time

| Field | Value |
|---|---|
| Local path | `/tmp/satyrn-cycle14-checkpoint-v2.jsonl` |
| Size | 4,540,098 bytes |
| SHA-256 | `ef0a7b9fc80b8c33fbe619ecf6fbef03edd98fad2209431b4af6febee1c26c8e` |
| Complete JSONL records | 16 |

The path is where this file was read on 2026-08-01, not a promise that it
will remain there. `/tmp` is transient. The file is not in Git and this
project has not archived it externally. If someone has retained a copy, the
size and checksum above identify whether it is this checkpoint.

## Conditions shared by all 16 records

| Field | Value |
|---|---|
| Model | `omlx/gemma-4-12B-it-MLX-8bit` |
| Pi version | `0.82.0` |
| Harness revision | `ddc03b36329807088d1fc5875f38e6fcccc22bc6` |
| Task-spec SHA-256 | `db17991e47b1b3dd5df18df08ff8939ed7924b81422a84cdb196dd0c51381c84` |
| Run timeout | 600 seconds |
| Grade timeout | 30 seconds |

Each record also names the same isolated Pi command: non-interactive JSON
output, no ambient extensions, skills, prompt templates, themes, or context
files; the project `hello-world.ts` extension; and the task spec in the final
prompt position.

## Result read from the checkpoint

| Field | Aggregate value |
|---|---|
| Accepted runs | 16 of 16 |
| Pi timeouts | 0 |
| Pi return codes | all 0 |
| Grade return codes | all 0 |
| Acceptance tests executed | 4 in every run |
| Acceptance tests expected | 4 in every run |

This is the evidence behind Phase 1's completed n=16 reproduction. The
post-Phase-1 Pi-exit correction does not alter it: every recorded Pi return
code already satisfies the stricter zero-exit requirement.

## Verification method

The checkpoint was inspected directly as JSONL: its lines were counted, its
SHA-256 and size were measured, and the unique conditions and outcome fields
were aggregated across all records. The raw artifact, rather than a summary
claim, supplied every value above.

# Cycle 7 — confirmatory result

**Phase:** 7 — workload first, envelope to candidate commit
**Status:** the batch this document reports ran to completion; not itself frozen or amendable, but see "What this does not establish" below for scope
**Pre-registration:** [`2026-08-11-phase7-cycle7-preregistration-design.md`](../specs/2026-08-11-phase7-cycle7-preregistration-design.md) — frozen at `0373ed9`
**Git revision run against:** `0373ed9` (the pre-registration's own commit; no contract, gate, or cohort edit landed between freeze and run)
**Batch driver:** a one-time, non-repository script (`confirmatory_batch.py`, not committed — see "What this does not establish"), run as background task `bf01r14bi`, started 2026-08-11 15:28 and finished 2026-08-11 ~17:54 (≈146 minutes for 64 attempts + 1 replaced void)

## Result

64/64 pre-registered attempts completed. 0 unresolved voids. 1 attempt voided and replaced within its slot (see "Void attempts" below) — the pre-registered n=8 per arm per task was reached everywhere.

### Per-task (primary)

| Task | Arm | n | candidate-created | oracle-passed | Wilson 95% CI |
|---|---|---|---|---|---|
| flask-extensions | brief | 8 | 8 | 8 | [0.676, 1.000] |
| flask-extensions | locating-contract | 8 | 8 | 8 | [0.676, 1.000] |
| stringified-annotations | brief | 8 | 6 | 3 | [0.137, 0.694] |
| stringified-annotations | locating-contract | 8 | 8 | 8 | [0.676, 1.000] |
| local-pings | brief | 8 | 8 | 7 | [0.529, 0.978] |
| local-pings | locating-contract | 8 | 8 | 7 | [0.529, 0.978] |
| autowire | brief | 8 | 1 | 0 | [0.000, 0.324] |
| autowire | locating-contract | 8 | 8 | 0 | [0.000, 0.324] |

| Task | Newcombe diff (contract − brief) | Verdict |
|---|---|---|
| flask-extensions | [-0.324, 0.324] | INCONCLUSIVE — both arms tied at ceiling (see "Floor/ceiling flags") |
| stringified-annotations | [0.170, 0.863] | **SUPERIORITY (contract > brief)** — interval excludes 0 |
| local-pings | [-0.361, 0.361] | INCONCLUSIVE — both arms tied near-ceiling |
| autowire | [-0.324, 0.324] | INCONCLUSIVE — both arms tied at floor (see "Floor/ceiling flags") |

Per the pre-registration's directional hypothesis ("Arm B has a higher oracle-passed rate than Arm A on at least the tasks where Arm B has already shown near-ceiling pilot performance — flask-extensions, stringified-annotations"): confirmed for **stringified-annotations**, not confirmed for **flask-extensions** (both arms were already at ceiling, so there was no headroom for separation).

### Pooled (secondary — not a substitute for the per-task table above)

| Arm | n | oracle-passed | rate | Wilson 95% CI |
|---|---|---|---|---|
| brief | 32 | 18 | 0.562 | [0.393, 0.718] |
| locating-contract | 32 | 23 | 0.719 | [0.546, 0.844] |

Pooled Newcombe diff (contract − brief): [-0.076, 0.367] — includes 0. The pooled number is directionally consistent with the per-task result (locating-contract ahead on 3 of 4 tasks' point estimates, tied on the fourth) but, as the pre-registration anticipated, does not itself clear the superiority bar; the per-task table is where the real finding is, per this document's compliance with the pre-registration's task-weighting rule.

Both computed by `harness/intervals.py` (`wilson_interval`, `newcombe_interval`), the same tested helper the pre-registration specifies — not hand-computed.

## Floor/ceiling flags

Per the pre-registration's workload floor/ceiling stop rule:

- **flask-extensions**: both arms at 8/8 (universal ceiling), no separation. Flagged — this task contributed no comparative information in this batch; it was already known from pilot data to be near-ceiling for the locating-contract arm, and this batch shows the brief arm reaches the same ceiling. Consistent with the manifest's own account: `flask-extensions`'s edit is small and localized enough that the executor's exact-path scoping (which both arms retain) may already carry what the locating contract adds.
- **autowire**: both arms at 0/8 (universal floor), no separation on the primary metric. Flagged — per the pre-registration's own anticipation of this exact outcome ("if it also floors under Arm A, that is itself informative — it would mean the locating contract's detail is not what autowire's ceiling is about"). Confirmed: the locating contract does **not** move autowire's failure mode. See "autowire secondary-metric divergence" below for what it does move.
- **local-pings**: 7/8 both arms — near-ceiling and tied, but not a literal 0/8 or 8/8 so it does not trigger the stop rule's strict definition. Reported here for the same reason: no separation, no comparative information from this task in this batch.

Net: of four tasks, only **stringified-annotations** discriminated between arms in this batch.

## autowire secondary-metric divergence (candidate-created)

Both arms floor identically on the primary metric (oracle-passed), but diverge sharply on the secondary one: brief produced a `candidate-created` result on 1/8 attempts, locating-contract on 8/8. The locating contract reliably gets the executor to a state that passes the *preservation* suite; it does not get it to a state that passes the *hidden* oracle test. The one brief-arm candidate that was created failed the oracle with 67 real test failures (signature/type-annotation handling gaps in the generated `_autowire`/`aautowire` implementation) — a genuine capability shortfall, not a validation-gate artifact (confirmed by reading the failure tail directly, matching this session's earlier flask-extensions-defect discipline of checking gate failures against ground truth rather than trusting the summary number). The remaining seven locating-contract and seven brief-arm autowire attempts that did not reach `candidate-created` mostly failed with circular-import or missing-module errors from the model's own written code (`ImportError: cannot import name 'autowire' from partially initialized module 'svcs'`, `ModuleNotFoundError: No module named 'svcs.container'`) — the model choosing an import structure that doesn't resolve, independent of arm.

This is consistent with the pilot's prior characterization of autowire as "a genuine capability ceiling, not a harness artifact" ([`gemma12b-implementer-v1.toml`](../../../workloads/svcs/cells/gemma12b-implementer-v1.toml)) and sharpens it: the ceiling is specifically about correctly implementing autowiring semantics (parameter kinds, defaults, special typing forms), not about locating where to write code — the locating contract solves the latter (`candidate-created` jumps from 1/8 to 8/8) without touching the former.

## Void attempts

One void, replaced within its slot per the pre-registration's void-handling rule (excluded from both numerator and denominator, a fresh attempt run in its place):

- `stringified-annotations__brief__r5`, first attempt: model call exited with signal -15 (SIGTERM) after the 900-second wall-clock budget with no output — classified `infrastructure-failure` by `deliver_candidate.py`, matching the pre-registration's void criterion "Pi exits having never reached a tool call." Retry (`__retry1`) completed normally and is the attempt recorded in the per-task table above.

No other void or infrastructure-failure occurred in the remaining 64 recorded attempts.

## Abort-condition check

Per the pre-registration's exclusions and abort conditions, checked directly against the batch log rather than assumed:

- `CellMismatch`: 0 occurrences. `cell gemma12b-implementer-v1: live configuration verified` printed 65 times (64 attempts + 1 void retry), matching every attempt including the replaced one.
- `policy_error` (the implementer's `tool_call` handler's `try`/`catch` firing): 0 occurrences.
- Validation-gate defect of the flask-extensions-deselect shape (a gate that rejects or accepts independent of candidate correctness): none discovered. autowire's failures were confirmed to be genuine candidate defects (import errors, real oracle test failures) by reading the actual failure output, not inferred from a pass/fail count.

No abort condition was met. The batch ran to its full pre-registered n without early stop.

## Housekeeping verified after completion

- `pi-agent-dir/models.json`'s `gemma-4-12B-it-MLX-8bit` entry: `maxTokens` confirmed restored to `8192` (the committed default) after the batch's single `bumped_max_tokens(..., 32768)` context exited.
- Worktree clean at batch completion (aside from unrelated, separately committed work).
- All 64 attempts' receipts and per-attempt records are accounted for in `all_results.json`; no denominator in the tables above silently includes a void.

## Evidence archive

Indexed alongside this repository's other archived evidence in
[`2026-08-11-evidence-archive-index.md`](2026-08-11-evidence-archive-index.md).
Bundled and checksum-verified at
`/Users/pauleveritt/projects/pauleveritt/local-ai-pi-evidence-archive/2026-08-11-phase7-cycle7-confirmatory/`
(external to this repository, per the distribution brief's "record the bundle's
location and checksum in the repository, but do not require a collaborator to
download it" — no test or product path reads from this location):

- `receipts/*.json` — all 65 attempt receipts (64 pre-registered + 1 void
  replacement), `deliver_candidate.py`'s own `--receipt` output.
- `all_results.json` — the batch driver's aggregated per-attempt records.
- `batch-run.log` — the batch's full stdout.
- `MANIFEST.md` — provenance, result summary, and an explicit account of what
  is *not* in the bundle (see below).
- `CHECKSUMS.sha256` — SHA-256 of every file above; verify with
  `shasum -a 256 -c CHECKSUMS.sha256` from that directory.

Bundle checksum-of-checksums (detects tampering with `CHECKSUMS.sha256`
itself without re-hashing every file):
`SHA256(CHECKSUMS.sha256) = ab9b59e66b93e01f3661d92f63cf6f9b4d5992338516978ff28178c889713610`.

**What the bundle does not contain, and why:** no raw Pi/model transcripts —
`harness/processes.run_process()` captures the model child's stdout/stderr
only in memory, never to disk, for every attempt in this batch, not a
bundling gap; no candidate patches/diffs — each attempt's candidate commit
lived inside a `disposable_dir()` (`harness/workspace.py`) that is
`shutil.rmtree`'d unconditionally on exit, so only `changed_paths` (filenames)
survive, not content; no `confirmatory_batch.py` driver — written as a
one-time execution of the frozen pre-registration, not committed product
infrastructure. A future batch needing replayable transcripts or diffs
requires extending `run_process()` and `deliver()` to persist them before
cleanup, which does not exist today — this is now a documented harness gap,
not a silent one.

## What this does not establish

- **Not evidence for a fifth task or a general planner.** This remains the same four-task cohort the pre-registration scoped to; `harness/typed_contract.py` is still a narrow bridge, not general contract authoring.
- **Not a claim that locating contracts help universally.** They discriminated on exactly one of four tasks in this batch (stringified-annotations); two tasks were already ceiling-tied and one is floor-tied on the primary metric regardless of arm.
- **Batch driver script is not in the repository.** `confirmatory_batch.py` was written and run as a one-time execution of the frozen pre-registration (its own header says so explicitly) and is not committed product infrastructure. The distribution brief's step 4 ("give the running comparison a discoverable checked-in driver") remains open — the evidence archive above preserves this batch's *results*, not a rerunnable driver.
- **Pilot data is not re-cited as confirmatory evidence here**, consistent with governing rule 8 and the pre-registration's own framing; every rate above is this batch's own attempts, not pooled with any earlier pilot round.

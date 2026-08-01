# Roadmap

*Phases group feature cycles. One direction at a time. Tangents go to the
Backlog, not into the current phase.*

## Now

**Phase 1 — Reproduce AgentClinic Phase 1 with a trustworthy engine.** One
run, hermetically graded, recorded to a checkpoint; then n=16 reproducing
~15/16. The engine's first job is to reproduce a number we already trust, not
to discover one — see `BRIEF.md` for why. Everything else waits.

*(Superseded framing, kept for the record: an earlier pass named Phase 1 "the
restructure spec" — define the volunteer reader, then derive a section
structure for them. That's a real question, but it's downstream of having a
working engine and real suites to write about; it isn't Phase 1's job. See
`BRIEF.md`, "First decision for the new session.")*

## Concept budget

*Every term below is a cost against a 5–10 h/wk volunteer's ability to hold
the design in mind — see `BRIEF.md`. Checked and updated at the end of each
cycle; a term earns its place by naming something the design actually needs,
not by being convenient shorthand.*

| Term | Means | Introduced |
|---|---|---|
| feature cycle | the unit of work within a phase — one small, provable thing | kickoff |
| phase | groups feature cycles; one direction at a time | kickoff |
| suite | the acceptance test suite a solution is graded against | cycle 1 |
| fixture | a known-good or known-broken example solution, used to prove the grader itself | cycle 1 |
| workspace | a disposable, git-initialized directory the model writes into. Read by the grader, never graded directly — see *grading directory* | cycle 2 |
| grading directory | a fresh directory holding only allowlisted files copied out of the workspace, plus the suite; what pytest actually runs against | cycle 9 |
| hermetic | graded with controlled model-written files and caller configuration, so those inputs cannot affect the verdict | cycle 2 |
| grader | the code that turns a workspace into a verdict (`harness/grading.py`) | cycle 1 |
| harness | the eval harness as a whole (`harness/` package) | kickoff |
| verdict | the accept/reject/refuse outcome of grading one workspace (`GradeResult`) | cycle 3 |
| hook | the pytest hook that writes the real per-test outcomes to a results file | cycle 3 |
| vacuous / non-vacuity | a test that passes without testing what it claims to — this project's recurring hazard | cycle 3 |
| refusal | the grader declines to certify a run before pytest ever executes | cycle 5 |
| task spec | the AgentClinic roadmap document a model builds a solution from | cycle 6 |
| seam | a parameter standing in for a value that could change, so nothing has to change if it does — not a hardcode | `BRIEF.md`, reused cycle 7 |
| liveness (check) | confirming the model server responds before a run is even attempted | cycle 7 |
| allowlist | which model-written paths (`app.py`, `templates`) get copied into a fresh directory and graded at all | cycle 5's close, implemented cycle 9 |
| checkpoint | an append-only JSONL record of completed runs; resumes by counting valid lines, tolerant of a truncated last line on both read and write | cycle 2's deferrals, implemented cycle 10 |
| run | one invocation of Pi against one fresh workspace, followed by its grade | cycle 8 |
| batch | a fixed, sequential set of runs under one declared set of conditions | cycle 11's re-plan |
| extension | the fixed project-supplied Pi addition loaded for each run, distinct from Pi's ambient extensions | cycle 8 |
| process group | one Pi or pytest child plus descendants, terminated together if that child times out | cycle 12 |

**Retired, not currently spent:** `oracle` — dropped from the engine's
vocabulary, since "grader"/"verdict" cover the same ground without a term
borrowed from testing theory. It survives in `BRIEF.md` only as a
reference to the old branch's suite, which is a historical citation rather
than live usage; don't "fix" that occurrence. `conjunct` — renamed to
`condition`; cycle 5's audit caught that the rename hadn't reached every
test name.

## Phases

| # | Phase | Direction (one sentence) | Status |
|---|-------|--------------------------|--------|
| 1 | Reproduce AgentClinic Phase 1 | One trustworthy, hermetically-graded run; n=16 reproducing ~15/16 | complete |

### Phase 1 feature cycles

| Cycle | Summary | Spec | Plan | State |
|-------|---------|------|------|-------|
| 1 | Accept/reject fixture pair — known-good and known-broken AgentClinic Phase 1 solutions, proven by plain pytest | [spec](docs/superpowers/specs/2026-07-30-phase1-cycle1-fixture-pair-design.md) | [plan](docs/superpowers/plans/2026-07-30-phase1-cycle1-fixture-pair.md) | Done |
| 2 | Workspace provisioning — `prepare_workspace` context manager copies a fixture into a fresh, git-initialized, disposable workspace; proven by an automated pytest test re-running cycle 1's accept/reject procedure through it | [spec](docs/superpowers/specs/2026-07-30-phase1-cycle2-workspace-provisioning-design.md) | [plan](docs/superpowers/plans/2026-07-30-phase1-cycle2-workspace-provisioning.md) | Done |
| 3 | Verdict from a hook-written results file — grade by reading a file a pytest hook wrote, not pytest's exit code. Names the verdict type. | [spec](docs/superpowers/specs/2026-07-30-phase1-cycle3-verdict-file-design.md) | [plan](docs/superpowers/plans/2026-07-30-phase1-cycle3-verdict-file.md) | Done |
| 4 | Subversion fixtures — fixtures that attack grading (`addopts = --collect-only`; import-time `os._exit(0)`), confirmed to defeat a naive exit-code grader | [spec](docs/superpowers/specs/2026-07-30-phase1-cycle4-subversion-fixtures-design.md) | [plan](docs/superpowers/plans/2026-07-30-phase1-cycle4-subversion-fixtures.md) | Done |
| 5 | Refusal of model-written config — the grader refuses to certify a run whose workspace carries model-written `pytest.ini`/`.pytest.ini`/`pyproject.toml`/`tox.ini`/`setup.cfg`/`conftest.py`/`sitecustomize.py`, before pytest ever runs. Split from the original combined row (below) — the allowlist half needed evidence this half didn't. | [spec](docs/superpowers/specs/2026-07-30-phase1-cycle5-config-refusal-design.md) | [plan](docs/superpowers/plans/2026-07-30-phase1-cycle5-config-refusal.md) | Done |
| 6 | AgentClinic task spec — transplanted **Phase 1's section only** of the detailed roadmap to `examples/agentclinic/specs/roadmap.md`, the document the trusted number was produced against, resolving a citation cycle 1's suite had carried since. Deliberately *not* a variant choice: see the Backlog note. Also fixed the grading regression the transplant made reachable. | [spec](docs/superpowers/specs/2026-07-30-phase1-cycle6-task-spec-design.md) | [plan](docs/superpowers/plans/2026-07-30-phase1-cycle6-task-spec.md) | Done |
| 7 | Model-server liveness check — `check_model_server_alive` GETs `/v1/models` on the `omlx` server (`127.0.0.1:8001` default, a seam) and raises `ModelServerDown` on anything but a 200; proven against a stub HTTP server, not a real model, with two distinct down-modes (nothing listening; a completed exchange with a bad status) so the raise isn't just "catch anything." | [spec](docs/superpowers/specs/2026-07-31-phase1-cycle7-liveness-check-design.md) | [plan](docs/superpowers/plans/2026-07-31-phase1-cycle7-liveness-check.md) | Done |
| 8 | First real run — `run_agentclinic_phase1()` invokes `pi` against a fresh, literally-empty workspace, captures a diff against the workspace's initial commit, and grades hermetically via cycles 3–6's grader. The task spec is passed as `pi`'s prompt text, never placed in the workspace. **Actually run, live, against the real `omlx` server, once the harness code and three bugs invisible to fixture-only testing were fixed** (see below): the model built a working AgentClinic Phase 1 app and it graded `accepted=True, tests_executed=tests_expected=4, returncode=0`. | [spec](docs/superpowers/specs/2026-07-31-phase1-cycle8-first-real-run-design.md) | [plan](docs/superpowers/plans/2026-07-31-phase1-cycle8-first-real-run.md) | Done |
| 9 | Source allowlist — `grade()` now copies only allowlisted paths (`app.py`, `templates`, default) plus the suite into a fresh grading directory and runs pytest there, instead of `cwd=workspace`. Closes the sys.path-shadowing threat by construction: a model-written `harness/` package or `pytest.py` is never copied in, so it can never be imported in place of the real thing. Proven with a verified-first exploit — a rogue `harness/grading_plugin.py` that crashed collection and leaked into `stderr` under the old code, confirmed inert after the fix. | [spec](docs/superpowers/specs/2026-07-31-phase1-cycle9-source-allowlist-design.md) | [plan](docs/superpowers/plans/2026-07-31-phase1-cycle9-source-allowlist.md) | Done |
| 10 | Checkpoint recording — `harness/checkpoint.py`'s `append_checkpoint`/`load_checkpoint` persist a `RunResult` per completed run as JSONL, resuming by position (the Nth valid line is run N). `load_checkpoint` tolerates a truncated final line (a process that died mid-write); `append_checkpoint` cleans up that same dangling fragment before writing its own record, so resuming more than once stays safe — a real corruption bug Fable's review caught before implementation, where the naive version would have concatenated onto the fragment instead. | [spec](docs/superpowers/specs/2026-07-31-phase1-cycle10-checkpoint-recording-design.md) | [plan](docs/superpowers/plans/2026-07-31-phase1-cycle10-checkpoint-recording.md) | Done |
| 11 | Corrective hardening — checkpoint append preserves complete final records and never rewrites valid prefixes; grading uses a controlled child environment; workspace setup is independent of hooks/global Git config and supports a literally empty workspace; missing proof regressions are added. | [spec](docs/superpowers/specs/2026-08-01-phase1-cycle11-corrective-hardening-design.md) | [plan](docs/superpowers/plans/2026-08-01-phase1-cycle11-corrective-hardening.md) | Done |
| 12 | Hang tolerance — Pi and pytest timeouts terminate their entire process groups, yield bounded rejected results with partial output, and let a later batch attempt continue. | [spec](docs/superpowers/specs/2026-08-01-phase1-cycle12-hang-tolerance-design.md) | [plan](docs/superpowers/plans/2026-08-01-phase1-cycle12-hang-tolerance.md) | Done |
| 13 | Batch contract — restore the trusted Pi invocation shape, prove real model output before a batch, and record the conditions that make completed runs comparable. | [spec](docs/superpowers/specs/2026-08-01-phase1-cycle13-batch-contract-design.md) | [plan](docs/superpowers/plans/2026-08-01-phase1-cycle13-batch-contract.md) | Done |
| 14 | n=16 batch, sequential and resumable — target ~15/16; the supervised run completed 16/16 accepted with no rejected attempts. | [spec](docs/superpowers/specs/2026-08-01-phase1-cycle14-n16-batch-design.md) | [plan](docs/superpowers/plans/2026-08-01-phase1-cycle14-n16-batch.md) | Done |

### Post-Phase 1 corrective cycles

| Cycle | Summary | Spec | Plan | State |
|-------|---------|------|------|-------|
| 15 | Pi exit veto — a run remains diagnostically graded after Pi returns, but it is accepted only when Pi did not time out, Pi exited zero, and the grade is accepted. The recorded Phase 1 batch is unaffected: all sixteen Pi return codes were zero. | [spec](docs/superpowers/specs/2026-08-01-post-phase1-pi-exit-veto-design.md) | [plan](docs/superpowers/plans/2026-08-01-post-phase1-pi-exit-veto.md) | Done |
| 16 | n=16 batch evidence — a compact, committed [record](docs/superpowers/research/2026-08-01-phase1-n16-batch-evidence.md) identifies the raw checkpoint and its measured conditions/results without committing 4.5 MB of model output. | [spec](docs/superpowers/specs/2026-08-01-post-phase1-batch-evidence-record-design.md) | [plan](docs/superpowers/plans/2026-08-01-post-phase1-batch-evidence-record.md) | Done |
| 17 | Local workspace hygiene — active linked worktrees and local agent state are ignored; nine old generated session files moved unchanged into the preserved old-project worktree after SHA-256 verification; the stale Sphinx static-path setting is removed so strict docs builds pass. | [spec](docs/superpowers/specs/2026-08-01-post-phase1-local-workspace-hygiene-design.md) | [plan](docs/superpowers/plans/2026-08-01-post-phase1-local-workspace-hygiene.md) | Done |

**Why this order.** Cycles 3–7 build and prove the entire judging apparatus
*before* a model runs once — every one of them is provable against fixtures
with no model in the loop. That is deliberate: it means the ~15/16 at cycle
14 measures the model rather than the engine, which is the whole reason
Phase 1 was chosen for being boring (see `BRIEF.md`). Building the grader
after the first run would produce output with no trusted way to judge it.
Cycle 9 (the allowlist) is the one deliberate exception — it is judging
apparatus built *after* a model has run, because it is the one piece that
needs a model's actual output to be anything more than a guess. Cycle 10
(checkpoint recording) returns to the fixture-only pattern: its tests
construct a `RunResult` by hand and never invoke `pi` or the model
server, exactly like cycles 3–7.

Cycles 4-before-5, 6-before-8, and 8-before-9 follow cycle 1's precedent:
the artifacts that make a proof possible get their own cycle, ahead of the
machinery that consumes them.

**Current dependency order, corrected 2026-08-01.** The post-cycle-10
harvest originally placed workspace hardening after the batch. The deep
review demonstrated that a contributor's `core.hooksPath`, checkpoint repair,
and caller-controlled pytest settings can break or corrupt an otherwise valid
batch before it starts. Cycle 11 repairs those prerequisites first; cycle 12
then makes one timed-out attempt survivable; cycle 13 establishes the exact
conditions and real-output preflight for comparable runs; and cycle 14 is the
batch that consumes all three. The historical harvest notes below retain their
original cycle numbers only as a record of that superseded plan.

**The 2026-07-31 harvest re-plan.** After cycle 10 closed, a stocktake of
everything sitting in Deferred candidates and the Backlog turned three
items into cycles rather than leaving them to fall off the end of Phase 1
unaddressed: hang tolerance (new cycle 11, following the same
before-the-machinery-that-needs-it logic as cycle 1's precedent — the
n=16 batch is the machinery, hang tolerance is the artifact it depends
on), the n=16 batch itself (pushed from 11 to 12), and
`harness/workspace.py` hardening (new cycle 13, closing two bugs homeless
since cycle 2's review). Items deliberately *not* promoted: the
`pyproject.toml` reservation and `pi_stdout`/`pi_stderr`-on-timeout
capture are both evidence-gated with no evidence yet — forcing them into
a cycle now would be exactly the "machinery ahead of the contract it
serves" `BRIEF.md` warns against; the roadmap-variant experiment, the
phase-2+ authoring scaffold, and telemetry all stay in the Backlog
because they're Phase 2's business, not Phase 1's — see the Backlog
section.

**Correction, 2026-08-01: the harvest re-plan also promoted
out-of-process suite execution as cycle 14, and that promotion is
withdrawn.** It was ranked by severity-if-exploited rather than by
expected value against the actual threat, and "largest known gap" quietly
became "next thing to build." Three arguments against it, in ascending
order of weight. The threat is not live: forging a verdict requires a 12B
model to know a grader exists, know its filename prefix, and know its
`nodeid<TAB>outcome` file format, none of which appears in the task spec
it receives. The fidelity argument was overstated: `TestClient` diverges
from a real server on lifespan events, streaming, and connection
semantics, and Phase 1's suite exercises none of them — it asserts a 200,
a substring, two links, and a doctype. And decisively, the acceptance
suite *is* the measuring instrument that produced the trusted number;
rewriting it at the end of a reproduction phase, and paying a sixteen-run
re-baseline to get back to where we already are, is the same move cycle 6
refused for one bullet of the task spec. Phase 1 now ends at cycle 14.

**Post-Phase 1 correction, 2026-08-01.** Reviewing the completed batch
found one missing run-level condition: a nonzero Pi exit could coexist with
an accepted grade. Cycle 15 closes that gap without changing the grading
contract or discarding diagnostic evidence; the runner still diffs and grades
the workspace after Pi returns. It is deliberately outside Phase 1's feature
sequence because all sixteen historical records already have return code zero,
so the correction does not alter the reproduced result. The concept budget is
unchanged: it uses the existing terms *run* and *verdict* rather than naming a
new mechanism.

**Post-Phase 1 evidence record, 2026-08-01.** Cycle 16 records the raw
n=16 checkpoint's path at verification time, size, checksum, shared
conditions, and aggregate result in a committed
[research page](docs/superpowers/research/2026-08-01-phase1-n16-batch-evidence.md).
The 4.5 MB raw JSONL remains outside Git and has not been archived externally;
the path is a reference, not durable storage. The concept budget is unchanged:
this preserves existing checkpoint evidence rather than adding a mechanism.

**Post-Phase 1 local workspace hygiene, 2026-08-01.** Publishing the orphan
history as `main` exposed active worktrees, local agent state, and generated
old-project session files in the root worktree. Cycle 17 adds only the two
general local ignore rules (`.worktrees/`, `.superpowers/`) and moves the
nine session files unchanged into the matching ignored path of the preserved
old-project worktree, verified by SHA-256 before and after. The concept budget
is unchanged: this is file placement and repository hygiene, not a new engine
mechanism. Cycle 17 also removed the unused `html_static_path` setting from
`docs/conf.py`; no custom static assets exist, and the strict Sphinx build now
passes without warnings.
The research survives in the Backlog entry — it is worth keeping and
expensive to re-derive.

### Deferred candidates

*Things a cycle's brainstorming considered and passed over — usually the
"smallest choice" between two real options. Tracked here, updated at the
end of each cycle, so the next brainstorming session starts from this list
instead of re-deriving it from old specs.*

The 2026-07-30 re-plan absorbed this list into cycles 3–10 above (numbers
as they stood then): the hermetic grader split into cycles 3 and 5, the
typed verdict into cycle 3 (so the grader names the concept rather than
inheriting a name it never argued for), the git-diff exercise into cycle 8
(the first time a model writes changes worth diffing), checkpoint/resume
into cycle 9, and n=16 into cycle 10. That re-plan also found three things
the list had never named — a model actually being invoked, a liveness
check, and the AgentClinic spec the model builds from — which are now
cycles 8, 7, and 6. Cycle 5's own close then split its combined row and
inserted the allowlist as a new cycle 9, pushing checkpoint/resume and
n=16 to 10 and 11 — the numbers above reflect that; this paragraph is
historical record of the numbering as it stood before that split.

**Resolved by cycle 5, kept for the record.** The two notes above from
cycle 2's review (`core.hooksPath` breaking `prepare_workspace`'s commit;
`CalledProcessError` on an empty source directory) were about
`harness/workspace.py`, which cycle 5 correctly never touched — they carry
forward again below, still open. Cycle 3's git-isolation note and cycle
4's two notes (reusable attack helpers; the vacuity trap in "proven by
rejecting cycle 4's attacks") were all directly addressed by cycle 5: it
graded in the workspace with no second directory, consumed cycle 4's
helpers as planned, and its non-vacuous tests assert on `refused_config`
and `returncode is None` rather than `accepted is False` alone.

**Resolved by cycle 11.** The 2026-07-31 harvest had assigned workspace
hardening to its old cycle 13. Cycle 11 moved it before every batch
dependency: its initial commit ignores global/system Git configuration and
hooks, and `--allow-empty` permits a genuinely empty workspace with no
placeholder file.

These two notes from cycle 5 were carried to cycle 9. One is resolved,
one is still open and has nowhere else to go:

- **Still open — the `pyproject.toml` reservation.** Cycle 5 refuses a
  model-written `pyproject.toml` outright, on the grounds that AgentClinic
  Phase 1 never needs one and `[tool.pytest.ini_options]` inside it is a
  live attack path — but it's the one refused name a model might write
  for a legitimate reason (declaring dependencies). Cycle 8's real run
  didn't produce one (the model wrote `app.py`, `templates/`, and its
  own `tests/test_app.py`), so
  this note's trigger condition never fired and the question is still
  exactly where cycle 5 left it. Not cycle 9's to resolve — the allowlist
  is additive (what gets copied in), not a change to what refusal blocks.
  Carried forward with no specific owning cycle; revisit if a future run
  ever does produce one.
- **Resolved by cycle 9.** Module shadowing via `sys.path` — see the
  Backlog entry (below) for the full resolution. Cycle 9 took exactly the
  copy-only-allowlisted-files shape this note speculated about.

**Resolved by cycle 12.** Surfaced by cycle 5's brainstorming, not a
specific single cycle at the time:
`grade()` never catches `subprocess.TimeoutExpired`; it propagates
uncaught. Immaterial for a single run, but a batch needs one hung run to
record a rejection and continue, not abort the whole batch. Cycle 10's
checkpoint made resuming a batch possible; Cycle 12 makes surviving a
hang inside one possible, with group teardown and a bounded returned result.

**A collision surfaced by cycle 6's brainstorming, confirmed empirically,
and resolved by cycle 6.** `grade()` invoked `pytest -q` with
`cwd=workspace` and *no path argument*, so pytest collected every test
file in the workspace — not just the acceptance suite the harness copied
in. The AgentClinic roadmap's Phase 1 section ends by instructing the
model to "Write a smoke test in `tests/test_app.py`". So a model that
followed the spec **correctly** produced extra test files, and
`tests_executed == tests_expected` (cycle 3's condition, cycle 4's proof)
failed on a perfect solution.

Measured, not predicted: cycle 1's `reference` solution plus a two-test
`tests/test_app.py` graded as `accepted=False, executed=6, expected=4,
returncode=0`. Had it gone unresolved, cycle 8's first real run would have
rejected a correct solution and the failure would have looked like a model
problem rather than an engine problem — precisely the confusion Phase 1
was chosen to make impossible.

**Resolved by cycle 6.** `grade()` now passes the acceptance suite's
filename to pytest, so only the suite is collected — restoring what the
old harness got from `tests/test_acceptance.py` in its argv, and what the
trusted number was produced under. Pinned by
`tests/test_grading.py::test_grade_ignores_model_written_tests_and_grades_the_suite_alone`.

Two alternatives were considered and rejected. Editing the smoke-test
bullet out of the transplanted spec would work, and is the wrong
direction: the 16/16 runs included that bullet, so removing it moves our
conditions away from the ones being reproduced. Deriving `tests_expected`
from what pytest collected would discard the count check that catches
`--collect-only`.

**Resolved a second way by cycle 9.** Cycle 9's allowlist took the
copy-only-allowlisted-files shape this note anticipated, so model-written
tests are now never even copied into the grading directory — independent
of this fix, not superseded by it.

Carried forward as notes from cycle 6:

- **For cycle 8 (first real run).** The transplanted task spec is Phase 1
  only. If cycle 8's run shows the model needs surrounding context the
  omitted phases supplied — a sense of where Phase 1 sits in a larger
  build — that is evidence for how much of the document to transplant,
  not a reason to add commentary to it. The file is model-facing input;
  anything added is a difference from the conditions the trusted number
  was produced under.
- **The load-bearing-facts check, worth applying before any future
  cycle's first run.** From the old branch's research: grep a spec for the
  facts its acceptance suite imports. Anything the suite reaches for that
  the spec never states is a silent dependency on whatever prose happens
  to surround it. Phase 1's suite does `from app import app`; the
  transplanted spec states `app.py` and FastAPI explicitly, so this one
  checks out — but phases 2 and 3, whose suites import `models` and
  `Complaint` by name, are where it would bite.

**Resolved by cycle 8, kept for the record.** Cycle 7's two carried-forward
notes are both closed: the `127.0.0.1:8001` default was re-confirmed
against `BRIEF.md` while writing cycle 8's spec (no drift found), and
`run_agentclinic_phase1()` calls `check_model_server_alive()` first,
letting `ModelServerDown` propagate as an environment failure rather than
a graded verdict — exactly as cycle 7 required.

**Resolved by the first live run, kept for the record.** Cycle 8's review
flagged that `pi`'s stdout/stderr was discarded, and noted it as the first
place to look if a live run came back confusing. It did: the first actual
attempt hit three bugs invisible to fixture-only testing, none caught by
Fable's review because none of them exist without a real server and a
real `pi` process —

1. `check_model_server_alive()` never sent an `Authorization` header.
   `omlx` requires one present (any non-empty value; `"not-needed"`
   works) — without it, a genuinely-up server read as down. Fixed:
   `api_key` parameter (default `"not-needed"`), sent as a Bearer token,
   proven against a stub server that 401s when the header is absent.
2. The `pi` invocation used a `--` separator `pi` doesn't recognize
   (`Unknown option: --`) and never passed `--print`, so it wasn't even
   in non-interactive mode. Confirmed against `pi --help` and a trivial
   live invocation before fixing — the prompt is a plain positional
   argument, no separator needed.
3. The captured diff included `__pycache__/*.pyc` as new binary files.
   Fixed at the time with a `.gitignore` in the now-retired `empty/`
   fixture.

`pi_stdout`/`pi_stderr` were added to `RunResult` while diagnosing bug 2 —
without them, bug 2 would have produced an empty diff and a silent
`accepted=False`, indistinguishable from the model simply failing the
task. With all three fixed, `run_agentclinic_phase1()` completed
successfully: `accepted=True, tests_executed=tests_expected=4,
returncode=0`.

Fable's light review of these fixes (below the fixes themselves) caught a
fourth instance of the same leak: `.pytest_cache/` wasn't in the `empty/`
fixture's `.gitignore` either, and the task spec has the model write its
own smoke test — so `pi` running pytest inside the workspace would create
one, showing up in the diff exactly like the `.pyc` files did. Fixed the
same way, verified the same way (no full model run needed). Cycle 11 later
removed the `empty/` placeholder entirely: `prepare_workspace()` now creates
the empty initial commit directly.

**Considered and deliberately not promoted by the 2026-07-31 harvest
re-plan.** `pi_stdout`/`pi_stderr` are captured, but only on the path
where `subprocess.run` returns normally. On a timeout,
`subprocess.TimeoutExpired` propagates uncaught (as designed — cycle 8's
spec explicitly allows this) and whatever `pi` had printed up to that
point is lost, since `subprocess.run` doesn't expose partial output from
a killed process. Immaterial for a single supervised run; a batch that
needs to diagnose *why* one run out of sixteen hung will want it. Cycle
12 (hang tolerance) makes the batch survive this case, but doesn't
capture partial output when it happens — still not fixed, still no
evidence it's needed, and `subprocess.run`'s timeout handling doesn't
offer partial capture without switching to `Popen` directly, which
remains more machinery than a single unconfirmed need justifies. Revisit
if Cycle 14's actual batch run ever produces a hang worth diagnosing.

**Resolved by cycle 11.** `prepare_workspace` no longer needs the old
`empty/` fixture's `.gitkeep` placeholder: `git commit --allow-empty`
creates a real initial commit from an empty source, while Git hooks and
ambient configuration remain isolated.

**A quiet coverage shift, surfaced by the 2026-08-01 deep review.** Cycle
5's refusal now intercepts the `--collect-only` attack before pytest ever
runs, so `test_collect_only_attack_is_refused_before_any_exit_code_exists`
(cycle 4) and `test_grade_refuses_a_workspace_carrying_config_without_running_pytest`
(cycle 5) assert the same thing by different routes. Both are kept — they
would fail differently if refusal regressed — but the consequence is worth
naming: there is no longer any *end-to-end* proof that the verdict's
count-mismatch logic catches `--collect-only`. Only the unit-level
`test_verdict_rejects_a_partial_run` covers that mechanism now. Not a bug;
worth knowing before anyone assumes the integration path still exercises
it.

Nothing else is currently deferred. Add to this list as later cycles pass
things over.

## Backlog

- Formatting cleanup: `uv run ruff format --check .` currently reports 21
  unformatted files across historical source, specs, and plans. This is
  mechanical, non-behavioral debt, so it stays deferred rather than widening a
  corrective cycle into a noisy rewrite. Revisit as one isolated mechanical
  cycle when a clean repository-wide formatter check is worth the review cost.
- Volunteer-reader / section-structure design (superseded Phase 1 framing;
  revisit once an engine and real suites exist to write about)
- Telemetry (Phase 2): aggregate model/session measurements only after a
  suite author has named a claim they need those measurements to support.
  Phase 1 records accept/reject evidence and complete Pi output, but does not
  infer token, tool, or context-window metrics from it.
- Authoring scaffold for future acceptance suites (phase 2+): stub test
  functions named for the fact they prove, `raise NotImplementedError`
  bodies, a model fills in from owner-dictated bullets, owner reviews by
  tracing each assertion back to its bullet. Not needed for phase 1 (its
  suite already exists, human-authored).
- Which AgentClinic roadmap variant (implementation-detail vs. user-story)
  a model should build from — i.e. *does a spec's abstraction level change
  what a small model can build?* **Promoted to cycle 6 by the 2026-07-30
  re-plan; that promotion is withdrawn.** It is a discovery question, and
  Phase 1 is explicitly a reproduction milestone — `BRIEF.md`: "reproduce a
  number we already trust, not to discover one." With that framing there is
  no choice to make: reproduction uses the document the trusted number was
  produced against, which is the detailed variant. Cycle 6 transplants;
  it does not choose.

  Evidence gathered while the question was (wrongly) live, worth keeping so
  the experiment starts from it rather than re-deriving it — all from
  `user-story-batch`'s
  `docs/section-3-sdd/research/2026-07-29-user-story-workload-is-not-substitutable.md`,
  which carries a PENDING RULE 8 REVIEW banner and is not citable prose:
  - Phase 1, n=16, same model and Pi version this reboot uses: detailed
    spec 16/16 (reproducing the published 15/16); user-story spec 1/16
    bare.
  - The cause is narrow, not a general property of user-story framing. The
    Phase 1 suite's only structural coupling is `from app import app`; the
    detailed spec states it ("Create `app.py` with the FastAPI application
    instance"), the user-story variant never names `app.py`, FastAPI, or
    even that this is Python. Supplying that one fact separately recovered
    the arm to 15/16 — but that recovery is flagged post-hoc in the source,
    "a lead for a pre-registered replication, not a confirmed result," and
    the replication was never run.
  - The generalizable hazard, worth applying to any future suite: **grep a
    spec for the facts its acceptance suite imports.** Anything the suite
    reaches for that the spec never states is a silent dependency.

  Revisit as a deliberate experiment once a trusted number is in hand —
  not during Phase 1.
- Acceptance-suite rules beyond human-authorship (cumulative,
  contract-vs-implementation, non-vacuous, naming convention) — untouched,
  each needs its own argument when it becomes relevant.
- **Out-of-process suite execution. Still Backlog — promoted to a Phase 1
  cycle on 2026-07-31 and withdrawn on 2026-08-01.** Acceptance grading
  trusts a same-process signal a model can forge. A model-authored
  `app.py` can read the results-file path from the environment it shares
  with `harness/grading_plugin.py` and write forged `nodeid<TAB>outcome`
  lines and a completion marker straight into the results file. No
  in-process secret closes it — anything the plugin can read, model code
  sharing its process can read too. Scoped out of cycle 4 by explicit
  decision, not oversight (see that cycle's design doc, "Out of scope for
  this cycle").

  **Research done during the brief promotion, worth keeping — it is
  expensive to re-derive and one half of it is counter-intuitive.**

  *The obvious fix does not work.* Running the app in a separate process
  with `SATYRN_GRADE_RESULTS_PATH` scrubbed does **not** close this. The
  app subprocess globs `$TMPDIR/satyrn-grade-results-*.txt` — the prefix
  is a literal in `grading.py` — and forges a pass, because it runs as
  the same UID that owns the `0600` file. Demonstrated directly, not
  argued: a broken solution graded as `accepted`.

  *What does work, also demonstrated.* Hold the results file's fd, unlink
  its path immediately so nothing is on disk to find, and pass the fd
  only to the trusted pytest process via `pass_fds`. The hostile
  subprocess then found zero glob candidates, no `SATYRN_*` variables,
  and no writable inherited fd, while the real outcome came through
  intact.

  *It is all-or-nothing.* The fd fix only works **after** out-of-process
  execution — in-process, model code reads the fd from its own process
  table or introspects `sys.modules` for the plugin. There is no cheap
  partial version.

  *Two further design findings.* Once the suite talks HTTP, the pytest
  process needs nothing model-written, so the grading directory can split
  into an `app_dir` (allowlisted files) and a `suite_dir` (suite only),
  making the pytest process model-free by construction — and closing an
  unnamed vector where `app.py` could read `test_acceptance.py` at import
  time and craft responses against its literals. Feasibility confirmed
  against real uvicorn subprocesses: `reference` serves 200 with the
  tagline, `broken` serves 404 despite having no `templates/`, both from
  a directory containing no acceptance suite.

  **Why it was withdrawn.** Ranked by severity-if-exploited rather than
  expected value. Forging requires a 12B model to know a grader exists,
  its filename prefix, and its file format — none of which is in the task
  spec it receives. The fidelity case was overstated for *this* suite,
  which asserts a 200, a substring, two links, and a doctype, and touches
  none of where `TestClient` actually diverges from a live server. And
  the acceptance suite is the measuring instrument that produced the
  trusted number: rewriting it during a reproduction phase, at the cost
  of a sixteen-run re-baseline, is the move cycle 6 refused for a single
  bullet of the task spec.

  **What would make it worth building.** Contributors writing suites for
  arbitrary workflows, where the grader's trustworthiness becomes
  load-bearing for a claim someone acts on; a suite that genuinely needs
  real-server semantics (lifespan, streaming, websockets, middleware
  ordering); or models strong enough to reason about their own evaluation
  environment. A natural Phase 2 candidate alongside telemetry. The
  withdrawn cycle-14 design doc
  (`docs/superpowers/specs/2026-08-01-phase1-cycle14-live-server-execution-design.md`)
  is kept as the starting point.
## Prior work

The pre-restructure project lives on the `user-story-batch` branch, untouched.
Nothing there is imported here except by an explicit phase decision.

## Workflow

`restructure` is this reboot's trunk — `main` stays untouched until the whole
reboot is ready to replace the old project. Starting with cycle 2, each
feature cycle branches from `restructure` and merges back to it, never to
`main`.

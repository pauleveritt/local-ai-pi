# Oracle-Invalid Incident: Acceptance Oracle Fails Correct Solutions

**Date:** 2026-07-24
**Status:** closed (oracle repaired, evidence chain rebuilt)

## 1. What happened

The acceptance oracle — `uv run pytest -q` executed in the harness-stamped
workspace after a model run — fails collection for a textbook-correct Phase 1
solution. The verdict is not "the model wrote bad code"; it is "the workspace
is misconfigured such that no correct solution can pass." Every measurement
batch that used this oracle recorded an unstated pytest-configuration puzzle,
not model competence.

The experiment below is reproducible and does not involve a model. A
spec-compliant Phase 1 solution is placed in a freshly stamped workspace
(matching `harness/workspace.py::_stamp_pyproject` exactly, including its
pinned dependency versions). Two runs:

### Run A: without `tests/__init__.py` (fails)

```
$ uv run pytest -q

==================================== ERRORS ====================================
______________________ ERROR collecting tests/test_app.py ______________________
ImportError while importing test module '/…/workspace/tests/test_app.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/…/lib/python3.14/importlib/__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/test_app.py:3: in <module>
    from app import app
E   ModuleNotFoundError: No module named 'app'
=========================== short test summary info ============================
ERROR tests/test_app.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.20s
```

Exit code 2 (errors during collection — an import crash, not "no tests
collected").

### Run B: with `tests/__init__.py` (passes)

```
$ touch tests/__init__.py
$ uv run pytest -q
.                                                                        [100%]
1 passed in 0.71s
```

Exit code 0. The identical solution — same `app.py`, same templates, same
`tests/test_app.py` — passes when a single empty `tests/__init__.py` is
added to the workspace. This file is **not** mentioned in the AgentClinic
spec, the course roadmap, or the phased implementation packet.

## 2. Root cause

- `harness/workspace.py::_stamp_pyproject` writes a `pyproject.toml` with
  **no** `[tool.pytest.ini_options]` section and provisioning creates no
  `conftest.py`. The stamped file contains only `[project]` with name,
  version, requires-python, and three dependencies.

- `uv run pytest -q` does **not** put the workspace root on `sys.path`,
  unlike the prior course's `.venv/bin/python -m pytest` where `python -m`
  adds CWD. When `tests/test_app.py` does `from app import app`, the import
  fails because `app` is not on `sys.path`. This is a command-change
  regression: the prior course used `python -m pytest` (implicit CWD on path);
  this course uses `uv run pytest` (no implicit CWD).

- Adding `tests/__init__.py` makes `tests/` a package, and Python (by default,
  via `testpaths` inference) adds its parent directory to `sys.path` during
  collection. This workaround happens to resolve the import, but nothing in
  the spec requires or mentions it.

## 3. What is invalidated

Every measurement that used `uv run pytest -q` in the stamped workspace
before the oracle was validated. These numbers measured whether the model
stumbled onto one of two unstated workarounds (`tests/__init__.py` or a
`sys.path` hack), not whether it delivered a correct solution.

| Report | Headline | File |
|--------|----------|------|
| SP1 Phase 1 baseline | **0/8** | `2026-07-23-baseline-phase-1.md` |
| SP2 Phase 1 baseline (pre-tuning, first batch) | **3/8** | `../../section-3-sdd/research/2026-07-23-sp2-baseline-phase-1.md` |
| SP2 Phase 1 baseline (post-tuning, first batch) | **4/8** | `../../section-3-sdd/research/2026-07-23-sp2-baseline-phase-1-post-tuning.md` |
| SP2 Phase 1 baseline (pre-tuning, re-run) | **3/8** | `../../section-3-sdd/research/2026-07-24-sp2-baseline-phase-1.md` |
| SP2 Phase 1 baseline (post-tuning, re-run) | **5/8** | `../../section-3-sdd/research/2026-07-24-sp2-baseline-phase-1-post-tuning.md` |
| SP2 deep-dive analysis | built on the above | `../../section-3-sdd/research/2026-07-24-sp2-deep-dive.md` |

In particular:

- The SP1 claim of "0/8 — Phase 1 is the ditch" is an oracle artifact. Every
  SP1 run wrote the correct three files in ~40s (the model is fast at this
  task) but 8/8 failed collection because of the missing pythonpath. The
  model was fine; the workspace was broken.

- The steered-vs-unsteered comparison is confounded: steered runs (SP2) had
  more turns and subagent repair attempts, hence more chances to discover the
  `tests/__init__.py` workaround. The pre-tuning 3/8 and post-tuning 5/8
  cannot be interpreted as competence deltas under this confound.

- The deep-dive's drift mechanism findings (narrowing behavior, overreach
  patterns, false-pass claim analysis) remain informative even though the
  numerical base was contaminated. Its banner on supersession should say so.

## 4. What survives

- **Harness code:** `harness/workspace.py` (except `_stamp_pyproject`, which
  is repaired), `harness/session.py`, `harness/runner.py`, `harness/telemetry.py`
- **Telemetry reader:** `harness/telemetry.py` and the JSONL artifact format
- **Subagent mechanism:** `.pi/extensions/` and `.pi/agents/`
- **Prompts:** `prompts/` and the phased implementation packet format
- **All teaching content about method:** the course's architecture
  (Phases 1–4, SP1/SP2 profiles, scout-then-pool protocol, evidence tiers)
  is structurally sound. Only the numerical claims regenerate.

- **The six invalidated reports:** kept on disk, marked superseded, never
  deleted. They remain part of the historical record as documented in the
  evidence policy (reports are append-only; superseded banners indicate the
  chain has been rebuilt).

## 5. Doctrine extension

> **An oracle's verdict is not evidence until the oracle has been validated
> against a known-good solution.**

A measurement pipeline has three parts: the workload, the subject under test,
and the oracle that judges the subject's output. Validating the subject
without validating the oracle is like calibrating a scale without a reference
weight — you measure something, but you don't know what.

This is not hypothetical. The Tainie project's generalization campaign found
its repo-pytest oracle vacuous: zero tests collected on all 34 targets. The
campaign ran an oracle-repair phase before trusting anything downstream. The
same pattern has now recurred in a different project with a different oracle
mechanism — which is why this is worth elevating to doctrine rather than
treating as a one-off.

The permanent gate is `tests/test_oracle.py` (created in the repair phase of
this incident cycle). It provisions the reference solution through the real
harness and requires the acceptance oracle to pass it. Any change to the
workload, the workspace stamp, or the acceptance command re-triggers this
validation before the next published batch.

## 6. Repair and re-run protocol

See the [oracle-repair implementation plan](../../superpowers/plans/2026-07-24-oracle-repair.md)
for the full task sequence. Summary:

1. Reference solution fixture (spec-compliant, zero workarounds)
2. One-line oracle repair (`pythonpath = ["."]` in the stamped pyproject)
3. Permanent oracle-validation test (`tests/test_oracle.py`)
4. Evidence policy rule 6 (oracle validation gates every batch)
5. Superseded banners on all six invalidated reports
6. Pre-registered scout-then-pool re-run protocol with honest terminal case

Post-repair reports replace the superseded ones in the evidence chain. The
roadmap and all narrative documents are updated to cite the new numbers.

---

## Evidence tier

**GREEN** — the experiment is deterministic and artifact-backed. The Run A
and Run B transcripts above were captured from a fresh temporary workspace
on 2026-07-24, not pasted from memory. The root cause is mechanically
traceable to a single function (`_stamp_pyproject`) and a single CLI change
(`python -m pytest` → `uv run pytest`). The reference solution is committed
as a permanent fixture.

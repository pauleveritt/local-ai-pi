# Pin the Pi version a batch runs against

**Phase:** 3 — Build the extension half (corrective)
**Status:** design, awaiting plan

## Why this cycle

On 2026-08-03, Pi went from 0.82.0 to 0.83.0 **during a working session**.
Every mechanism this project depends on survived the upgrade. Eight
`file:line` citations in a published chapter did not, and nothing in the test
suite could have caught it.

The documentation damage was the visible part. The measurement risk is worse
and quieter: two collaborators on different Pi versions each produce an
internally valid batch, and those batches get compared as though they were
comparable.

## What is already protected, and what is not

**Already protected.** `RunConditions.pi_version` records the version, and
`run_batch` refuses to resume a checkpoint whose conditions differ. A single
batch therefore cannot silently span an upgrade. This has been true since
Phase 1 and needs no change.

**Not protected:**

- Two contributors on different versions producing separately valid,
  wrongly comparable batches.
- A fresh batch starting on a newly upgraded Pi with nobody noticing the
  change happened — exactly what occurred on 2026-08-03.

**Also not protected, and not by this cycle: the model server.** `BRIEF.md`
names oMLX as part of the recorded environment, and `RunConditions` records
nothing about its version or build. Two contributors on identically pinned Pi
but different oMLX builds are the original worry, unaddressed *and*
unrecorded. Saying so matters because the pin must not be read as sufficient
for comparability — it removes one variable, not the set.

**Not fixable by a pin at all:** documentation citations rotting. No version
check can find a stale `file:line`. What a pin buys is that the upgrade
becomes a *decision* someone makes, and re-checking the docs is part of
making it.

## Design

One constant and one comparison.

In `harness/runner.py`, beside `DEFAULT_MODEL`:

```python
EXPECTED_PI_VERSION = "0.83.0"
```

In `run_batch`, immediately after `requested = _conditions(...)` is computed
and before anything expensive happens, raise `RuntimeError` when
`requested.pi_version` differs.

**Why nothing more than that.** `_conditions()` already shells `pi --version`
to populate `RunConditions.pi_version`, and `run_batch` already calls it. An
earlier draft of this design added a `harness/pi_version.py` module, a
`PiVersionMismatch` exception, a `check_pi_version()` function with a seam
parameter, and handling for three failure modes. All of it was deleted on the
owner's challenge not to overengineer, and the deletions are the interesting
part of this record:

| Deleted | Because |
|---|---|
| A second `pi --version` subprocess | The value is already in `requested.pi_version` |
| A new module | Nothing left to put in it |
| A named exception | `run_batch` already raises bare `RuntimeError` and `ValueError`; a new class would be the odd one out |
| A seam parameter | The constant *is* the seam, and it has one reader |
| Missing-binary and bad-exit handling | `_conditions` calls `subprocess.run(..., check=True)`, so `FileNotFoundError` and `CalledProcessError` already fire earlier, with better messages than we would write |

## Scope: batches only

`run_batch` is the only batch entry point. `run_agentclinic_phase1()` and the
test suite do not call it, so a contributor exploring the harness or running
tests is never blocked. Only evidence production requires the pinned version.

There is deliberately **no override** — no environment variable, no flag. An
override would be reached for exactly when someone is in a hurry, which is
when it is least wanted, and it buys nothing: a contributor who genuinely
wants a batch on a newer Pi bumps `EXPECTED_PI_VERSION`, which is a one-line
commit, costs less than remembering a variable name, and leaves a git record
of when the project moved.

## The message is the deliverable

A contributor may meet this on their first batch, and it must not send them
to the source to understand it. It states:

- the expected version and the version found
- that the harness pins Pi so batches stay comparable between contributors
- **both** remedies: install the expected version, **or** bump
  `EXPECTED_PI_VERSION` — and that bumping means re-checking documentation
  that cites Pi by file and line, because those citations do not survive
  upgrades and no test catches them

The second remedy is the one 2026-08-03 argues for. An upgrade should be a
commit made on purpose.

## Testing

- A batch whose recorded `pi_version` differs from `EXPECTED_PI_VERSION`
  raises, and the message names both versions.
- A batch whose version matches proceeds — otherwise the check could be
  refusing everything and the first test would still pass.
- `EXPECTED_PI_VERSION` matches the installed `pi --version`. This is the one
  test that will fail on the *next* upgrade, which is the point: it turns a
  silent drift into a red suite.

  It **skips** when `pi` is not on PATH. `docs/setup.md` says Pi is needed
  only for work that invokes a model, and every other Pi-dependent test here
  is opt-in — so an ungated version test would error for a contributor who
  has done nothing wrong. A contributor with the *wrong* Pi still fails,
  which is the case it exists for. (An earlier draft of this spec justified
  leaving it ungated by saying Pi-dependence "is already true of the
  live-gated tests"; that elided the fact that those *skip*.)

## Documentation

`docs/setup.md` states the pinned version, that batches refuse to run against
anything else, and what to do when a contributor's Pi differs.

The Backlog entry proposing this work is replaced by a record that it was
done, keeping the reasoning that motivated it — and answering a question that
entry raised about itself. It observes that quotations from installed Pi are
deliberately ungated by `tests/test_doc_quotes.py` "precisely because a
contributor's Pi may differ… **Pinning would change that calculus.**" It does
not: the suite must still pass for a contributor without Pi, which is why the
installed-version test skips rather than fails. The record says so, rather
than leaving the question hanging.

## Gates

`uv run pytest && uv run ruff check . && uv run pyrefly check`, plus a clean
strict Sphinx build.

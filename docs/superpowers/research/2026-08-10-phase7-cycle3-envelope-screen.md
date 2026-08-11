# Cycle 3, for real — the exact envelope's brief-only baseline

**Date:** 2026-08-10 (overnight)
**Status:** COMPLETE. 24/24 attempts. See the completion line at the bottom.
**Cell:** [`workloads/svcs/cells/gemma12b-envelope.toml`](../../../workloads/svcs/cells/gemma12b-envelope.toml)
**Arm:** gemma-4-12B, `read,write` only, 16 turns / 30 tools, no shell — the
literal configuration the roadmap names as Cycle 3 and this project has never
actually run before tonight. Every prior gemma number used the looser probe
budget (60/150, `read,bash,edit,write`).

## The headline

**0 of 24 accepted.** All 8 cohort tasks, 3 replicates each, zero accepts.
20 attempts ended `no-changes`, 4 ended `no-progress`. No task, no
replicate, broke the pattern -- `flask-extensions` and
`fastapi-get-registry`, which have short, guessable module paths
(`src/svcs/flask.py`), did not fare any better than the others.

This is a sharp break from the probe-budget frontier (gemma12b 3/8 at n=1,
24-replicate noise floor 46%). The mechanism is not a harness defect; it was
checked directly against the raw tool-execution events, not inferred from
outcome labels or the model's own narration.

## The mechanism, verified against raw events

> **Correction, same night.** This section originally said "Pi's built-in
> tool set is exactly `{read, bash, edit, write}` — confirmed from `pi
> --help`'s own description." That is wrong, and it was wrong because I read
> only `pi --help`'s one-line summary and not its full `Built-in Tool Names:`
> section. Pi has **seven** built-in tools: `read, bash, edit, write, grep,
> find, ls` — the last three are read-only and off by default, but they
> exist. `--tools read,grep,find,ls` is even given as an example invocation
> in Pi's own help text. What's true and load-bearing is narrower than my
> original claim: **this project's `ENVELOPE_TOOLS = "read,write"` constant
> does not include them**, not that Pi lacks the capability. The rest of
> this section is corrected to that narrower, accurate claim.

Under this project's envelope cell (`read,write`, not Pi's full tool set), a
model has no way to enumerate a directory: `read` on a directory returns
`EISDIR: illegal operation on a directory, read`, verified from the actual
`tool_execution_end` event in `magicmock-factory__r1`'s transcript, not from
the model's own claim about what happened.

`magicmock-factory__r1` shows the resulting behavior directly:

1. `read({"path": "."})` → `EISDIR` (three times, varying the path string).
2. `write({"path": "ls_output.sh", "content": "ls -R\n"})` — the model tries
   to *write a script* it has no way to execute, since there is no shell.
3. Six blind guesses at conventional filenames: `README.md` (exists),
   `svcs/__init__.py` (does not — the real layout is `src/svcs/`),
   `requirements.txt`, `setup.py` (neither exists), before reading
   `pyproject.toml`, which happens to reveal the `src/` layout, from which it
   correctly infers `src/svcs/__init__.py` and then `src/svcs/_core.py`.

That sequence is roughly 13 of the arm's 16-turn budget spent on navigation
before a single line of the actual task can begin. `async-cm-enter`'s three
replicates instead gave up outright in one turn each (`stopReason: stop`,
zero tool calls, 3-9 seconds), announcing an intent to search
("I'll search for `class Registry`... I don't have a search tool... I'll list
the files... Wait, I don't have an `ls` tool either") and then producing no
action at all rather than attempting the guess-and-check strategy
`magicmock-factory` used.

## Why this is the mechanism, not a bug to fix

The authoring prompt written earlier tonight
([`../../../workloads/svcs/authoring-prompt.md`](../../../workloads/svcs/authoring-prompt.md))
instructs every contract to name "which file or files must change, and the
exact place in them." That is precisely the information this baseline has
just been shown to lack any tool-based way of discovering on its own. The
contract arm (Cycle 6, running later tonight once the leak-probe readiness
loop clears each task) is not a separate, unrelated measurement — it is the
direct test of whether handing over exactly this missing information closes
the gap this baseline is falling into. A brief-only arm that could `ls`/`grep`
freely would make this comparison weaker, not stronger: the whole point of
the exact envelope's restriction is to remove the capability a contract's
location information is meant to substitute for.

**No tool was added to the brief-only arm to work around this.** Doing so
would eliminate the contrast the rest of tonight's plan depends on measuring
-- and, per the correction above, it is a live option (`grep`/`find`/`ls`
genuinely exist and are cheap, read-only additions), which makes not
touching it a decision, not an oversight. `ENVELOPE_TOOLS` is a deliberate,
named constant (`envelope-cap.ts`'s docstring: calibrated "to an arm with
`--tools read,write` and no way to execute anything," to mirror the real
implementer child's own configuration). Whether that calibration is still
right, now that its consequence is a measured 0/24, is exactly the kind of
grading-instrument change this project's own rule 8 says must not happen
after seeing a result -- so it was not changed tonight. It is named here as
an open question for deliberate daylight review, not resolved by me
unilaterally overnight.

## A second, independent wall: output tokens cannot hold the file

A design-review checkpoint on this result (dispatched before stage 4 spent
anything on the strength of it) found a second mechanism this section
missed entirely, and it is more serious than the first because **no
contract can fix it**.

`autowire__r3` and `stringified-annotations__r1` both *beat* navigation --
found `src/svcs/_core.py` via the `pyproject.toml` inference chain, same as
`magicmock-factory__r1` -- and then ended `stopReason: length` with
`output: 8192` in the raw usage record, exactly the cell's pinned
`max_tokens`. Verified directly: the `read` result immediately before the
truncated response is 35,196 characters (`autowire__r3`) and 25,850
characters (`stringified-annotations__r1`). The envelope has no `edit`
tool -- only whole-file `write` -- so the only way to change `_core.py` is
to emit its entire new content in one response. A ~30-35KB file cannot fit
in an 8192-token response: this is not a probabilistic tendency, it is
arithmetic, and it was hit exactly, twice, independent of what either model
actually tried to say.

**Five of eight cohort tasks pin `candidate_output` to `src/svcs/_core.py`**
(`async-cm-enter`, `local-pings`, `magicmock-factory`, `registry-iter`,
`stringified-annotations`, verified from each task's `manifest.toml`), and
`_core.py` is 29,684-35,196 bytes depending on which task's base commit is
staged. For these five, wall 2 is unconditional: even a contract that
perfectly names the file and line still cannot make the model's response
fit an 8192-token write of that file. Running the contract arm on these
tonight, unchanged, would not measure whether contracts help -- it would
re-measure the output cap, and the predictable near-zero result would read
as "contracts don't help" for a reason that has nothing to do with
contracts.

**The other three tasks are expressible, checked by file size:**

| task | file(s) `write` must produce whole | size |
|---|---|---|
| `flask-extensions` | `src/svcs/flask.py` (existing, rewritten whole) | 7,146 B |
| `fastapi-get-registry` | `src/svcs/fastapi.py` + `src/svcs/starlette.py` (two separate `write` calls, not one blob) | 2,594 B + 6,445 B |
| `autowire` | `src/svcs/_autowire.py` (new file) + a small edit to `src/svcs/__init__.py` | ~8,259 B of added content in the reference patch -- borderline, not confirmed either way |

**Decision for tonight's contract arm: run it on `flask-extensions` and
`fastapi-get-registry`, attempt `autowire` with its borderline status noted,
and exclude the five `_core.py`-pinned tasks from tonight's run with this
reason recorded** -- not silently dropped, and not run to produce a
predictable, uninformative zero. This is a choice about which tasks get
tonight's contract-arm budget, not a change to the envelope's tool
definition; widening `max_tokens` or adding `edit` is left for the same
deliberate daylight review as the tool-set question above.

## What this does NOT show

- **Not evidence about the product.** The roadmap's envelope numbers (16
  turns / 30 tools, `read,write`) mirror the real implementer child's
  budget, per `envelope-cap.ts`'s own docstring — but whether the *product*
  hands its implementer child a raw task with no localization step, or
  whether an earlier stage (a controller, a contract) always supplies exact
  paths first, is a design question this run does not answer by itself. It
  is exactly the question Cycle 6 exists to answer.
- **Not yet replicated model-to-model.** This is gemma only. The conditional
  stage extending to qwen27b under the same envelope (if tonight's budget
  allows) will show whether a stronger model reaches better guesses faster
  through wall 1 -- it cannot show anything different about wall 2, which
  is arithmetic and does not care which model is generating the response.
- **Not a claim that the product's real implementer child hits either
  wall.** Whether the shipped implementer actually runs at `max_tokens:
  8192` with no `edit` tool, or whether an earlier stage in the real
  product already supplies exact paths before the implementer ever runs
  (which would make wall 1 moot for the product even though it is real for
  this bare arm), was not checked -- Pi's own implementer source is not
  part of this repository and was not reachable tonight. This run measures
  this project's own envelope cell, which was built to mirror the product
  by name and citation, not verified against the product's current source
  tonight.

## The turn budget compounds the navigation cost

3 of 24 attempts (`local-pings__r2`, `local-pings__r3`,
`magicmock-factory__r1`) recorded `budget_exhausted: turns` -- the 16-turn
cap, not a wall-clock timeout. `magicmock-factory__r1` is the transcript
read above: it hit the cap right after finally locating `_core.py` via the
`pyproject.toml` inference chain, with no turns left to act on it. Turn
exhaustion does not correlate with the longest wall-clock attempts (several
300-400s attempts never hit it) -- a model making many fast guesses can
exhaust the turn budget quickly in seconds; one reading fewer, larger files
can run long without ever reaching turn 16. Both are the same underlying
cost, spent differently.

## The no-changes / no-progress split is not a capability signal

Checked directly against each attempt's `changed_paths` field: all 4
`no-progress` attempts changed only navigation-workaround files --
`autowire__r1`: `files.txt`; `local-pings__r3`: eight files including
`find_containers.py`, a Python script the model wrote hoping to run it as
its own listing tool; `magicmock-factory__r1`/`r2`: `ls_output.sh` /
`ls_output.txt`. Every one of these is separately flagged `out_of_scope` in
its own record. **Zero of 24 attempts touched a production file.** The
20/4 no-changes/no-progress split looks like it might stratify capability;
it does not, and should not be read as one.

## Verification posture

Checked personally, tonight, against the actual transcript and attempt
files, not inferred from labels or the model's own narration: the raw
`tool_execution_start`/`tool_execution_end` events for `magicmock-factory__r1`
(the `EISDIR` results, the `ls_output.sh` write, the six blind file-path
guesses) and for the two `stopReason: length` truncations
(`autowire__r3`, `stringified-annotations__r1` -- exact `output: 8192` in
the raw usage record, and the preceding `read` result's exact character
count); the `stopReason`/tool-call-count for all three `async-cm-enter`
replicates; the outcome/accepted field for all 24 attempts and the
`changed_paths` field for all 4 no-progress attempts, read directly from
each `<task>.json`; the `candidate_output` pin and reference-patch content
for every task, to build the expressibility table above; Pi's actual
built-in tool list, from the full `pi --help` output rather than its
one-line summary (the correction above).

A design-review checkpoint (dispatched before stage 4 spent anything on
this result) found the second wall independently and first -- credited
above where the finding appears, not hidden behind a separate document. Its
byte-count for `_core.py` (35,196) came from one specific run's `read`
result and differs from this file's own 29,684-byte figure for a different
task's staged copy; both are cited as read, neither is asserted as *the*
canonical file size, since the base commit differs per task.

## Completion

**Complete. 24/24 attempts, 0 accepted, run exited cleanly (no infra-abort,
no deadline).** Two independent, verified mechanisms account for it: no
enumeration tool under `read,write` (wall 1), and an 8192-token output cap
that cannot hold a ~30KB whole-file `write` (wall 2, unconditional for 5 of
8 tasks). Neither was treated as a bug to fix in the envelope cell itself;
both are named as open, deliberate-review questions rather than resolved
unilaterally overnight. Tonight's contract arm proceeds only on the three
tasks wall 2 does not foreclose.

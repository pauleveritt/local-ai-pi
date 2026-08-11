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

Pi's built-in tool set is exactly `{read, bash, edit, write}` — confirmed
from `pi --help`'s own description. There is no separate listing, glob, or
search tool. Under `read,write`, a model has no way to enumerate a
directory: `read` on a directory returns `EISDIR: illegal operation on a
directory, read`, verified from the actual `tool_execution_end` event in
`magicmock-factory__r1`'s transcript, not from the model's own claim about
what happened.

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
would eliminate the contrast the rest of tonight's plan depends on measuring.

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
  allows) will show whether a stronger model reaches better guesses faster,
  or hits the same wall.

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

## Verification posture

Checked personally, tonight, against the actual transcript files: the raw
`tool_execution_start`/`tool_execution_end` events for `magicmock-factory__r1`
(the `EISDIR` results, the `ls_output.sh` write, the six blind file-path
guesses); the `stopReason`/tool-call-count for all three `async-cm-enter`
replicates; the outcome/accepted field for all 24 attempts, read directly
from each `<task>.json`. Not checked: whether `no-progress` attempts (4 of
24) made any edit at all before failing validation, versus failing for the
same navigation reason under a different label -- a closer transcript read
is warranted before citing the no-changes/no-progress split as meaningful,
and is exactly the kind of thing the checkpoint review below was asked to
look for.

## Completion

**Complete. 24/24 attempts, 0 accepted, run exited cleanly (no infra-abort,
no deadline).** A Fable review of this result was dispatched before stage 4
started; its verdict is recorded separately rather than folded in here,
so this file stays what it has been throughout: my own direct read of the
transcripts, not a synthesis.

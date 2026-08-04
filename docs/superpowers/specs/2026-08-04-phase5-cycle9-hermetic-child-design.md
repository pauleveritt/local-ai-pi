# Phase 5 cycle 9 — the hermetic child

**Date:** 2026-08-04
**Status:** design
**Phase:** 5 — the improvement loop

## Why this cycle exists

Cycle 8 asked how to deliver a guard to the delegated child. The research that
answered it found something we were not looking for: **the child has never been
hermetic.** Every orchestrated arm this project has published ran its child
with the operator's personal Pi configuration loaded.

This is a conditions defect, not a bug in the improvement, and it outranks the
runaway child — a runaway is a visible failure, and an unrecorded condition is
an invisible one.

## What is loaded, and the proof it was loaded

The parent is launched hermetically: `--no-extensions --no-skills
--no-prompt-templates --no-themes --no-context-files`. The child is launched by
Pi's shipped subagent extension with

```
--mode json -p --no-session [--model] [--tools] [--append-system-prompt]
```

and **none of those suppression flags**. User-scope resources are trusted by
definition and load unconditionally, so the child picked up
`~/.pi/agent/extensions/` (`rtk.ts`, `ds4-laguna-s-greedy.ts`) and the packages
named in `~/.pi/agent/settings.json` (`superpowers`, `context7`) plus
`~/.agents/skills`. `spawn` passes no `env`, so the child inherits the
environment as well.

`rtk.ts` is not a passive extension. It handles `tool_call` and **rewrites the
child's bash commands** — `ls -R` becomes `rtk ls -R`, `python3 -m pytest
tests/test_app.py` becomes `rtk pytest tests/test_app.py` (verified by running
`rtk rewrite` on both).

**This is confirmed in our own recorded data, not merely inferred.** The child
transcript in cycle 7's checkpoint records `ls -R` returning a flat,
size-annotated listing:

```
templates/
hooks/
...
COMMIT_EDITMSG  24B
HEAD  23B
config  137B
```

Real `ls -R` prints `dir:` headers and no sizes. That output is `rtk ls -R`,
reproduced byte-for-byte in a scratch git repo. **The child was running rtk.**

## What this costs the record

Every arm whose child delegated — cycle 2's n=16 orchestrated arm, cycle 4's,
and the cycle 5–8 pilots — is affected. The bare arms are unaffected: no child,
no contamination.

It does **not** invalidate the phase's headline comparisons, because the
contamination was constant across the arms being compared, and the corrections
in cycles 5–7 acted on the parent's prompt. It does mean **the orchestrated
arms measure "our orchestrator plus the operator's toolbelt"**, which is not
what any record says they measure. Affected records get a correction banner,
following the cycle 2 token-counting precedent.

It also means `RunConditions` — whose whole job is to make a run's conditions
citable — has been silent about a resource set that could change between two
runs on the same machine without any harness change at all.

## The fix, and why this one

`PI_CODING_AGENT_DIR` overrides the config directory (`docs/environment-
variables.md:76`) and, being an environment variable, **is inherited by the
child**. A harness-owned agent dir therefore fixes both problems at once:

- the child stops seeing rtk, the packages, and the skills;
- `extensions/loop-breaker.ts` placed in that dir is a *user-scope* extension,
  so the child loads it unconditionally — the guard delivery cycle 8 could not
  achieve.

One environment variable. No fork of the shipped extension, no new subagent
tool, no Pi changes. Per the standing decision to take the simplest available
option, this is it.

**Rejected for now:** building our own subagent tool (still gated and still
justified, but strictly larger), and adopting `pi-subagents`, whose result
payload would not match the `tool_execution_end → result.details.results[]`
shape `harness/telemetry.py` parses — breaking comparability with every arm we
have published, in exchange for features this env var already buys.

## What the harness-owned dir contains

Checked into the repo at `pi-agent-dir/`:

- `settings.json` — **no** `packages`, **no** `skills`. The operator's other
  keys (`compaction`, `defaultThinkingLevel`) are carried over deliberately, so
  the *parent's* behaviour does not change with this cycle; changing them would
  confound the arm.
- `models.json` — the `omlx` provider and the single model we run, transcribed
  from the operator's file. Checking it in makes the provider definition a
  recorded condition instead of a machine fact.
- `extensions/loop-breaker.ts` — the guard, now reaching the child.

**Not** copied: `auth.json`. The `omlx` provider carries `"apiKey":
"not-needed"`, so nothing is required, and a harness directory that never holds
credentials is the correct shape regardless.

The parent keeps its explicit `--extension` for the loop-breaker: with
`--no-extensions` it will not auto-discover the user-scope copy, and its
conditions should not silently change.

## Pre-registered predictions

1. **The child's bash commands stop being rewritten** — no `rtk`-shaped output
   in any child transcript. This is the cycle's real assertion and it is
   near-certain; it is registered so the check is performed rather than assumed.
2. **The loop-breaker fires in the child**, producing the first `loop_broken`
   entries this project has ever recorded from live runs. Given cycle 8's run 1
   repeated `ls -R` 83 times, at least one run should trip the 5-in-20 rule.
3. **Timeouts fall.** Weak, n=6, and the same contention caveat as cycle 7
   applies — throughput is measured per pilot before any claim is made.
4. **Grader-accepted does not fall.** The guard must not break working runs.
   A drop here is the outcome that would send this back for redesign.

## Verification

1. Unit: the agent dir is materialized and its digest lands in `RunConditions`.
2. Static: `settings.json` names no packages and no skills; no `auth.json`.
3. One smoke run: grep the child transcript for rtk's signature output.
4. n=6 pilot at `run_timeout=300`, uncontended, throughput recorded.

## What this does to the n=16 arm

The n=16 arm was to run next on cycle 8's configuration. **It should run on
this one instead.** Knowingly publishing an arm whose child loads the
operator's toolbelt, after discovering that it does, would be indefensible —
and the arm is the expensive artifact this phase is meant to leave behind.

## Out of scope

- Our own subagent tool. Gated, justified, larger, and not needed for this.
- A turn cap. Pi has none at any level (CLI, settings, agent frontmatter); the
  SDK's `shouldStopAfterTurn` is not wired to anything a CLI user can reach,
  and upstream closed the request for `--max-turns` without implementing it.
  A cap by `ctx.abort()` is possible as a companion extension, but it converts
  a runaway into a *failed* delegation rather than a salvaged one, so the
  loop-breaker's block-with-reason is tried first.

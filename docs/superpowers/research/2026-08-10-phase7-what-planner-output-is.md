# What planner output is — settled

**Date:** 2026-08-10
**Status:** decision. Blocks the contract baseline until implemented; nothing
further is authored under the old prompt.
**Plan:** [`../plans/2026-08-09-phase7-workload-first-roadmap.md`](../plans/2026-08-09-phase7-workload-first-roadmap.md)
**Basis:** [`2026-08-10-phase7-frontier-contracts-variance.md`](2026-08-10-phase7-frontier-contracts-variance.md)

---

## The decision

**Planner output is a contract that locates and bounds the work. It does not
contain the implementation.**

A contract may name the file and the extension point, state the invariants,
describe the required behaviour, give a signature, show how the API is called,
and say how a reader would know the work is done. It may not contain the
statements that constitute the change.

## Why this and not the alternatives

Three products were available and the current authoring prompt chose one by
accident.

**Solution-bearing plan, safely transcribed — rejected.** This is what the
existing drafts are, and what Experiment A actually measured: a 27B derived the
whole fix and a 12B transcribed it 5 times in 6. It works, and it is a coherent
product. It is rejected because it answers a question that defeats itself — if
the planner must derive the complete fix, the honest comparison is not against
brief-only but against *letting the planner make the edit*. A pipeline whose
strong half does the thinking competes with "use the stronger model", and the
brief's pitch is not "run two models".

**Requirements-only, to improve reasoning — rejected.** Abstract requirements
discard the one benefit there is direct evidence for. The measured navigation
tax is **41–47% of every run's tool calls before the first edit**, on every
model, rediscovering the same file. A contract that withholds location leaves
that cost in place and measures nothing that the brief does not already say.

**Locating and bounding — chosen.** It removes a cost we have measured, leaves
the implementation as the executor's own work, and matches what the owner
described wanting: a roadmap, a tech stack, a domain document — situating
material, produced up front, so the engine can do bounded work afterwards. The
cohort's briefs are already right-sized in *scope*; what they withhold is
*context*, and that is the gap this fills.

It also makes the arm's comparison well-defined. Baseline is brief-only. The
contract adds location and bounds. Any delta is attributable to knowing where
and what, not to having been handed the answer.

## What this costs

Every existing draft is void. Three of the eight are empty stubs; the other
five are solution-bearing, verified mechanically:

| task | solution statements in fences |
|---|---|
| `registry-iter` | 12 |
| `local-pings` | 12 |
| `autowire` | 11 |
| `stringified-annotations` | 6 |
| `flask-extensions` | 0 (a shell command only) |
| three stubs | 0 (empty) |

`flask-extensions` passes the gate — its fences hold a `pytest` command, not
code — and is void anyway, because it was authored under the superseded prompt
and a contract's provenance is part of the arm. The gate and the decision are
not the same bar, and conflating them would let one draft through on a
technicality.

Experiment A's 5/6 does not transfer. It measured transcription of a contract
that will no longer exist, and it may not be cited as a contract-arm result
under the new definition.

## Enforcement, and its limits

A prompt alone will not hold this. The current prompt never said "do not write
the code" and the author helpfully complied; a rule stated once in prose is
exactly what this project has repeatedly found insufficient.

`tools/author_contract.py` now rejects a draft whose fenced blocks contain more
than two Python statements — `return`, `if`, `for`, `import`, an assignment, and
so on. Rejected drafts are deleted rather than left on disk, because a rejected
draft that stays is one the next sweep silently uses.

**The gate is a heuristic and is documented as one.** It cannot distinguish
code that *illustrates the problem* from code that *is the answer*:
`stringified-annotations`'s draft shows the current guard and the fixed guard,
and both read the same to a line matcher. It errs toward rejection, which costs
one authoring call (~9 minutes) and is the cheaper error. A draft that passes
the gate is not thereby proven free of the answer — it is proven free of the
shape the answer usually takes, and the first read of any new draft should
still ask.

## What these numbers do NOT show

- **Nothing about whether locating contracts help.** That is the experiment this
  decision makes possible; it has not been run. The honest prior is uncertain:
  the failures we catalogued are conduct and mechanics, not navigation, and a
  contract that fixes location may move none of them.
- **Nothing that rescues Experiment A.** Its result stands as a transcription
  finding and is retired as contract-arm evidence.
- **No claim that the gate is sufficient.** It bounds one failure mode of
  authoring, not the space of ways a contract can leak an answer.

## Verification posture

Checked personally: the solution-statement counts above, run over all eight
committed drafts; that the three stubs are 29–80 bytes of preamble; that the
`registry-iter` draft contains a complete `__iter__` with its own docstring
rather than the reference's, which is why exact-overlap against the reference
patch reports only 23% and is the wrong instrument for this question. Relayed
without re-derivation: the 41–47% navigation-tax figure, measured earlier in the
phase.

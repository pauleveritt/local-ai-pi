# Cycle 1, first attempt — stopped at 3 of 8, no transcripts

Kept, not deleted. These are three real graded attempts under rule 5, and
they cost three model calls.

## Why it was stopped

`screen_task` discarded `child.stdout`. `magicmock-factory` ran for 561
seconds and wrote nothing, and there was no way to tell whether it hit the
30-tool-call cap while still exploring, reasoned its way out of a correct
edit, or never understood the brief. Those are three different findings with
three different responses.

Stopping at 3 of 8 cost about thirteen minutes of redone work. Finishing blind
would have produced four or five more results in the same condition, each
needing its own re-run to interpret — and this phase was rebuilt specifically
to stop paying for long runs that end up uninterpretable.

## Standing when stopped

| Task | Gap closed | Accepted | Time | Note |
|---|---|---|---|---|
| `registry-iter` | 100% | no | 122s | correct fix, also wrote `tests/test_registry.py` |
| `async-cm-enter` | 100% | **yes** | 281s | clean, in scope |
| `magicmock-factory` | 0% | no | 561s | wrote nothing; unexplained |

## What they are still good for

The rerun repeats all three, so these become a free variance datapoint on three
tasks — the same executor, same arm, same grading rule, two independent
attempts. Cycle 4 sizes variance deliberately on one cell; this is three cells
of it for nothing.

They are **not** poolable with the rerun. Two attempts of the same task under
the same conditions are two replicates, and reporting either set as "the"
Cycle 1 result would be picking the run that reads better.

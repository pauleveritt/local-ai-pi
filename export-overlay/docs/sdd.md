# How changes get made

The short version of a practice the research repository documents at
length. What matters here is what review will actually hold you to.

## Before the code

For anything beyond a small fix, write down **what you're building and
why** before building it — a paragraph is often enough. The value isn't
ceremony; it's that a design you can state plainly is one you can be
argued out of cheaply, and this project has been argued out of several
good-sounding ideas at that stage rather than after the code existed.

For a large change, say so in an issue first. The
[concept budget](contributing.md#conventions) is real: a change that
adds a term everyone has to learn is more expensive than it looks.

## While writing it

**Test first where you can.** Not dogma — but this codebase's recurring
failure is the test that passes without testing its claim, and writing
the test before the fix is the cheapest way to know it fails for the
right reason.

**Verify, don't assert.** If you claim a fix works, show it: stash the
fix, watch the new test fail, restore, watch it pass. If you claim a
refusal fires, trigger it. Commit messages here record what was
demonstrated, not what was intended.

**Record the why, not the what.** The code says what it does. Comments
in this repository exist to say why it's like that — usually naming the
specific failure that made it so. When you fix something subtle, leave
the reason behind; several comments here are the only surviving record
of a bug that took a day to find.

## Before you push

```bash
uv run pytest
bun test
uv run ruff check . && uv run ruff format --check .
uv run pyrefly check
```

All green on a clean checkout. If one is red and you didn't cause it,
say so rather than working around it.

## What good looks like here

A change that deletes as much as it adds; a test that would fail if the
thing it names broke; a comment a stranger could use to decide whether
your reasoning still applies. The full spec-and-plan practice, and the
cycle-by-cycle record of how these habits were arrived at, live in the
research repository this one is exported from.

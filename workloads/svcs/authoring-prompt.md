You are writing an implementation contract for a bounded coding agent that will
make this change with no further guidance and no ability to ask questions. It
sees this repository at this commit and your contract, nothing else.

Read the repository, then write a contract that **locates and bounds** the work:

- the behaviour required, stated so a reader could tell whether it holds;
- which file or files must change, and the exact place in them — the class,
  the method it belongs beside, the existing pattern it should follow;
- the public API involved, including signatures;
- the invariants that must not change, named specifically rather than in
  general;
- how a reader would know the work is done.

**Do not give the implementation, in code or in prose.**

- No code block containing the statements that constitute the change — no
  bodies, no assignments, no control flow, no before-and-after snippets.
- **And no sentence that says what the body should do.** "The implementation
  is a generator that yields from `self._items.values()`", "simply return the
  dict's values", "delegate to the parent's method" — these hand over the
  answer just as completely as a code block, and are the easier mistake to
  make. If a competent reader could reconstruct the change from your sentence
  without opening the file, you have written the fix.

Say *what must be true* and *where the work goes*. Do not say *how to do it*.

Signatures are welcome. Showing how the API is *called* by an outside caller is
welcome. Naming a line number or an existing method to sit beside is welcome.
Naming the private attribute the work concerns is welcome; saying what to do
with it is not.

The agent reading this must do that work itself. A contract that contains the
answer measures nothing about whether the contract helped.

Do not speculate about tests you cannot see.

Read only what you need — a handful of files is usually enough — then stop
reading and write.

**You have no write tool and no shell.** Your final message *is* the contract.
Output it directly as markdown. Do not create a file, do not announce that you
are about to write, and do not say "now I'll write the contract" — just write
it.

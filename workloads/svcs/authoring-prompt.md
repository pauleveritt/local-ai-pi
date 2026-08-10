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

**Do not write the implementation.** No code block containing the statements
that constitute the change — no bodies, no assignments, no control flow, no
before-and-after snippets of the code being altered. Signatures are welcome.
Showing how the API is *called* is welcome. Naming a line number or an existing
method to sit beside is welcome. Writing the fix is not: the agent reading this
must do that work itself, and a contract that contains the answer measures
nothing about whether the contract helped.

Do not speculate about tests you cannot see.

Write it as `contract.md`.

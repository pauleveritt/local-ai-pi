# Roadmap: satyrn-engine

Read `BRIEF.md` first. This list is settled; brainstorm within a phase, not
across the list.

Each phase ends with **a command a contributor can run**, and evidence that
names a success fixture and a failure fixture. A phase never includes
publishing, polish, or an abstraction that only a later phase needs.

## Phases

| # | Delivers | Done when | Explicitly out |
|---|---|---|---|
| **E1** | `satyrn-engine check --repo REPO CONTRACT` | A checkout install accepts one valid contract and refuses invalid YAML, an impossible path, and a missing required field, with distinct stable exit codes. No process and no model is started. The default test tier passes in single-digit seconds, and a **planted process-spawning test fails the build** (demonstrated once, then kept as a fixture). | Pi, delivery, mutation, publishing |
| **E2** | `/implement CONTRACT` reaches E1 through the TypeScript adapter | A real Pi print-mode fixture receives the same named refusal. Success, missing executable, malformed output, non-zero exit, timeout, and parent-death orphan cases all pass, **on POSIX and Windows**. | Persistent process, mutation, model call |
| **E3** | `satyrn-engine deliver --repo REPO --contract CONTRACT -- ATTEMPT...` creates or discards a candidate ref | Delivery runs `ATTEMPT... CONTRACT` in an isolated worktree. A trivial executable produces a valid patch and a candidate ref. Dirty-tree, linked-worktree, timeout and validation-failure paths leave the caller's tree and HEAD unchanged — asserted by snapshotting `git status --porcelain` and HEAD before and after. | Pi child, grading, measurement |
| **E4** | One bounded file replacement runs Pi → TypeScript → Python | A fixture replacement succeeds. Stale revision, undeclared path, missing anchor and ambiguous anchor each refuse. The adapter never throws. | General edit language, symbol analysis, guards |
| **E5** | `satyrn-engine attempt CONTRACT` and `/implement CONTRACT` complete one named task from a source checkout | `attempt` writes only inside its own disposable worktree. `/implement` supplies E3's isolation around the same command. One real model attempt uses E4's bounded replacement and leaves a candidate ref, a transcript and a receipt. | Packaging, multiple tasks, performance claims |
| **E6** | The same `/implement`, packaged | Works outside either source checkout, on POSIX and Windows, and records an immutable engine identity. | Auto-update, publishing claims |

## The guards

Copied in verbatim at repository creation: `engine.ts` and its replay
fixtures. Zero dependencies; `engine.ts` imports nothing local, so installing
it is a directory copy.

They are **not a phase** and must not be improved in transit. Their replay
fixtures pin the behavior — one fixture on which a guard must fire, one on
which it must stay silent — driven against the *shipped* file, not the source
it was built from.

## E2 is the architecture gate

If the adapter cannot keep failures bounded and legible on both platforms
without growing a supervisor, **stop and reconsider TypeScript-versus-Python
before building E3–E6.** That is the point at which the core decision is still
cheap to reverse.

## E4 is the scope-blowup risk

It implements **one** replacement operation. The prior engine's no-op-edit,
symbol-loss, cross-file-move and oversized-proposal rules are candidates for
later slices, not one large port. Nothing beyond the four named refusals is in
scope.

One tax disappears here: porting TypeScript to Python inverts the `fnmatch`
problem. Python's `fnmatch` becomes the reference semantics — `*` crossing `/`
is the behavior, not a divergence to hand-port — and the differential-test
burden dies with the TypeScript implementation.

## Deferred, with the condition that reopens each

- **A persistent sidecar.** Reopens when per-operation startup is *measured*
  as a material cost against a real batch. The request and response objects do
  not change when it does.
- **A subinterpreter pool.** Reopens when a caller is concurrent. The current
  caller is strictly sequential.
- **Guards in Python.** Reopens only if the everyday path acquires a Python
  prerequisite for some other reason. Note the argument that latency forbids
  it is *wrong* — tool calls are seconds apart — so do not re-derive it and
  reach the right answer for the wrong reason. The real objections are the
  install story, blast radius inside `emitToolCall`, and the replay-fixture
  gap.
- **Contract authoring.** Stays a main-agent skill.
- **A four-method protocol.** Start with one operation. Add another only when
  a vertical slice consumes it.

## Concept budget

Maintained from phase one. One row per term: what it means, and the phase that
introduced it. A term earns its place by naming something the design actually
needs.

Seed terms: **contract**, **candidate**, **receipt**, **adapter**, **guard**,
**worktree isolation**.

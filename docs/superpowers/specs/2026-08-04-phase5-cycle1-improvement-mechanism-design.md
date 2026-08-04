# Phase 5 cycle 1 — the improvement mechanism

**Date:** 2026-08-04
**Status:** design, awaiting owner review
**Phase:** 5 — the improvement loop

All `file:line` citations in this document were verified at `0be8c7c` on
2026-08-04.

## Purpose

Give the harness one thing it cannot say today: *this run had something
applied to it* — and prove one delegation actually happens under this
harness's flags.

**This cycle claims no number and runs no batch**, following Phase 4 cycle
1's precedent. The cost batches are cycle 2. The split is deliberate: a batch
requires a cross-session commit freeze and hours of sequential wall time,
while everything here is provable against fixtures plus one live invocation.
Bundling them would mean discovering a mechanism defect after paying for the
evidence.

The cycle touches no suite. Its live spike runs against
`AGENTCLINIC_PHASE_1`, already in the repository with its grader floor
already proven.

## Why cycle 2's cost question is answerable on a saturated workload

Bare Pi scored 16/16 on AgentClinic Phase 1 in the supervised batch, and the
prior project's orchestrated arm on the same detailed roadmap also scored
16/16. A success rate that cannot move is normally a dead end. Here it is the
control: with the verdict pinned on both arms, every difference in turns and
`context_processed` is attributable to the orchestration, not to one arm
solving a different amount of the problem.

What an improvement *buys* is not observable there at all, and belongs to the
suite with headroom in cycle 3.

## What gets built

### `Improvement` — a descriptor, not a manifest

```python
@dataclass(frozen=True)
class Improvement:
    name: str
    seed_dir: Path | None          # copied into the workspace before git init
    extensions: tuple[Path, ...]   # appended to EXTENSIONS
    system_prompt: Path | None     # passed as --append-system-prompt
```

An earlier framing of this phase called for a directory per improvement plus
a manifest file the harness parses. That is dropped as a cathedral: `Suite`
already establishes the pattern of a frozen descriptor naming paths, the
harness already knows how to digest paths, and a manifest format is a parser,
a schema, and an error path bought for no present caller. If a contributor
ever needs to add an improvement without editing Python, that is the cycle
that adds the manifest.

`run_batch(checkpoint_path, *, suite, target, model, improvement=None)` and
`run_suite(suite, *, model, timeout, improvement=None)`. A run has exactly one
improvement or none. Nothing composes two.

### The three seams it uses, all of which already exist

- **Seeding.** `prepare_workspace(source_dir)` copies, *then* git-inits and
  commits (`harness/workspace.py:31-68`). Improvement files therefore land in
  the initial commit and never appear in the diff, which is what makes
  `.pi/agents/implementer.md` placeable without polluting the record of what
  the model wrote. `Suite`'s docstring notes this parameter has no caller
  today; the improvement is its first.
- **Extensions.** `run_suite` currently binds `extensions = EXTENSIONS`
  locally (`harness/runner.py:114`). It becomes `EXTENSIONS +
  improvement.extensions`.
- **The command.** `_pi_command` gains `--append-system-prompt <path>` when
  the improvement supplies one. The orchestrator prompt is passed by flag and
  deliberately does **not** live in `.pi/agents/`: any `.md` there carrying
  `name:`/`description:` frontmatter is discovered as a *callable specialist*,
  so an orchestrator kept there could delegate to itself with no depth cap.

### Digesting a directory tree

`_extension_digest` raises on a directory today, and its docstring defers the
decision to "the cycle that needs it" (`harness/runner.py:176-185`). This is
that cycle: Pi's shipped subagent extension is a directory.

The rule: hash each file's contents, pair each with its path relative to the
tree root, sort the pairs, and hash the sorted list. Order-independent,
content-addressed, and machine-independent — the shipped extension lives at a
different absolute path on every contributor's machine and moves on every Pi
upgrade, so a path-based digest would report drift that isn't there and miss
drift that is.

### `RunConditions` — one break, three fields

Adding any field makes existing checkpoints non-matching, and roughly 80
recorded evidence runs live outside version control in
`~/local-ai-pi-evidence/`. So the break happens once and carries everything
owed:

| Field | Why |
|---|---|
| `improvement_name: str` | `"none"` when absent. A human reading a checkpoint line can tell the arms apart without a digest table. |
| `improvement_digest: str` | `"<none>"` when absent. Contents, so an edited agent file cannot silently resume. |
| `acceptance_sha256: str` | Backlog debt. `harness_revision` is `git rev-parse HEAD`, which an **uncommitted** acceptance edit sails past. |
| `source_allowlist: tuple[str, ...]` | Backlog debt. Recorded verbatim rather than digested — it is three short strings, and a reader should be able to see them. |

Records written before this cycle load with the sentinel `"<pre-phase5>"`
(and `("<pre-phase5>",)` for the allowlist), following the `("<pre-cycle1>",)`
precedent at `harness/runner.py:65-68`. Old checkpoints stay readable and
recomputable; no SHA-256 or real allowlist can equal a sentinel, so
`run_batch` refuses to resume them. Unresumable is a smaller loss than
unreadable.

The two acceptance/allowlist digests are an **early payment**, not a
satisfied gate. Their Backlog gate asked for a triggering event and none has
occurred; what changed is that the break is happening anyway, so their
marginal cost is zero. Recorded so nobody later reads this as the gate having
fired.

### Improvement #1 — `sdd-orchestrator`

Two authored markdown files and Pi's shipped extension. No TypeScript.

- `improvements/sdd-orchestrator/seed/.pi/agents/implementer.md` — frontmatter
  (`name`, `description`, `tools: read,write,bash`, `model`) plus a body
  teaching it to build exactly what the packet specifies and to run the
  validation command before reporting.
- `improvements/sdd-orchestrator/orchestrator.md` — the parent system prompt:
  extract the task from the roadmap, construct a handoff packet, delegate,
  verify.
- Pi's shipped `examples/extensions/subagent/`, resolved from the `pi` binary's
  own install location rather than a checkout.

The packet shape is inherited from the prior project's approved spec: Task,
Allowed Files, Acceptance Strings, Validation. It is a starting point to be
measured, not a claim.

## The gating spike, before any batch

Three facts about delegation are known only from the prior project's reading
and have never been observed under *this* harness's flags:

1. A delegation must pass `agentScope: "both"` or `.pi/agents/` is never read.
2. The project-local confirmation prompt only fires when a UI is present, so
   headless runs bypass it silently.
3. `--no-extensions` excludes project-local extensions; the shipped subagent
   extension must arrive by explicit `--extension`.

Phase 3 cycle 1's precedent applies: a claim justified by reading, not by a
run, was wrong and was retired when a run disagreed. So cycle 1 runs **one**
live invocation with the improvement applied and confirms a `subagent` tool
call appears in captured stdout with a child result, before anything else is
built on top. If it does not, that finding is the cycle's deliverable and the
batch does not happen.

Run it in the foreground. A backgrounded live run was torn down mid-flight by
its controlling process during Phase 4 cycle 1, and a dead run leaves no trace
in the harness's records.

## Verification

Every seam ships with a mutation check: apply the break, watch a *named* test
fail, revert. Phase 4 cycle 1's near-miss is the reason — replacing `suite.*`
with the old constant at six sites left the whole suite green, so the seam was
correct but unproven.

| Seam | Mutation | Named test that must fail |
|---|---|---|
| improvement digest | edit a seeded agent file | `test_editing_a_seeded_file_changes_conditions` |
| acceptance digest | edit the acceptance file, leave it uncommitted | `test_uncommitted_acceptance_edit_changes_conditions` |
| allowlist recorded | change a suite's `source_allowlist` | `test_changing_the_allowlist_changes_conditions` |
| directory digest | change one file deep in the tree | `test_tree_digest_changes_on_any_nested_file` |
| directory digest is path-independent | copy the tree to another location | `test_tree_digest_ignores_the_trees_own_path` |
| sentinel refusal | hand `run_batch` a pre-phase-5 checkpoint | `test_run_batch_refuses_a_pre_phase5_checkpoint` |
| seeding | drop `seed_dir` from the copy step | `test_seeded_agent_file_is_present_in_the_workspace` |
| seeded files stay out of the diff | — | `test_seeded_files_do_not_appear_in_the_run_diff` |

Implementer self-reports do not count. A subagent during Phase 4 cycle 1
reported "2 passed" for tests that did not exist; every claim here is re-run
independently.

## Pre-registered predictions for cycle 2

Recorded here, in the cycle that builds the mechanism, so they are on paper
before the mechanism that will test them even exists. They come from a prior
series carrying a `PENDING RULE 8 REVIEW` banner: predictions to replicate or
falsify, **never** citable as results.

1. Both arms accept 16/16. The bare arm reproduces Phase 1; the orchestrated
   arm matches the prior project's detailed-roadmap arm.
2. The orchestrated arm's `context_processed` is higher. That is the
   handoff-packet claim; a null or negative result is equally publishable and
   is the reason the cycle exists.
3. Delegation occurs on 16/16 orchestrated runs. The prior series measured
   dispatch at 13–16 of 16 on a *different* roadmap variant, with one run
   indeterminate because a hung non-dispatcher cannot be observed as one.

Riding along in cycle 2 as an observation, not a prediction: whether the shipped
extension puts **parallel children** on the single-threaded local server. The
Backlog gates building our own ~150-line subagent tool on a measured run
showing the shipped extension contaminating or losing a measurement. This is
the project's first measured orchestrated run, so it is the first chance for
that gate to fire — and the own-tool is the honest path toward something
installable.

## Operating conditions for the live spike

Confirm the model server returns real output first —
`curl -s -m 10 http://127.0.0.1:8001/v1/models`. When it is down, `pi` exits 0
with empty stderr and the harness records a fabricated result that looks like
data (`docs/setup.md`).

One invocation is not a batch and needs no commit freeze. Cycle 2's batches
do: `_conditions` re-reads `HEAD` per run, so a commit in *any* session aborts
a batch in flight. That freeze is agreed with the owner across sessions, never
self-imposed.

## Out of scope

- **The cost batches.** Cycle 2. This cycle produces the mechanism they need
  and the predictions they test, and nothing else.
- **Automated comparison.** Running the loop by hand twice is how we learn
  what a comparison must refuse. Building the refusal first is machinery ahead
  of its contract.
- **Parent/child telemetry attribution.** The parent's `tool_execution_end`
  already carries what this cycle's question needs.
- **Our own subagent tool.** Gated on the observation above.
- **A second suite.** Cycle 3. *(Renumbered 2026-08-04: a telemetry cycle was inserted as cycle 3, so the suite is cycle 4 and tuning is cycle 5+.)*
- **More specialists** (`validator`, `scout`). They are improvements #2 and
  #3, which is the point of the mechanism.

## Concept budget

Spends `improvement`, already added to the table with the reasoning for
preferring it over `intervention` and `arm`. Revives `orchestrator` and
`handoff packet` on the retirement note's own terms. `Improvement`,
`improvement_digest`, and the sentinel are field and type names, not concepts
a contributor must hold.

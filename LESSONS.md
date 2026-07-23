# Lessons for Helping Small Local Coding Models

These lessons came from repeated OpenCode runs, session telemetry, generated
code, and validation results. They are ranked by demonstrated impact. Treat
them as controls for a system, not as claims about a model's character: the
same model can look capable or unreliable depending on scope, tools, context,
and stopping conditions.

## 1. Remove decisions from the SLM

Small local models do best at routine, bounded work, not open-ended
"galaxy-brain" problem solving. Give them a complete implementation packet:
the one phase, files they may change, exact behavior to preserve, acceptance
checks, and one validation command. Let stronger reasoning, human judgment, or
the broader community's training work handle novelty.

The durable strategy is to remove decisions from the model, not to add another
prompt rule. A rule such as "repair at most twice" still relies on the SLM to
count its own loop; a mechanical stop or fresh repair packet does not.

This is the "structure beats strings" principle. A model should not be expected
to remember that a call site matches a signature three files away, a registration
string matches a module path, or an edit anchor matches the file byte-for-byte.
Represent and enforce those relationships with codebase structure, deterministic
tools, and explicit handoff data.

## 2. Treat telemetry and validation as the source of truth

Nothing matters except evidence. An agent's report is not reliable evidence: it
can claim success while missing a contract requirement, or give a plausible
explanation for slowness that the trace disproves. Hunches about local AI are
usually wrong until session records, tool outputs, and validation results agree.

After every meaningful run, inspect parent and child telemetry, tool outputs,
and the actual diff. Use the host-local repository skill in
[Codex](.codex/skills/opencode-telemetry/SKILL.md) or
[OpenCode](.opencode/skills/opencode-telemetry/SKILL.md). Both skills use the
same read-only collector, follow nested sessions, identify context risks, and
report evidence-based metrics.

Live local runs also showed that generation throughput can fall sharply as a
conversation grows: one model fell from about 60 tokens/second at turn zero to
38-42 by turn four. Measure both turn count and per-turn speed; multi-turn
prefill cost compounds, so a long context is a latency problem even when it
still fits the model window.

## 3. Use spec-driven development with small, isolated phases

Turn a feature into small phase contracts, then hand each contract from a
big-brain planner to a little-brain implementer. The largest gains came from a
fresh child responsible for one phase, with only the named files, exact
user-visible strings, preservation requirements, and validation command.

Do not send the full roadmap, prior summaries, or unrelated repair history
unless the child actually needs them. Phase 2 is especially sensitive to packet
size: broad context and growing test files repeatedly turned ordinary
implementation into long repair loops.

The environment is part of the phase contract. A declared FastAPI version and
an installed Starlette version can imply different APIs. Pin the intended
Python and package versions in `pyproject.toml` and `uv.lock`, run every tier
with the same lock, and treat a spec/environment mismatch as an experiment
failure rather than a model failure.

## 4. Separate orchestration, implementation, and verification

Give each role a small, inspectable responsibility. The orchestrator prepares
the packet, keeps context lean, evaluates acceptance criteria, and issues at
most one focused repair packet. The implementer writes only the requested
change. A verifier runs deterministic checks and compares the result with the
phase contract.

For a modest workflow, the parent agent can be the orchestrator and verifier;
adding a separate orchestrator subagent otherwise creates another reasoning hop
and another chance for context drift. That hop is not only a drift risk. When a
parent must relay an instruction it did not author, it tends to paraphrase: in
one recorded run the parent turned a delegated `Run Phase 1` into `read the
specs and provide a summary`, so no implementer ever launched. The durable
principle is that a handoff packet is trustworthy when the agent that authored
it is the same agent that sends it; the lossy step is a model relaying another
party's instruction verbatim. OpenCode also caps subagent nesting at depth 1 by
default, so a `main -> orchestrator -> implementer` shape fails mechanically
unless you raise `subagent_depth` — a further reason to let one parent own
orchestration and delegate a single level to the implementer. In a repeatable
production system, a dedicated orchestrator and mechanical verifier are still
worthwhile because they move loop control outside the SLM.

A 12B or 27B orchestrator should still be procedural rather than deliberative.
It has enough headroom to read named files, construct a packet, run a fixed test
command, compare the changed-file set, and check literal requirements. Do not
ask it to invent architecture, perform an open-ended semantic review, or repair
application code itself. Start a fresh orchestrator chat for each phase when
phase-to-phase context isolation matters; a persistent orchestrator isolates
its children but continues accumulating its own history.

Independent verification is foundational. A live Gemma run wrote an edit with
an unresolvable name and still shipped it. Even direct diagnostic feedback does
not guarantee repair: observed self-correction engaged with only half of the
flagged files on the following turn. Let the model author; let a type checker,
test suite, LSP, Pyrefly overlay, or other verifier establish whether it worked.

## 5. Orient the model with structure, not repository-wide exploration

Small models do not have structural awareness of this codebase or its local
house style. Without external orientation, they grep, guess, and use trial and
error for import paths, naming, registration wiring, and ownership boundaries.
That wastes context and does not reliably converge.

The orchestrator should provide the relevant symbols, module paths, conventions,
and complete change surface in the handoff packet. A structural index such as an
LSP, CST/AST transform, or a "model starts, deterministic tooling finishes"
write path can enforce relationships that a prompt merely describes.

## 6. Keep the SLM out of responsibilities owned by better tools

SLMs are not replacements for developers or an IDE. Keep Git operations,
refactors, diagnostics, test execution, code navigation, and deterministic
transformations in the tools that already do them well. Ask the model to make a
specified code change, not to own every decision around it.

This also means stopping after the acceptance command answers the question.
Do not let a small model chase framework warnings, invent adjacent features, or
keep editing after success. Warning cleanup is a separate task unless it is an
explicit acceptance criterion.

## 7. Build a codebase that is easy to constrain and verify

Modular code, useful type hints, mature frameworks, and focused tests reduce
the amount of reasoning delegated to the model. Resist the "god-box" seduction
of asking an agent to invent dependencies or architecture when a mature
framework already supplies known behavior.

Tests and reviews must check the actual phase contract. Several runs passed a
smoke test while silently changing branding, the favicon, navigation, imports,
or required strings. Assert exact user-visible behavior and preservation of
earlier phases; do not accept a vague "no critical issues" review.

## 8. Enforce tool-output limits; do not rely on a prompt reminder

A single `ls -R` traversed `.venv`, produced tens of thousands of characters,
and inflated every following request. The model's initial choice was stochastic;
the context explosion after that choice was deterministic.

Reject recursive listings and protected-directory traversal at the Bash-tool
layer. Allow narrow discovery such as `rg --files`, named-file reads, and the
project's validation command. Prompt guidance is useful, but an enforced tool
policy is what removes this failure mode.

An allowlist is only as tight as the tools it can see. A denied Bash command
does not stop a model that reaches for a different tool: in one run a child hit
its denied `ls` calls, then routed the same intent through an editor-injected
shell tool it had never been told to avoid, and burned its whole step budget
without delegating. Prefer a default-deny permission ruleset (`"*": deny` with
explicit allows) to naming individual denied commands, because default-deny also
hides tools an editor or client injects at runtime that no allowlist
anticipated. Path patterns compose with this: because `read` and `edit`
permissions match worktree-relative paths, denying `specs/*` on both makes an
implementer structurally unable to consult the roadmap or rewrite the contract,
so its entire knowledge of a phase is the packet it was handed.

## 9. Keep context deliberately small and clean

A new parent chat is not magic: when every phase already has a fresh child, the
packet shape matters more than the parent's conversation history. Keep routine
SLM work near a 32K input budget and work hard to ensure the phase, tool output,
and validation evidence fit within it.

The coding profile used `context: 40960`, `input: 32768`, and `output: 2048` to
avoid compaction pressure while bounding oversized completions and repair tails.
The output cap was later raised to 4096: in the medium workflow the delegation
packet and coverage matrix are themselves model output, and 2048 risked
truncating a `task` call mid-argument. The correction is paired, not just
larger: raise the cap for safety margin, and design packets that never inline
file contents so they stay far below it. The goal is not maximum context. It is
enough room for a small, clean task plus validation, with a budget that makes a
bad tool choice visible and bounded.

## 10. Choose the exact model and tune it for the role

Model identity and tool training matter. Similar Gemma names, fine-tunes, and
backends can behave very differently: one coder-oriented Gemma variant emitted
a `task` call as prose or stopped after its first tool result, while another
handled multi-step tool trajectories more reliably. Verify the resolved model
through configuration, session telemetry, and backend logs; a configured name
is not proof that it received the request.

For Gemma 4 routine implementation, low sampling entropy reduced chattiness,
speculative plans, and unnecessary tool use: `temperature: 0.2`, `top_p: 0.9`,
and `top_k: 64`. Reserve broader sampling for work that genuinely needs
divergent ideas.

## 11. Give the implementer one job and put validation at one layer

In the minimum workflow, a fresh `implementer1` receives one phase as a
self-contained packet, not a pointer to the specifications. It makes the
edits, runs the project's explicit validation command once, and stops whether
it passes or fails. It does not diagnose or repair after validation, so a
failed minimum run remains a failed run. The Bash permission must allow the
same command named in the packet—for this project,
`.venv/bin/python -m pytest tests/`—and deny every other command. This prevents
a failed run from becoming a `PYTHONPATH` workaround and second test run. This
exposes a result without opening a child repair loop, but it is not independent
verification.

For a phase that changes shared files, the parent packet must mark each target
as new or shared and state the routes, tests, strings, and behavior that must
survive. The implementer reads every existing target completely before editing;
otherwise a phase can pass its new smoke test while erasing earlier behavior.

In the medium workflow, the implementer is write-only. The parent controller
runs the project's declared validation command, compares the changed files with
the packet, and checks exact contract strings after the child returns. Do not
make both roles own repair. Disable planning/design skills for routine
implementation and avoid opportunistic linters, type checkers, or shell
activation.

If the child needs more information, the controller should provide a narrower
packet rather than asking the child to explore the entire repository. Use a hard
step cap as a circuit breaker, not as a solution: it bounds a runaway run but
does not fix a bad packet, stale edit anchor, or semantic trap.

The recorded doom loops were not hypothetical. One child exhausted all 20
steps in edit retries, another was cancelled after 100 messages, and another
ran pytest ten times after it had already passed. In the last case the model's
reasoning repeatedly decided to stop but emitted another tool call. OpenCode's
built-in doom-loop guard did not catch repetition spread across separate
assistant messages. A platform-enforced step cap bounded the cost but sometimes
forced an empty final response, so the orchestrator must judge the files and
validation evidence rather than depend on a perfect child summary.

Time budgets are a second circuit breaker. Live runs showed that many prompts
past the first could not converge within 120 seconds. Treat a timeout as
workflow evidence, not an invitation to keep extending the same unbounded
conversation: narrow the packet, use a fresh repair turn, or change the tool
protocol.

## 12. Make edits deterministic and preserve file ownership

For a small file the child has completely read and whose final state belongs to
the current phase, a whole-file write is more reliable than repeated
anchor-based edits. Gemma repeatedly used stale or empty `oldString` values,
producing edit retries that consumed turns without making the intended change.

This was a broad failure mode, not one malformed `__main__` literal: the session
record contained 27 `oldString` mismatches across blind edits, stale content,
whitespace and escaping differences, empty anchors, and late-session collapse.
A repair packet should name the implicated files and state the exact failure
and required final state — not inline the current file contents, which pays for
the content twice in a small context and risks truncating the delegation under
the output cap. The fresh repair child reads the named files itself, then
writes. When the packet grants complete ownership of a small file, ask a fresh
child for a full-file write; do not ask it to apply an `oldString` patch. The
read-then-rewrite repair flow never touches an edit anchor, so this failure
mode cannot recur there.

Whole-file writes are unsafe when another phase owns part of the file: they can
erase routes, imports, or behavior that must survive. Use one only when the
packet supplies the complete desired content or the phase owns the complete
file state. Otherwise use a constrained structural or deterministic transform;
if an anchor fails, re-read before retrying.

## 13. Put framework semantics in the packet and the tests

Some failures were semantic, not implementation failures. `TestClient` follows
redirects by default, so a test for a 303 response must use
`follow_redirects=False`. Likewise, a test that only makes a request will not
exercise a script entrypoint or prove that a deprecation warning was removed.

Put known semantic traps in the phase packet, and add focused behavior tests for
paths that ordinary request tests do not cover.

For medium, encode the few known, phase-relevant facts directly in the packet.
Do not attach general framework documentation to every run. Context7 or another
documentation retriever is out of scope for this course's tiers: a controller
should consult one only for a real API uncertainty, then compress the answer
into one concrete rule for the implementer. This preserves the benefit without
paying the full context cost in both agent roles.

Do not silently repair a minimum run. In one recorded run, the child received
the instruction to repair until tests passed even though its agent contract said
to stop after one validation. It then spent seven turns repeating no-op edits;
the parent later edited the code and claimed success. The fix is a terminal
validation instruction in the implementer prompt, not more persuasive wording
or a repair loop after the failure.

## 14. Interpret context and cache metrics correctly

LM Studio and oMLX do not report prompt reuse the same way. oMLX exposes
`cache_read` tokens, so compare effective per-request context as
`fresh input + cache read`, while reporting the two values separately. Do not
compare fresh-input totals, cache totals, or token ratios across providers as if
they were one accounting system.

Nonzero cache reads prove prefix reuse, not a wall-clock speedup. Parent
lifetime can include idle time and nested child time, so report parent and
implementer time separately instead of adding nested durations together. The
collector's activity span is useful but is based on message creation times and
can omit final-response generation. For a precise end-to-end comparison, use
the first user message's `time.created` and the final assistant message's
`time.completed`; for parent inference, sum each assistant request from its
start to its first tool start, or to completion when it has no tool.

## 15. Compact packets must preserve the contract, not merely omit code

"Do not write the code for the child" fixed one failure mode: parents had been
copying complete files into delegation packets, leaving the implementer only
to transcribe. The replacement is not a vague packet. A good packet names each
repo-relative writable file, marks it as new or shared, states the exact
required behavior and literals, and lists every route, import, test, string,
and user-visible behavior that must survive.

The parent must read every existing target before delegation. A glob that finds
`app.py` and `tests/test_app.py` is not a read. In a later Phase 2 run, the
parent skipped those reads and the child happened to rescue the workflow by
reading them itself. That is not a valid self-contained handoff and can erase
earlier behavior when the child is weaker or more literal.

The Phase 1 comparison showed the opposite failure: an overly short packet
produced code that passed its smoke test while omitting the Jinja title block,
italic tagline, and required `starlette.testclient` import. Exact acceptance
criteria are not implementation code; they belong in the packet and in tests.
Do not include complete files, code blocks, pseudocode, or line-by-line
solutions, but do include exact strings, APIs, preserved behavior, and
phase-specific semantic constraints.

## 16. Make validation terminal in the tool policy, then report raw evidence

Terminal-validation wording alone is insufficient. Two Phase 3 children ran
pytest, repaired a failure, and ran pytest again despite being told to stop
after the first result. A final green test does not make that a compliant
minimum run: it hides the original failure and turns validation into an
unauthorized repair loop.

Align the prompt, agent frontmatter, and validation command exactly. A Phase 1
child initially could not run `.venv/bin/python -m pytest tests/` because its
allowlist still admitted only the old `uv` command; it retried the denied call
and the parent improperly ran pytest afterward. Once the allowlist matched the
packet, later Phase 2 runs performed one permitted direct-venv test call.

The parent must report the literal command result, including warnings and the
first failure when one occurred. "Validation successful" or "no critical
violations" is not evidence. Read the child tool output, the changed files,
and the changed-file set; never infer a clean run from the child summary.

The medium workflow removes this failure mode at the source rather than patching
it with wording: the implementer is given no Bash at all, so it cannot run or
re-run validation, and the parent owns the single test call. Terminal-validation
wording is a minimum-only patch for a writer that can also validate; where the
writer cannot validate, there is nothing to make terminal.

## 17. Compare parent models with raw timing, not session lifetime

In controlled Phase 1 comparisons, an oMLX Gemma parent used fewer turns and
tools than a DeepSeek parent, and its child finished faster. The end-to-end
runs were nevertheless nearly equal because the oMLX parent's own observed
generation time was about eleven seconds longer. In a Phase 2 comparison, that
same parent was slower both before delegation and in total despite a smaller
reported effective context.

These are measurements, not general model rankings. Backends tokenize and
account for cache differently, and a parent session's lifetime can include
idle time. The durable lesson is to report the resolved model, exact nested
timeline, raw request timing, turns, tools, fresh input, and cache reads; then
state only what that run supports. Fewer turns, a cache hit, or a smaller
context number does not by itself prove lower latency or better orchestration.

The latest Phase 3 comparison demonstrates the distinction. The constrained
write-only implementer finished its active work in 44.5 seconds versus 60.7
seconds in the earlier successful run, with 8 rather than 10 turns and about
half the fresh input. Yet end-to-end lifetime was effectively unchanged (113.0
seconds versus 113.5), because the controller now performs the baseline,
independent pytest run, changed-file diff, and post-change reads. Report that
as a reliability improvement, not a throughput claim.

## Workflow levels

### Minimum

Minimum uses one fresh main chat per phase with a hand-typed prompt. The parent
reads the specifications and the phase's target files, then delegates once to a
fresh `@implementer1` with a self-contained packet. The implementer makes the
requested edits, runs the validation command exactly once as its final tool
call, and reports the exact command and result; it does not repair afterward.
The parent then reads the changed files and reports critical contract
violations. `implementer1` denies writes under `specs/*`, so it cannot rewrite
the contract while implementing. The deliberate limitation is that validation is
self-reported by the writer rather than run independently.

### Medium

Medium replaces the hand-typed prompt with a `/phase N` command, so the learner
kickoff is a single line. The command template is delivered to the main chat
verbatim — OpenCode substitutes `$ARGUMENTS` and does not let a model paraphrase
it — which removes the kickoff-rewrite failure that broke earlier nested
designs. The specifications are attached to the command with `@`-references, so
their content arrives with the message instead of costing separate tool calls.
An earlier attempt moved the protocol into a phase-local `orchestrator2` primary
agent; that added a reasoning hop and depended on a client exposing custom
primary-agent selection, and it was dropped in favor of the command.

The main chat is the controller and verifier; there is no orchestrator subagent.
It:

1. Refuses to run if the chat already contains prior phase work. This is
   model-enforced, but it fails visibly to the learner instead of silently
   degrading isolation.
2. Reads the phase's target files and records the `git status --short` baseline.
3. Builds a compact packet and delegates once to a fresh, write-only
   `@implementer1a` without a task ID.
4. Runs `.venv/bin/python -m pytest tests/` itself, diffs `git status --short`
   against the baseline, reads each changed file, and completes a readable
   atomic coverage ledger.
5. On failure, sends exactly one repair packet to one new `@implementer1a`,
   validates once more, and stops.

Validation moved from the implementer to the controller: `implementer1a` has no
Bash at all, so scope checking no longer trusts the writer's self-report, and
the minimum-only terminal-validation rule is retired. The repair packet names
the implicated files, the exact failing output, and the required fix; it never
inlines file contents, which would pay for them twice in a small context and
risk truncating the delegation under the output cap. The fresh repair child
reads the named files and writes complete files, so the `oldString` failure mode
cannot recur.

`implementer1a` uses a default-deny permission ruleset: every tool is denied
except `read` and `write`, and both deny `specs/*`. The implementer therefore
cannot consult the roadmap and improvise scope — its entire knowledge of the
phase is the packet — and cannot reach an editor-injected shell tool to escape
its constraints. Because current OpenCode maps `edit` and `write` to the same
`edit` permission, medium still cannot expose `write` while mechanically denying
exact-match edits within the allowed paths; the whole-file-write instruction
remains prompt-enforced and should be measured in telemetry.

OpenCode provides no per-agent "one repair" counter, so the single-repair rule
remains model-enforced. Medium restores a 25-step controller cap as a circuit
breaker after telemetry exposed a Phase 2 run that reached 32 turns while
repeating a misspelled-path read. The cap bounds the cost; it does not repair the
path or replace the command's fail-fast read rule.

Medium also denies `external_directory`. The same Phase 2 typo would otherwise
have triggered a learner approval prompt for a path outside the project. The
denial makes the scope violation visible and keeps the controller in the
project, while the terminal read-error rule prevents retries.

A `task: {implementer1a: ask}` permission would make each delegation a learner
click that also serves as a manual repair counter, but telemetry has not yet
shown a controller delegating in an unbounded way — the recorded doom-loops were
all implementer-internal (edit retries, repeated pytest), not repeated
re-delegation. Do not impose that click on the learner until a run demonstrates
the need; watch the traces and add the gate only if delegation actually runs
away.

Do not force a scout agent to read one or two known files. Prior experiments
ignored that rule across eight phases because direct reads were cheaper. A
read-only scout is useful only for genuine cross-file searches or convention
discovery.

### Out of scope

This course stops at minimum and medium. Some controls raise reliability further
but cost more setup or context than a teaching baseline should: mechanically
enforced tool-output limits, structural navigation or LSP checks, deterministic
`write`-path transforms, on-demand Context7 research, richer contract tests,
telemetry-driven model verification, and externally enforced repair budgets.
They record the direction a production system would take, not a tier this
repository implements.

## Evidence sources

- [Lesson 11 OpenCode debug notes](docs/lesson-11-opencode-debug.md) preserve
  the original session evidence and the first set of workflow changes.
- [Model configuration](README.md#model-config) records the native LM Studio
  baseline and the selected coding profile.
- [Telemetry workflow](README.md#telemetry-workflow) explains how to collect,
  inspect, and report each OpenCode run.

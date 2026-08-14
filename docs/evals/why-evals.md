# Why evals?

If you are looking at this repository and thinking "this is a lot of
machinery, and there are plenty of benchmarks already" — this page is the
answer. It is the project's own argument for why an eval harness exists
at all, what it measures that nothing else does, and why the machinery is
the size it is.

## The question benchmarks answer, and the one this answers

A benchmark answers: *how capable is this model at a canonical task?*
MMLU, HumanEval, SWE-bench, the leaderboards — one number, comparable
across models, fixed prompts, graded once, published. That is a
capability question, and it is a good one.

This harness answers a different question: ***did the technique help?***
Same suite. Same machine. Same pinned Pi version. One variable changed —
a system prompt, a guard, an improvement — and everything else recorded
as conditions so the comparison is airtight. The unit of measurement is
not the model's rank; it is the *controlled difference between two arms*
of one experiment.

Those are not the same kind of question, and the difference is the whole
reason the project exists. A leaderboard cannot tell you whether adding a
"Technology" section to a prompt moved a 12B model from 0/16 to 13/16 —
that is not a benchmark question. It is a *steering* question, and it is
the only question this project is interested in, because small local
models fail on routine, small, engineering-like work in ways that
steering changes — not on the capability ceilings a leaderboard ranks.

## Where this harness collected signals no benchmark could

The proof is concrete: every major engine improvement shipped because the
harness recorded something a benchmark would have thrown away.

**The loop, and guard #1.** One recorded run: 261 turns, 245 of them the
identical `ls -R` against an empty directory. A benchmark would report
that run as one data point — a failure, or a completion. The harness kept
the transcript, and the transcript showed the model was not failing at
the task; it was *repeating one tool call 245 times*. That signal became
the loop breaker, guard #1 of the engine. No benchmark would have shown
you the loop; the harness's evidence did.

**The contract mismatch.** Models kept choosing WSGI frameworks against a
suite that drives ASGI — `TypeError: Flask.__call__() missing
start_response` — and solutions under `app/main.py` never reached the
grader at all. The harness's hermetically-graded acceptance surfaced the
pattern, and the improvement loop answered it with a prompt that names
the framework explicitly: the recorded 0/16 → 13/16 turn. A benchmark
cannot tell you *why* a model failed; the harness's grading can.

**The agency floor.** The user-story suite ran both arms to 0/16 — bare
Pi read the spec, restated it accurately, and stopped to ask what to do,
writing nothing. A capability benchmark would call that "failed." The
harness's run corpus showed it was not capability but *agency*: the model
was able and unwilling. That distinction shaped the orchestrator
improvement.

**The silent server.** When the model server is down, Pi exits 0 with
empty output, and the harness was recording results that *looked like
data*. The harness caught its own silent corruption and every run path
now checks liveness first. No benchmark runs your server; the harness
does, hands-free, sixteen runs at a time.

**The deleted route.** Three of four runs failed the same way: the model
replaced an existing `/about` route instead of adding the requested
`/contact` one. That pattern became preserve-symbols, guard #2. The
harness's grade said "failed"; the harness's record said *how* — and the
record was actionable.

**Honest numbers, including its own.** The harness retracted two of its
own published wall-clock figures when the conditions showed they were
untrustworthy, and recorded the retractions with banners rather than
editing them away. It applies to itself the standard it applies to
models: a number without recorded conditions is not evidence.

## What the machinery buys you

The size is the price of the two properties that make any of the above
trustworthy — and of the workflow that makes them cheap to collect.

**Hermetic grading.** Each run's verdict means something because the
model cannot touch its own grader: only allowlisted files reach the
grading directory, model-written config is refused, and the verdict comes
from a hook-written results file, never from pytest's exit code. That
is not decoration; earlier versions were defeated by `addopts =
--collect-only` and an import-time `os._exit(0)`.

**Recorded conditions.** Every run carries the digests that make it
reproducible — task spec, acceptance file, extensions, agent dir, the
harness revision itself. When conditions cannot be guaranteed (a
different Pi version, a checkpoint whose conditions moved), the harness
refuses to resume rather than silently producing a number. A batch is
locked to its checkpoint: commit mid-batch and it stops, loudly.

**Hands-free n=16.** A batch is sixteen sequential, unattended runs
against one shared local server — walk away, come back, and the
checkpoint holds a corpus: raw stdout, the diff, the grade, and the
conditions, one run per line. A benchmark hands you a number. The
harness hands you the evidence *behind* the number, and the evidence is
the deliverable.

**Rolling up the evidence.** Claims are classified — confirmatory versus
pilot — and indexed in `docs/evidence-index.md`; pre-registered
comparisons are recorded before they run; pilot results say they are
pilot. The project's published numbers carry their own evidentiary
grade.

## And the cathedral worry

The size is deliberate and the project says so in writing: its own
roadmap opens with the trap it is avoiding — three prior attempts that
"turned into engineering efforts *about orchestration*" until the
machinery outgrew anyone's ability to hold it in their head. Every phase
runs under a standing rule: *no machinery ahead of the contract it
serves*. Phase 8's brief was literally "the harness already refuses; the
CLI translates" — the engine was untouched. The machinery that exists is
the minimum that hermetic, recorded, reproducible measurement requires,
and the project has a published budget on its own jargon.

So: it is not a benchmark and not a competitor to one. It is a measuring
instrument for a question no benchmark can answer — *did the technique
help, on my machine, reproducibly?* — and the evidence it has already
produced is the engine itself.

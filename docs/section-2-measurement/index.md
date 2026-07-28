# Section II — Measurement

The evaluation harness: it drives Pi headless via `subprocess`, provisions
disposable git-tracked workspaces, captures diffs, and runs pytest as the
acceptance oracle.

**Status:** evidence finalized 2026-07-27, chapter prose below is written
against it (Task 9). Every earlier number below (the n=4 0/8 baseline, the
pre-repair post-repair reports) was measured under an invalid or self-graded
oracle and is superseded — kept as historical record, bannered where
applicable. The grading path was rebuilt under the grading-path reboot (see
[`docs/superpowers/plans/2026-07-24-grading-path-reboot.md`](../superpowers/plans/2026-07-24-grading-path-reboot.md)),
and the 2026-07-27 unsteered n=16 reports below are the first trustworthy
numbers this project has produced.

**Evidence:** unsteered n=16 per phase, no ditch —
[Phase 1](research/2026-07-27-post-repair-sp1-phase1.md) 15/16 (Wilson 95%: 72–99%),
[Phase 2](research/2026-07-27-post-repair-sp1-phase2.md) 15/16 (Wilson 95%: 72–99%),
[Phase 3](research/2026-07-27-post-repair-sp1-phase3.md) 16/16 (Wilson 95%: 81–100%),
[Phase 3, less-prescriptive spec](research/2026-07-28-post-repair-sp1-phase3-less-prescriptive-spec.md) 16/16 (Wilson 95%: 81–100%).

## What the workload actually is

Before you can write a suite that grades a phase, you have to be able to say
what "a phase" is. That sounds like bookkeeping. It is the first thing this
project got wrong, and getting it wrong invalidated a whole batch.

### A phase-N run starts seeded, not empty

The rule, stated as **D1** in
[the evidence policy](../superpowers/policies/evidence.md): *a phase-N run
starts from the committed reference solution of phases 1..N−1, overlaid before
the pristine commit.* A run from an empty workspace measures phases 1..N
combined and must not be labelled phase N.

That rule exists because of a specific incident. An early batch was recorded as
**"Phase 2: 0/8"**. The workspace it ran in — `examples/agentclinic` — contains
no app code, so every one of those eight runs started from nothing. What was
actually measured was "build Phases 1+2 combined, from an empty directory," and
it was labelled as if it measured Phase 2 alone. The
[oracle-repair plan's Amendment 1](../superpowers/plans/2026-07-24-oracle-repair.md)
records the finding and the decisions that followed it.

The damage is not just a mislabelled row. Two things broke:

- **The escalation inference collapsed.** The reasoning the batch was run to
  support — Phase 1 passed, Phase 2 scored zero, therefore Phase 2 is the
  ditch — does not hold from an empty start. A run that fails may have failed
  on Phase 1 work. You cannot attribute the failure to the phase you named.
- **Preservation breakage became unmeasurable.** The failure this workload was
  built to expose is a model completing Phase 2 while erasing Phase 1 behavior.
  If Phase 1 behavior was never in the workspace to begin with, there is
  nothing to erase, and the failure mode simply cannot occur.

Amendment 1's fix has three mechanical parts worth copying:

1. **Seed from a fixed reference fixture** (`examples/reference/phase-<k>/`),
   identical across every run and every arm — never from a model's own prior
   output, which would make each run's starting point depend on how well the
   previous one did.
2. **Commit the seed into the workspace's pristine git baseline**, so the
   captured `changed_files` set reflects only the model's phase-N work.
3. **Every report header states its starting state** — `seeded: reference
   phase-1 @ <path or hash>`, or `empty`. Amendment 1 puts this bluntly: a
   report without it is not citable.

The superseded reports were not deleted. They carry a banner saying what start
state they actually used and are kept as the historical record — you can read
[the phase-2 pooled report](research/2026-07-24-post-repair-sp1-phase2-pooled.md)
and see the relabelling for yourself.

### One sub-batch never decides anything

The second half of defining the workload is defining when a result is allowed
to make a decision. **D2** in the evidence policy: failure-mode incidence is the
primary metric, batches are n=16 unsteered and n=8 steered, and *every
escalation decision operates on pooled results only*.

The number that forced this is small and unpleasant. Two independent n=4
samples of the *identical* seeded-Phase-2 unsteered configuration returned
**4/4 and 2/4** — pooled, 6/8. Same workload, same model, same prompt, same
start state — this is the D1-seeded measurement, a different quantity from
the empty-start "Phase 2: 0/8" incident above, and the two numbers are not
directly comparable. Under the decision rule in force at the time ("4/4 → escalate"),
the first sample would have declared the phase solved and the second would have
declared it a candidate ditch. The Wilson 95% interval on 6/8 is roughly
**41–93%**, which is another way of saying eight runs cannot tell you much of
anything.

So the thresholds moved to the pooled batch:

| Pooled unsteered result | Decision |
|---|---|
| ≥ 15/16 | phase solved — escalate to the next phase |
| 13–14/16 | ambiguous — report honestly, decide with the human |
| ≤ 12/16 | candidate ditch — stop escalating |

Sub-batches of an identical configuration may be pooled legitimately; the
report has to state that it pooled them. What a sub-batch may never do is
decide on its own.

Two practical notes from running these. Unsteered runs take about 60 seconds
each, so n=16 is roughly fifteen minutes; steered runs take 130–380 seconds,
which is what makes large arms unaffordable. And batches must be *durable*:
three separate batches were lost mid-run on a single day to session teardown
reaping child processes, because the runner wrote its report only after all n
runs completed. Per-run checkpointing landed before the real batches, and it
earned its keep — two live interruptions during the Phase 1 run were recovered
from checkpoint without losing completed runs
([grading-path reboot](../superpowers/plans/2026-07-24-grading-path-reboot.md),
Task 8 addendum).

Applied to the finished evidence chain: under the rebuilt grading path, the
pooled unsteered results were 15/16, 15/16, and 16/16 for Phases 1, 2 and 3
(linked at the top of this page). All three clear the ≥15/16 line, so by D2
the decision is "solved, escalate" — and, there being no fourth phase, "no
ditch on this workload for this model." That is a decision made by a
pre-registered rule, not a success-rate claim: the 15/16, 15/16, and 16/16
counts above feed Amendment 2's pooled escalation rule as decision-rule
inputs, not as reported effects. Per
[Rule 7](../superpowers/policies/evidence.md), no chapter in this course claims
a success-rate delta at all.

## How to write an eval suite

**A passing smoke test is not a passing phase.** That is Rule 3 of the evidence
policy, and it is the whole reason this chapter exists. Acceptance means the
phase contract's literal requirements are met, checked explicitly — not that
*some* test the model could run came back green.

### The suite is harness-owned, human-authored, and overlaid last

**D3**: the acceptance suite lives in `examples/acceptance/phase-<N>/`, is
overlaid into the workspace *after the model finishes and immediately before
the oracle runs*, is cumulative across phases 1..N, and is the sole grade.

Each clause is load-bearing:

- **Harness-owned**, because the alternative was a self-graded exam. The
  original oracle ran `uv run pytest -q` inside the workspace, which executed
  `tests/test_app.py` — *a file the model writes*. Every phase-2 row lists
  `tests/test_app.py` in its changed files: the model inherits the seeded
  prior-phase test file and modifies it. A model that rewrites the suite with
  only the current phase's assertions passes green while prior-phase behavior
  goes unverified. That is exactly the `lessons.md` #7 failure — passing a
  smoke test while silently changing branding, the favicon, navigation,
  imports, or required strings.
- **Overlaid after the model finishes**, so the model never sees, edits, or
  reasons against the thing that grades it.
- **Cumulative**, so preservation breakage is *mechanically detectable* rather
  than inferred from reading a diff.

The model still writes its own tests — the roadmap asks it to — but those tests
do not grade it. They are run separately as a signal: model-tests-pass plus
acceptance-fails is the **false self-report** failure mode, now countable per
run instead of read out of prose.

#### The incident: authoring delegated to a model, and discarded

D3 ends with a clause that reads like an aesthetic preference and is not one:
*authoring it is human work by design — it is the one artifact that must not be
written by a model, because it is what grades models.*

It was violated anyway, in this project, deliberately, with the rule cited in
the briefing. A task brief handed the phase-2 and phase-3 suite authoring to a
model. The model authored both suites. The work was discarded unmerged and the
`test_suite_is_authored` guards restored
([grading-path reboot](../superpowers/plans/2026-07-24-grading-path-reboot.md),
Task 1).

The instructive part is the justification the brief used, because it is the
justification anyone reaches for: *a human reviews the model's suite
afterwards.* That does not preserve D3. It converts the judgment that **is**
the deliverable into a rubber stamp on plausible code. Reviewing an acceptance
suite means re-deriving, assertion by assertion, what the contract requires and
whether this assertion catches its violation — which is the entire authoring
task, done in a mode where a plausible answer is already sitting on the page
anchoring you.

What was salvaged from that run says the same thing from the other side. The
*mechanical facts* the model had gathered — escaping rules, import paths,
mutable seed state — were harvested into `examples/acceptance/WORKLOAD-FACTS.md`
and kept. The judgment calls were deliberately not.

### Non-vacuity, gated in both directions

A suite that passes everything grades nothing. So does a suite that collects
nothing. The precedent here comes from outside this project: the Tainie
project's generalization campaign found its repo-pytest oracle collected zero
tests on all **34** targets and was silently vacuous the entire time — every
verdict it issued was green, and none of them meant anything.

This project has its own worked example of direction 1, and it is worse than a
seed-count trap because the oracle did not just under-grade — it rejected a
textbook-correct solution outright. A Phase 1 reference solution, placed in a
freshly stamped workspace, failed pytest *collection* with
`ModuleNotFoundError: No module named 'app'`, because the stamped
`pyproject.toml` carried no pythonpath configuration and `uv run pytest`,
unlike the prior course's `python -m pytest`, does not put the workspace root
on `sys.path`. The identical solution passed once a single empty
`tests/__init__.py` was added — a file the spec never mentions. Every
pre-repair batch had been measuring whether a model stumbled onto that
unstated workaround, not whether it delivered a correct solution. See
[the oracle-invalid incident report](research/2026-07-24-oracle-invalid-incident.md)
for the full reproduction and the six reports it invalidated.

The gate (`tests/test_oracle.py`) therefore asserts **both** directions:

1. the acceptance suite **passes** the reference solution, and
2. the acceptance suite **fails** a deliberately broken one.

Direction 2 is where naive gates go wrong, and this project's first version
went wrong in exactly the interesting way. The break fixture blanked `app.py`
for every phase, removing all routes. For a phase-2 suite that trips the
*phase-1* preservation checks — so the gate passed whether or not the phase-2
assertions had any teeth. A phase-2 suite whose contract assertions were all
`assert True` would have cleared it.

The property you actually need, for suite N: **for each k ≤ N, the suite fails
a solution that violates only phase k.** That means a *matrix* — parametrize
`(suite_phase, broken_phase)` over every `broken_phase <= suite_phase` — and
each break must be genuinely isolated:

- **phase 1** — the tagline removed from `home.html`, routes left intact.
- **phase 2** — the `Scope creep never ends.` seed removed from `models.py`, or
  the `/complaints` route dropped. Either leaves phase-1 preservation green,
  because `href="/complaints"` lives in `base.html` markup.
- **phase 3** — the POST returns 200 instead of 303, *while still appending the
  complaint and still rendering the form*. The append clause is load-bearing:
  without it, a suite that omitted the 303 assertion would still fail on the
  append check, and the gate could not see the missing tooth.

That phase-3 break doubles as a `follow_redirects` trap detector (`lessons.md`
#13). Starlette's `TestClient` follows redirects by default, so a test for the
303 must pass `follow_redirects=False` or it silently asserts against the
followed page and passes for the wrong reason. The suite that grades everyone
else is the one place that trap must not be fallen into — and a suite that
asserts a final 200 passes the broken fixture and gets caught by the matrix.

The break matrix is not a one-time gate, either. `examples/acceptance/phase-3/`
carries its carried-forward obligations as a checklist in the file itself,
naming each break by id — `p1-tagline`, `p2-seed-count`, `p3-303`,
`p3-wrong-location`, `p3-no-append` — so that as new breaks are identified
they have a place to be tracked until the suite is shown to catch them; every
entry currently on the list is already checked off as caught. One entry
records a trap the suite set for itself: this suite's own
POST tests append to `models.complaints`, so a "3 to 5 seed complaints" length
check placed *after* them would false-fail the reference solution. Direction 1
of the gate catches that, so it cannot ship silently — but it costs a cycle.

Before the matrix landed, the gate reported 6 passed and 4 skipped: it *skipped*
whenever an acceptance suite was still a skeleton, which meant phases 2 and 3 —
the entire measurement site — were gated by nothing at all. A skip is not a
pass, and a gate that skips is a gate that is off.

### The grader accepts no model-controlled input

**D4**: grading happens *outside* the workspace, in a fresh directory holding an
explicit allowlist of the model's source artifacts and **no configuration files
of any kind**. A positive count of *executed* tests is required;
`returncode == 0` alone is not evidence.

D4 replaced a blacklist, and the story of why is the most useful thing in this
chapter. Successive hardening passes removed `conftest.py` and re-stamped
`pyproject.toml`. Two vectors closed. Then a review on a different model found
two live defeats of the *hardened* oracle:

- **F1** — `pytest.ini` outranks `[tool.pytest.ini_options]`. A model-written
  `pytest.ini` containing `addopts = --collect-only` yields exit 0 on a
  deliberately broken app: `tests_pass=True`, and the tampering list empty.
  `tox.ini` and `setup.cfg` are the same vector.
- **F2** — import-time process exit forges green. An `app.py` containing
  `os._exit(0)` produces empty pytest output and exit 0, again `tests_pass=True`.
  A stray top-level `sys.exit()` hits this one *by accident*, with no
  adversarial intent required.

Note what both defeats have in common: exit code 0 with **zero tests
executed**. That is why D4's executed-test count is not a nicety. The rebuilt
path copies in only allowlisted source artifacts, writes the harness's own
config and the acceptance suite, runs pytest with `-p no:cacheprovider`, an
explicit `-c`, and an explicit `--rootdir`, then requires the number of tests
that actually ran to equal the number of test functions in the suite. The model
config files refused entry are recorded in the result as evidence, not silently
dropped.

The general lesson, which the project's own backlog had written down before it
committed the blacklist anyway: **blacklisting an open category never closes
it.** Config-file formats are an open category — you can enumerate the four you
know about and pytest will still honor a fifth. `lessons.md` #8 states it as
"an allowlist is only as tight as the tools it can see." Every fix up to that
point had been a blacklist against an open category; the fix was not a longer
list but a different architecture, one where model-controlled input cannot
reach the grader at all.

### Rule 8: a gate is not passed until a different model has tried to break it

Almost everything above was found by someone other than its author — the
empty-start incident is the exception, surfaced by routine execution rather
than a review round. The pattern otherwise is not a coincidence, and the
evidence policy promotes it from habit to **Rule 8**: for
any change to the grading path, the acceptance suites, or the harness's
measurement code, the gate requires review by a model other than the one that
wrote it, with findings recorded alongside the change.

The record behind the rule: every adversarial review round in this project's
history was run by a different model than the one that produced the work, and
every round found a defect the author had missed and self-review had cleared —
a guardrail wired to an event that structurally could not observe its own
target failure; a path-traversal bypass; a guard that blocked the project's own
test command; and the two oracle defeats above, found *hours after* the
hardening commit that was supposed to close them. It cuts both ways, too: a
forensic replay overturned an amendment written the same day by the same
assistant.

The reason it is a rule and not advice: **an author's confidence carries no
information about whether the work is correct.** Every defect listed was
committed by an author who believed the work was done. Self-review cannot be
the last step, because the thing being reviewed is the reviewer.

Chapter prose and reports are exempt from Rule 8. What grades models is not.

### Case study: deriving a suite from a higher-level story

The suite material so far is retrospective — incidents, defeats, rules adopted
after the measurement they invalidated. This last part is an exercise you can
work yourself.

`examples/agentclinic/specs/roadmap.md` is the workload every report in this
section cites. It is written as implementation instructions. Alongside it sits
`examples/agentclinic/specs/roadmap-user-story.md`: the *same three phases*,
targeting the identical app — same routes, same redirect contract, same seed
content — restated as user-facing outcomes. Its own framing: read it as "what
agents experience," not "what files to create."

The exercise is to derive the acceptance contract from the story version, then
compare against the suite that already exists.

Start with Phase 3's core sentence:

> Submitting a complaint is a one-way action: it registers the complaint —
> under the exact name and exact text the agent provided, neither dropped nor
> altered — and then sends the agent's browser back to the complaints board so
> they can see their own words now sitting alongside everyone else's. Because
> this is a form submission that changes what's on the board, not just a page
> fetch, the response must be a redirect that re-fetches the board with a
> fresh `GET` rather than resubmitting the form if the agent reloads or goes
> back — concretely, an HTTP 303 status pointing back at `/complaints`.

What does that require *observably*? Work it clause by clause:

- "registers the complaint" — after the POST, a subsequent `GET /complaints`
  must contain both the submitted name and the submitted text. Note the trap
  the story spells out for you: "neither dropped nor altered" means a
  round-trip test on *both* fields. A POST that honors `text` while quietly
  discarding `agent_name` is a real failure mode, and only a two-field
  assertion catches it.
- "sends the agent's browser back" — a redirect, and the story is explicit
  about which: an HTTP 303 pointing at `/complaints`. It even gives the reason
  (a fresh `GET` rather than resubmitting the form on reload) rather than only
  the mechanism.
- "offers a way to submit" — a POST form on the board, carrying an input named
  `agent_name`, a textarea named `text`, and a submit control.

Now open `examples/acceptance/phase-3/test_acceptance.py`. Those three
judgment calls are already there, one test each:
`test_post_complaint_redirects_to_complaints_board` (303 plus a `location`
header of exactly `/complaints`, fetched with `follow_redirects=False`),
`test_posted_complaint_appears_on_complaints_board` (both fields, round-tripped
through a real `GET`), and `test_complaints_board_renders_add_complaint_form`
(a POST form whose action is `/complaints` or empty, containing all three
controls).

The same holds for Phase 2. "A handful of complaints (between three and five)"
becomes `assert 3 <= len(SEED_COMPLAINTS) <= 5`. "Its own filing moment,
recorded the instant it's added, in a timezone-aware form" becomes two separate
assertions — that two complaints do not share one timestamp object, and that
the timestamp's `tzinfo` yields a real UTC offset. "Stored under the exact names
`agent_name` and `text`" becomes a field-name check.

**That is the point of the exercise.** The existing suite, authored against the
prescriptive roadmap, grades the user-story roadmap correctly and without
modification. The app is functionally identical, so nothing needed authoring,
re-gating, or re-measuring
([the chapter design](../superpowers/specs/2026-07-28-eval-suite-chapter-design.md)
records that scope decision explicitly). What changed between the two specs is
**how much judgment deriving the grade takes** — not what is graded.

Which is exactly the argument for D3. If deriving the contract from a vague
story were mechanical, delegating it would be safe. It is not mechanical: every
bullet above was a decision about what "observably" means, and each one is a
place where a plausible-looking wrong answer would have produced a suite that
passes broken solutions.

Two closing cautions on the case study.

First, an adjacent lesson from the other side of the D3 boundary. The
model-facing phase-3 spec was itself rewritten to stop pre-defusing its own
known traps — the earlier version named `RedirectResponse` with status 303 and
told the model to test with `follow_redirects=False`, which is to say it stated
the answer to both traps `lessons.md` #13 records. The model-facing spec and
the acceptance suite are different artifacts on opposite sides of D3, but they
fail the same way: **a spec or an oracle that leaks its own answer measures
nothing.** The rewrite had to remove the implementation hint while preserving
the 303 *behavioral* requirement — drop the requirement too, and a
spec-compliant 200 re-render would fail acceptance against a contract its spec
no longer stated, which is the unstated-oracle-versus-workload mismatch this
whole section exists to warn about.

Second, **Rule 6 is deferred here, not skipped.** Introducing
`roadmap-user-story.md` is a change to the workload, and Rule 6 says any such
change re-triggers oracle validation before the next published batch. This pass
publishes no batch, so nothing is due yet — but whoever first runs a measured
batch against this roadmap owns re-running `tests/test_oracle.py` before
trusting a single number that comes out of it.

```{toctree}
:hidden:

spec
plan
research/2026-07-23-baseline-phase-1
research/2026-07-24-oracle-invalid-incident
research/2026-07-24-post-repair-sp1-phase1
research/2026-07-24-post-repair-sp1-phase2
research/2026-07-24-post-repair-sp1-phase2-pooled
research/2026-07-24-selfgrade-forensics
research/2026-07-24-write-vs-edit-experiment
research/2026-07-27-post-repair-sp1-phase1
research/2026-07-27-post-repair-sp1-phase2
research/2026-07-27-post-repair-sp1-phase3
research/2026-07-28-post-repair-sp1-phase3-less-prescriptive-spec
```

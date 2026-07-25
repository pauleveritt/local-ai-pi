# Workload facts for suite authors

Mechanical properties of the AgentClinic workload that an acceptance-suite
author needs to know. These are **facts about how the app and the test client
behave**, not decisions about what to assert. Nothing here tells you what the
contract is — that comes from
[`examples/agentclinic/specs/roadmap.md`](../agentclinic/specs/roadmap.md).

## Provenance, and why this file is short

On 2026-07-24 a model was mistakenly handed the authoring task and wrote full
assertion bodies for the phase-2 and phase-3 suites. That work was **discarded
unmerged** — it violated the human-authored rule (rule 1 in
[`README.md`](README.md), doctrine D3 in the evidence policy). The suite is what
grades models; a model writing it, and a human then reviewing the result,
converts the human's judgment into a rubber stamp on plausible-looking code.

Discarding it wholesale would have thrown away a handful of things that are not
judgment at all — properties you would otherwise rediscover by running into
them. Those are recorded below. **Every judgment call in the discarded work was
deliberately left out**: how strictly to match timestamp format, whether the
heading must match exactly, how much of the form's markup to pin, whether to
assert timestamp ordering as well as distinctness. Those are the author's to
make, and reading someone else's answer first is the anchoring this file exists
to avoid.

## Facts

**Jinja2 auto-escapes rendered text.** A complaint containing an apostrophe
renders as `&#39;` in the response body, so a substring match of the raw model
text against `response.text` fails. `html.unescape(response.text)` before
matching, or compare against escaped text.

**`models` imports cleanly from the workspace root.** `from models import
Complaint, complaints` resolves under the stamped
`[tool.pytest.ini_options] pythonpath = ["."]`. No path manipulation needed in
the suite.

**`Complaint` is a dataclass.** `dataclasses.fields(Complaint)` works for field
introspection, and `Complaint(agent_name=..., text=...)` constructs with the
timestamp defaulted.

**`models.complaints` is module-level and mutable, and POST mutates it.** State
therefore persists across tests within a run: a test that posts a complaint
changes what later tests see on `GET /complaints`. Anything asserting on
list length or on "the complaint I just added" has to account for that — a
value unique per test avoids matching a leftover from an earlier one.

**`TestClient` follows redirects by default.** A 303 assertion without
`follow_redirects=False` silently asserts against the *followed* page and
passes for the wrong reason. Not a new discovery — it is `lessons.md` #13 and
is already called out in the phase-3 skeleton's header — but it is the single
trap most likely to produce a suite that grades everyone as correct.

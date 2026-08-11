# Overnight spike — morning summary

**Read this first.** The full account, with every claim checked against a
real file, is
[`2026-08-10-phase7-cycle3-envelope-screen.md`](2026-08-10-phase7-cycle3-envelope-screen.md).
This is the short version, in the order you'd want to hear it.

## What actually ran, and why the shape changed mid-plan

The planned three stages ran, but stage 4/5's scope narrowed partway
through based on a real finding, not a shortcut — see below. Also: the
"Fable checkpoints the driver applies" idea from last night's design
didn't survive contact with reality. A subprocess script can't dispatch
Fable — that's a capability of my own harness, not something
`tools.replicate`/`tools.reauthor_until_clean` can do on their own. So the
actual architecture was me waking up on a schedule and doing the
review-and-decide step live, the same way I would awake — not a driver
with review logic baked in. Everything below is a decision I made and
checked, not an automated process's output.

## The headline: navigation and contracts, not accept rates

**Stage 2 — the exact envelope, brief-only, all 8 tasks: 0/24 accepted.**
This is the roadmap's literal Cycle 3 spec (16 turns, 30 tools,
`read,write`, no shell), never run before tonight. Every prior gemma number
used a looser config. The 0/24 has two independently verified causes:

1. **No enumeration tool.** `read,write` alone can't list a directory —
   `read` on a directory returns `EISDIR`. Models spent most of their turn
   budget guessing filenames. Confirmed from raw tool-execution events, not
   model narration.
2. **An 8192-token output cap can't hold a whole-file rewrite of a ~30KB
   file.** Two attempts beat navigation, found the right file, and hit
   `stopReason: length` at exactly `output: 8192`. No `edit` tool exists in
   this envelope, only whole-file `write`. Arithmetic, not a tendency — hit
   exactly, twice.

**Neither wall was patched.** Both are named as open questions for you to
decide, not resolved by me overnight — widening the tool set or the token
cap changes what "the exact envelope" means, and that's not a call to make
unilaterally after seeing a result.

**5 of 8 tasks pin `candidate_output` to the ~30KB file, so wall 2 forecloses
them unconditionally** — no contract can fix an output budget the answer
doesn't fit in. Tonight's contract arm ran only on the 3 tasks it doesn't
foreclose: `flask-extensions`, `fastapi-get-registry`, `autowire`.

**Stage 5 — same 3 tasks, brief+contract: still 0/9 accepted, but
completely different in kind.**

- **Navigation is fixed, fully.** Zero `EISDIR` loops, zero blind guesses,
  across all 9 attempts. The contract's location info does exactly what
  it's supposed to.
- **`flask-extensions` would be 3/3 correct.** The patch makes the exact
  fix the contract specifies, identically in all 3 reps, oracle passing
  19/19 every time. It's rejected for touching `docs/integrations/flask.md`
  — which the contract itself told it to update, which the real reference
  commit never touches, and which is outside the task's writable scope.
  **A contract-authoring defect, not a capability gap**: the authoring
  prompt forbids handing over the implementation, but doesn't forbid
  scope creep into reasonable-sounding adjacent changes. Not regraded
  tonight — the honest number is 0/3 — but this is the single most
  actionable finding of the night.
- **The other two are genuine, substantial attempts that got real things
  wrong**, not instrument artifacts — read in full, not just labeled.
  `fastapi-get-registry`'s diff writes a real `get_registry()` in both
  required files, with the model visibly reasoning about FastAPI/Starlette
  internals it got partially wrong. `autowire` creates a real 137-line new
  module with mostly-correct patterns and partial oracle credit. This is
  the first result tonight that speaks to model capability rather than
  harness mechanics.

## One reliability caveat, stated plainly

Two of the three admitted contracts (`flask-extensions`, `autowire`)
flipped from leaking to clean on a re-probe of **identical bytes** — no
re-authoring happened. The leak probe samples 3× per condition with a
2-of-3 threshold specifically to smooth model noise, but a full
leaked-to-clean flip on unchanged input is a bigger swing than that design
anticipates being reported as settled. Worth a higher sample count before
this probe is trusted as a hard gate rather than a screen — not
investigated further tonight, since re-running costs real model time
without resolving what's likely inherent variance.

## A correction I made to my own work, mid-night

I initially wrote that Pi's built-in tools are exactly `{read, bash, edit,
write}`, "confirmed from `pi --help`." That's what the one-line summary
says; the full help output lists seven tools, including `grep`/`find`/`ls`
(read-only, off by default). Corrected with a banner in the research doc,
not silently edited. The load-bearing fact survives narrower and still
true: this project's `ENVELOPE_TOOLS` constant doesn't include them — a
deliberate, named choice, not a Pi limitation.

## What I decided not to do, and why

- **Did not widen the envelope's tool set or `max_tokens`.** Changing what
  "the exact envelope" measures, after seeing a result it produced, is
  exactly the kind of post-hoc instrument tuning this project's rule 8
  exists to prevent.
- **Did not regrade `flask-extensions`** despite being confident the code
  fix is correct. The graded, honest number is 0/3.
- **Did not run the conditional qwen27b extension** (stage 8 in the
  original plan). It was scoped to extend the *brief-only* envelope
  baseline across models — but the interesting frontier moved during the
  night, from "does the exact envelope work at all" to "what happens under
  a good contract, and where does contract authoring itself fail." A
  qwen27b brief-only re-run doesn't speak to either. Better spent as a
  deliberate, informed choice than a leftover-budget default.

## What needs a decision from you, in priority order

1. **The `flask-extensions` scope defect** — cheapest fix, clearest payoff.
   Either the authoring prompt should forbid instructing changes outside
   the task's known writable scope, or contracts should stay silent about
   documentation entirely. Worth checking whether this recurs on the other
   7 tasks' contracts once (if) they're re-authored.
2. **The tool-set and `max_tokens` question for the envelope cell** — does
   the real product's implementer child have `edit` and a token budget that
   fits its own working files? If yes, this envelope cell is stricter than
   the product and should be corrected. If the product really is this
   constrained, that's a real, harsher product finding worth surfacing
   rather than working around.
3. **The leak probe's sample count** — 3 samples/2-threshold produced a
   full flip on identical input twice tonight. Worth deciding whether that's
   acceptable noise for a screen or needs more samples before it gates
   anything confirmatory.
4. **Re-authoring the 5 wall-2-foreclosed tasks' contracts is not useful
   until (2) is resolved** — any contract-arm run on them under the current
   cap re-measures the output cap, not the contract.

Everything is committed. Test suite green throughout (391 passed, 4
skipped). Nothing is running right now.

# Clean-machine rehearsal (distribution brief step 6)

**What this is not:** the brief's step 6 describes rehearsing against "the
curated repository" (step 2 of the same sequence) — a separate, lighter
export a real collaborator would actually clone. That export does not
exist yet; step 2 was never done. What follows is the next most useful
thing: a rehearsal against `phase7-workload` itself, cloned fresh and
followed only via its own README — the actual experience anyone cloning
this repository today would have, curated export or not. It is not a
substitute for the real curated-repo rehearsal once that export exists.

## Method

`git clone --branch phase7-workload` from the local repository (not pushed
to `origin` — this branch is local-only) into a disposable directory
outside this repository. Followed only `README.md` and, for the JS side,
`docs/contributing.md`. A live model server (`omlx`, `127.0.0.1:8001`,
`gemma-4-12B-it-MLX-8bit`) happened to be running, so the candidate-delivery
steps were exercised for real rather than only checked for a clean refusal.

## Findings

**Clone size: 167 MiB.** Expected, not a defect — the 106 MiB
`workloads/svcs/screen/` corpus is still fully tracked, by design (see
[`2026-08-11-evidence-archive-index.md`](2026-08-11-evidence-archive-index.md)).
The actual size reduction is curated-export work, not yet done.

**`uv sync` then `uv run pytest`: 466 passed, 0 failed, 4 skipped.** All
green, including `test_the_preinstall_claim_is_true_of_the_environment_runs_actually_get`
— which had shown as a failing, "pre-existing, unrelated" `FileNotFoundError:
'python'` throughout this session's own work, every time run as
`.venv/bin/python -m pytest` (a workaround for a local `rtk` shell hook that
otherwise intercepts `pytest` on this machine). Under the actual documented
`uv run pytest`, in an actual fresh `uv sync`, it passes. **The failure was
an artifact of this session's own bypass invocation, not a real defect** —
worth recording because it was cited as "pre-existing and unrelated" in
several commit messages this session without ever being run the documented
way to confirm that. It was an accurate call each time (the failure really
was unrelated to whatever was being changed), but "the README's own command
passes cleanly" is a stronger and now-verified claim than what was actually
checked before.

**`bun test` failed on a genuinely fresh clone — real gap, now fixed.**
`docs/contributing.md` said `bun test` with no mention of `bun install`
first. Confirmed by deleting `node_modules` and running `bun test`:
`orchestration.test.ts` fails immediately with `Cannot find package
"typebox"` (`guards.test.ts`, which doesn't import it, still passes —
a partial, confusing failure rather than a clean one). Fixed in
`docs/contributing.md` to `bun install && bun test`, with the confirmed
failure mode stated rather than assumed.

**The README's own copy-paste candidate-delivery example runs, but produces
a discard, not a ref.** `--writable "src/**"` matches nothing in this
repository (no `src/` directory exists here — it's the harness project
itself, not a target codebase), so the live attempt correctly reported
`outcome: discarded`, `reason: candidate changed nothing`, exit code 1 —
exactly matching the README's own documented exit-code table. Not a bug:
the example is deliberately generic ("your own repository"), and the
brief's own bar is "a candidate ref or an actionable refusal" — this is
the latter, and it's legible, not a crash. Left as-is rather than rewritten
to be repo-specific, which would undermine the point of the example.

**A real ref-producing attempt was also run, to check the ref lifecycle
end to end**, since the copy-paste example alone only demonstrated the
discard path. A minimal prompt against a disposable target
(`scratch_rehearsal.md`, `--validation "true"`) produced
`refs/satyrn/candidates/rehearsal-smoke`, `git show`'d cleanly, and
`git update-ref -d` discarded it exactly as the tool's own printed
instructions say. Working tree was untouched throughout (confirmed via
`git status --short` before and after). This is the disposable rehearsal
clone, not this repository — nothing here affected `phase7-workload`
itself.

**No untracked files after either test suite run.** `git status --short`
was empty after `uv run pytest` and after `bun test`.

**Owner-specific absolute paths exist in ten tracked markdown files**
(`BRIEF.md` plus nine dated research/spec/plan documents, including this
session's own `2026-08-11-phase7-cycle7-confirmatory-result.md`). All are
either historical command examples (`BRIEF.md`'s local-model-server path)
or accurate, current pointers to the external evidence archive's real
location on the owner's disk — neither is a credential, and none is
misleading. Not fixed: these are honest statements about where things
currently live, not portability bugs to paper over. A curated export
(brief step 2) is where paths like these would actually need to become
either generic or removed.

**No credential-shaped files, no `.env`.** Checked explicitly
(`find . -iname "*.env" -o -iname "*credential*" -o -iname "*secret*"`,
excluding `node_modules`/`.venv`/`.git`) — nothing found.

## What this rehearsal does not establish

- Not a rehearsal of the curated/shareable export (doesn't exist).
- Not a test of the four-task typed-contract path's own candidate-delivery
  flow end to end (that requires the materialized-worktree setup
  `tools/run_cycle7_confirmatory_batch.py` already exercises 64 times over;
  re-deriving it here would have duplicated already-strong evidence rather
  than added new information).
- Not a test from a machine that has never had this project's dependencies
  installed before (this machine already had `uv`, `bun`, and a live model
  server available) — a true first-contact rehearsal on a bare machine
  would still be worth doing before inviting a real collaborator.

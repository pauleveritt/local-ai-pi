"""Author a draft contract from a staged packet, read-only.

The author's whole world is the packet: the base tree and the brief. It
gets `--tools read` and nothing else, which is the firewall's teeth --
the packet's location outside `.workloads/` is only layout hygiene, and
a model with a shell has already demonstrated in this phase what it does
when an answer key is reachable.

The transcript is saved and must be audited before any arm result built
on the draft is believed. A draft authored by a model that saw the
oracle is a contaminated contract, and the only place that evidence
exists is the transcript.

Drafts are written to a directory, never into `workloads/svcs/tasks/`,
so no manifest changes and no `manifest_sha256` moves. Correcting a
draft into a real `contract.md` is a separate, attended step.
"""

import argparse
import hashlib
import json
import re
import sys
import time
from collections.abc import Sequence
from pathlib import Path

from harness.liveness import check_model_server_alive
from harness.processes import run_process
from harness.pi_invocation import pi_command, pi_env
from harness.screen import AUTHOR_EXTENSION

# A contract locates and bounds; it does not implement. These are the
# shapes an implementation takes, and a fenced block containing more than
# a couple of them is the answer rather than a description of where the
# answer goes.
_STATEMENT = re.compile(
    r"^(return|if|elif|else|for|while|with|try|except|finally|raise|yield"
    r"|assert|import|from)\b"
    r"|^[\w\.\[\]]+\s*(=|\+=|-=)\s*[^=]"
)
MAX_SOLUTION_STATEMENTS = 0
"""Zero, not a small number.

A threshold of two looked reasonable until the test for it was written:
`registry-iter`'s entire fix is `return iter(self._services.values())`,
one statement, so any tolerance at all admits the whole answer for the
smallest tasks. A locating contract needs no executable statements --
signatures and call examples match none of these patterns, and anything
the executor must import can be named in prose."""


def solution_statements(text: str) -> list[str]:
    """Python statements inside fenced blocks: the shape of a handed-over fix.

    A heuristic, and documented as one. It cannot tell code that
    *illustrates the problem* from code that *is the answer* --
    `stringified-annotations`'s first draft showed the current guard and
    the fixed guard, and both read alike to a line matcher. It errs
    toward rejection, which costs one authoring call and is the cheaper
    error. Passing this gate does not prove a draft is free of the
    answer; it proves the draft is free of the shape the answer usually
    takes.
    """
    inside, hits = False, []
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            inside = not inside
            continue
        if not inside:
            continue
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith(">>>"):
            continue
        if _STATEMENT.match(stripped):
            hits.append(stripped)
    return hits


MAX_ASIDE_CHARS = 400
"""Longest text outside an outer fence that can still be an apology.

Deliberately the same number as `--min-chars`: a contract shorter than
that is rejected as a stub, so text that short sitting outside a fence
cannot be the contract -- it is the author explaining itself, above the
document or below it, and both have been observed."""

_WRAPPER_INFO = ("markdown", "md", "")


def extract_contract(text: str) -> str:
    """The contract body, without the model's conversation around it.

    The author has no write tool, so it hands the contract back as prose:
    the first draft opened "I don't have a write tool available, so I'll
    present the complete contract content here" and fenced the document
    in a markdown block. Appended raw to a brief, that preamble becomes
    part of the executor's instructions and the arm partly measures the
    author's apology.

    A wrapper is unwrapped; anything else is left alone. Telling the two
    apart is the whole job, and the two errors are not symmetric. Failing
    to unwrap leaves an apology in the draft, where the gate and the first
    human reader both see it. Wrongly unwrapping *deletes* -- an earlier
    version took the span from the first fence to the last whenever that
    span exceeded half the text, which is true of most **plainly written**
    contracts carrying two or more fenced examples. On those it removed
    the title, the locating prose above the first example, and everything
    below the last one, which in a locating contract is the Bounds
    section. It also left the survivor with inverted fence parity, so
    `solution_statements` scanned code as prose and prose as code, and the
    gate reported zero on a draft whose fences held the answer.

    So the rule is biased toward leaving text alone. Unwrap only when the
    opening fence *declares* the document -- ```markdown, ```md, or a bare
    fence -- and the text outside it on either side is too short to be a
    contract. An examples fence (```python, ```text, ```bash) is never a
    wrapper, which is what the destructive case always looked like.
    """
    lines = text.splitlines()
    fences = [i for i, line in enumerate(lines) if line.lstrip().startswith("```")]
    if len(fences) < 2:
        return text.strip()
    if lines[fences[0]].lstrip()[3:].strip().lower() not in _WRAPPER_INFO:
        return text.strip()
    aside = "\n".join(lines[: fences[0]] + lines[fences[-1] + 1 :]).strip()
    if len(aside) > MAX_ASIDE_CHARS:
        return text.strip()
    # Outermost span, not the first matched pair: a wrapped contract
    # legitimately contains ```python examples, and a toggle parser closes
    # on the first of them -- which is how the first attempt at this
    # returned the preamble untouched.
    return "\n".join(lines[fences[0] + 1 : fences[-1]]).strip()


def compose_prompt(instruction: str, writable: tuple[str, ...], brief: str) -> str:
    """The full authoring prompt: shared instruction, this task's real
    writable scope, then the brief.

    The scope line is not a guess. Without it a contract can pass the leak
    probe and the fenced-statement gate while still asking for a change
    outside what the executor is allowed to make -- `flask-extensions`'s
    contract told the executor to update a docs file the manifest's own
    writable policy (`src/svcs/**`) excludes, and a letter-perfect code fix
    was rejected out-of-scope for it. Not oracle information: the
    instruction already asks the author to name the file, so this only
    removes the one way a contract can fail at a boundary it was never
    being tested on.
    """
    scope = (
        f"\n\nThe executor may only change files matching: {', '.join(writable)}\n"
        "Do not describe or require a change to any file outside that list "
        "-- not documentation, not tests, nothing else, even if updating it "
        "would be good practice."
    )
    return f"{instruction.strip()}{scope}\n\n---\n\n{brief.strip()}\n"


def author_one(task: str, args: argparse.Namespace) -> int:
    packet = args.packets / task
    repo, brief = packet / "repo", packet / "brief.md"
    for path in (repo, brief, args.prompt):
        if not path.exists():
            raise SystemExit(f"missing {path}")

    instruction = args.prompt.read_text().strip()
    import harness.workload as workload

    cohort = workload.load_cohort(args.cohort, require_accounting=True)
    manifest = workload.load_manifest(cohort.task_dir(task))
    prompt = compose_prompt(instruction, manifest.writable, brief.read_text())

    # read only: no bash, no edit, no write. The author cannot go looking
    # and cannot modify the tree it is describing.
    argv_pi = pi_command(args.model, prompt, (AUTHOR_EXTENSION,))
    argv_pi = argv_pi[:-1] + ["--tools", "read"] + argv_pi[-1:]

    started = time.monotonic()
    child = run_process(argv_pi, cwd=repo, timeout=args.timeout, env=pi_env())
    elapsed = time.monotonic() - started

    text = ""
    for line in child.stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "message_end":
            message = event.get("message", {})
            if message.get("role") == "assistant":
                body = "".join(
                    c.get("text", "") for c in message.get("content", []) if c.get("type") == "text"
                )
                if body.strip():
                    text = body

    # The stop reason, and whether the author actually finished. Three of
    # the first eight drafts were 29-80 byte preambles -- "Now I'll write
    # the contract:" and nothing after it -- from runs that ended before
    # producing anything. All three were recorded as authored, appended
    # to briefs as if they were contracts, and confounded the arm they
    # were measured in.
    stop_reason = "unknown"
    for line in child.stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "message_end":
            message = event.get("message", {})
            if message.get("role") == "assistant":
                stop_reason = message.get("stopReason") or stop_reason

    # Which budget, if any, ended this run. Without it a short draft is
    # indistinguishable from an author that had nothing to say -- which is
    # exactly the reading three aborted runs got when they were filed as
    # "empty stubs".
    budgets = []
    for line in child.stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "entry_appended":
            kind = event.get("entry", {}).get("customType", "")
            if kind.endswith("_exhausted") or kind in ("read_budget_reached", "author_would_not_stop"):
                budgets.append(kind)

    contract = extract_contract(text)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / f"{task}.md").write_text(contract + "\n")
    (args.out / f"{task}.raw.md").write_text(text)
    (args.out / f"{task}.jsonl").write_text(child.stdout)
    (args.out / f"{task}.provenance.json").write_text(
        json.dumps(
            {
                "task_id": task,
                "model": args.model,
                "tools": "read",
                "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
                "authoring_prompt_sha256": hashlib.sha256(instruction.encode()).hexdigest(),
                "packet": str(packet),
                "elapsed_seconds": round(elapsed, 1),
                "timed_out": child.timed_out,
                "draft_chars": len(contract),
                "stop_reason": stop_reason,
                "budget_events": budgets,
                "solution_statements": len(solution_statements(contract)),
                "solution_statements_raw": len(solution_statements(text)),
                "raw_chars": len(text),
                "unwrapped": contract != text.strip(),
                "argv": list(argv_pi[:-1]),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    # A draft has to be long enough to be a contract and has to come from
    # a run that ended deliberately. Any nonempty string used to count as
    # success, which is how the stubs got through.
    problems = []
    if len(contract.strip()) < args.min_chars:
        problems.append(f"only {len(contract.strip())} chars (min {args.min_chars})")
    if child.timed_out:
        problems.append("timed out")
    if stop_reason not in ("stop", "toolUse"):
        problems.append(f"stopReason={stop_reason}")
    if any(b.endswith("_exhausted") or b == "author_would_not_stop" for b in budgets):
        # Named separately from stopReason so the record says *why* the run
        # ended, not just that it did.
        problems.append("+".join(sorted(set(b for b in budgets if b != "read_budget_reached"))))
    # Gated on the raw text as well as the extracted body, whichever finds
    # more. Extraction is a heuristic over model prose, and a version of it
    # that mangled fence parity made the gate report zero on a draft whose
    # fences held the answer. The gate must not inherit extraction's
    # mistakes: a statement anywhere in either form rejects the draft.
    handed_over = max(
        solution_statements(contract), solution_statements(text), key=len
    )

    # Counted and reported, no longer fatal. Zero tolerance was demonstrated
    # to reject good contracts -- a draft quoting the file's existing import
    # line and showing two caller-side usage examples scored 3 and contained
    # none of the fix -- and a gate that deletes a draft before the leak
    # probe can adjudicate it destroys the artifact the probe exists to
    # judge. Admission is the probe's decision now; this is a flag on the
    # record and a hint to the reader.
    status = "ok" if not problems else "REJECTED: " + "; ".join(problems)
    if handed_over and not problems:
        status = f"ok (WARN: {len(handed_over)} fenced statements, first {handed_over[0][:40]!r})"
    print(f"{task:26} {len(contract):6} chars  {elapsed:6.1f}s  {status}", flush=True)
    if problems:
        # Removed rather than left on disk: a rejected draft that stays
        # is a draft the next sweep will silently use.
        (args.out / f"{task}.md").unlink(missing_ok=True)
        return 1
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--task", action="append", default=None,
        help="repeatable; omit with --cohort to author every included task",
    )
    parser.add_argument(
        "--cohort", type=Path, default=Path("workloads/svcs/cohort.toml"),
        help="omit --task to author every included task; always used to "
        "look up each task's writable scope for the prompt",
    )
    parser.add_argument("--model", required=True)
    parser.add_argument("--server", default="http://127.0.0.1:8001")
    parser.add_argument("--packets", type=Path, default=Path.home() / ".satyrn-authoring")
    parser.add_argument("--prompt", type=Path, default=Path("workloads/svcs/authoring-prompt.md"))
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--timeout", type=float, default=1800.0)
    parser.add_argument(
        "--min-chars",
        type=int,
        default=400,
        help="shortest draft accepted as a contract (stubs ran 29-80 chars)",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="re-author tasks whose draft is already on disk",
    )
    args = parser.parse_args(argv)

    tasks = list(args.task or ())
    if not tasks:
        import harness.workload as workload

        tasks = list(workload.load_cohort(args.cohort, require_accounting=True).included)

    # Before the first call, not between the third and fourth. An
    # unattended sweep that discovers a dead server an hour in has spent
    # an hour producing timeouts and recording them as drafts.
    check_model_server_alive(args.server)

    rejected = []
    for task in tasks:
        existing = args.out / f"{task}.md"
        if existing.is_file() and existing.read_text().strip() and not args.force:
            print(f"{task:26} draft present, skipped", flush=True)
            continue
        # A failure is recorded and the sweep continues. One task whose
        # author ran out of turns should not cost the other seven, and the
        # rejected draft is deleted, so a later resume retries exactly the
        # ones that failed.
        if author_one(task, args) != 0:
            rejected.append(task)

    print(f"\n{len(tasks) - len(rejected)}/{len(tasks)} drafts accepted")
    if rejected:
        print("rejected: " + ", ".join(rejected))
    return 1 if rejected else 0


if __name__ == "__main__":
    sys.exit(main())

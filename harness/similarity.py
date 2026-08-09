"""How much of a candidate is upstream's own text, recorded on every grade.

`svcs` is a public repository and these tasks are real upstream commits,
so every model in this phase has plausibly seen the answers. That is a
property of the workload, not a defect to be fixed, and it bounds what
the cohort can ever claim -- but it can at least be *measured* rather
than assumed away.

The measure is deliberately narrow: what share of the candidate's added
production lines appear verbatim in the target commit's own diff. High
overlap does not prove recall, and low overlap does not prove reasoning.
A model that absorbed the shape of a fix in training and reimplemented it
in its own words scores zero here and looks like clean capability. No
harness can separate those with a public repository.

What it does catch is verbatim reproduction, which is worth catching for
two reasons: it flagged the copied `autowire` candidate at 100% before
anyone read a transcript, and it is the only cheap signal that a result
might be recall. It is recorded, never used to reject -- an attempt is
void when the transcript shows the model left its workspace, not when a
number looks high.

The reassuring finding it produced on first use: both models solved
`magicmock-factory` with 38 lines against upstream's 4, at 0% overlap.
You cannot recall your way to a different answer.
"""

import re
from collections import Counter

_DIFF = re.compile(r"^diff --git a/(?P<a>\S+) b/(?P<b>\S+)")


def added_lines(patch: str, include: tuple[str, ...]) -> list[str]:
    """Meaningful added lines in files matching any `include` prefix.

    Blank lines and comments are dropped: they inflate agreement without
    saying anything about whether the code is the same code.
    """
    out: list[str] = []
    keep = False
    for line in patch.splitlines():
        match = _DIFF.match(line)
        if match:
            keep = any(match.group("b").startswith(p) for p in include)
        elif keep and line.startswith("+") and not line.startswith("+++"):
            stripped = line[1:].strip()
            if stripped and not stripped.startswith("#"):
                out.append(stripped)
    return out


def overlap(candidate: str, reference: str, include: tuple[str, ...]) -> float:
    """Share of the candidate's added production lines found in the reference.

    Multiset rather than set membership, so a candidate repeating one
    line ten times cannot score ten matches against a reference that
    contains it once.
    """
    mine = added_lines(candidate, include)
    if not mine:
        return 0.0
    theirs = Counter(added_lines(reference, include))
    hits = 0
    for line in mine:
        if theirs[line] > 0:
            theirs[line] -= 1
            hits += 1
    return round(hits / len(mine), 3)

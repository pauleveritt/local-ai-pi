"""Does the contract name a path that can be neither read nor created?

The one criterion of five that survived the 2026-08-16 measurement
(`phase11-inspect-contract`, "what survives"). Deterministic: no model,
no grader, no answer key, no network. That is what lets it run in the
product path, where there is no answer key to hold.

Deleted alongside it, and deliberately not reimplemented here:

- the *nomination* rule (which path the contract says to change), which
  tracked the shape of the line rather than what it asked for
- `mechanism_specificity` and `key_claims`, which compared the packet to
  one reference patch and so read a correct alternative solution as a
  defect

Symbol and line-number claims stay unjudged: contracts hedge them in
prose ("or the equivalent internal mechanism"), and a blocking layer that
fires on hedged prose rejects good packets.
"""

import re
from collections.abc import Sequence
from pathlib import Path

# A backticked token that looks like a repository path: a slash and a file
# extension, both required. Without the slash this matches bare words like
# `aget`; without the extension it matches `app.router`. The leading class
# admits a dot so dotfile-rooted paths (`.github/workflows/x.yml`,
# `.claude/skills/x/SKILL.md`) are not silently exempt from the lint, and
# the extension class admits digits (`.py3`, `.mp3`, `.h5`).
_PATH = re.compile(
    r"`([A-Za-z0-9_.][A-Za-z0-9_./-]*/[A-Za-z0-9_.-]+\.[A-Za-z0-9]{1,6})`"
)


class ContractLintUnusable(Exception):
    """The lint cannot judge -- a broken instrument, not a bad packet.

    Kept distinct because conflating the two is a bug this checker
    actually shipped once: its CLI leaked internal errors out as the exit
    code meaning "your packet is bad".
    """


def impossible_paths(
    task: str, writable_files: Sequence[str], base_tree: Path
) -> tuple[str, ...]:
    """Paths the contract names that can be neither read nor created.

    Empty when clean. A path absent from the tree but present in
    `writable_files` is a file the contract declares the implementer will
    create -- the whole shape of an add-a-module task, and judging
    absence alone rejected the committed `autowire` contract for naming
    the module that task exists to add.
    """
    if not writable_files:
        raise ContractLintUnusable(
            "cannot judge without writableFiles: the bounds are evidence, "
            "not decoration -- without them a declared new file is "
            "indistinguishable from a wrong one"
        )
    if not base_tree.is_dir():
        raise ContractLintUnusable(f"cannot judge without a base tree at {base_tree}")

    declared = set(writable_files)
    offending: list[str] = []
    for path in dict.fromkeys(_PATH.findall(task)):
        if (base_tree / path).is_file() or path in declared:
            continue
        offending.append(path)
    return tuple(offending)

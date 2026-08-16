"""A markdown contract file -> the `HandoffContract` wire format.

What an agent writes in-session, and the only producer of a contract in
the product path. YAML front-matter carries the bounds; the body is the
task prose.

The split matters: the bounds are *declared*, never inferred from the
prose. Inferring them is what the gate branch's nomination rule did, and
it was deleted on 2026-08-16 for firing on the shape of a line rather
than on what the line asked for -- three false positives and three false
negatives out of three tasks each.

Only `writableFiles` and `validation` are required of the author. The
remaining keys are filled with empty lists because `isContract()` in
`extensions/implementer/implementer.ts` validates the whole shape; an
author should not have to type fields to satisfy a schema.
"""

import re
from pathlib import Path

import yaml

from harness.typed_contract import HandoffContract

# The opening delimiter must be the very first line, and the closing one a
# line by itself (only trailing spaces/tabs allowed) -- not merely a "---"
# substring anywhere. A naive substring split matched the first "\n---" it
# found even mid-line ("--- see below") and, worse, truncated the body
# silently at any later standalone "---" (a markdown thematic break, for
# instance): with maxsplit=2 everything after a second occurrence vanished
# with no error, in a file whose entire premise is "the body is the task".
_OPENING = re.compile(r"\A---[ \t]*\n")
_CLOSING = re.compile(r"\n---[ \t]*(?:\n|\Z)")


class ContractFileError(Exception):
    """The file is missing, malformed, or incomplete.

    A bad packet, not a broken tool -- the caller maps this to exit 2.
    """


def _string_list(raw: object, field: str) -> list[str]:
    if raw is None:
        return []
    if not isinstance(raw, list) or not all(isinstance(item, str) for item in raw):
        raise ContractFileError(
            f"{field} must be a list of strings; got {type(raw).__name__}"
        )
    return list(raw)


def _reject_unusable_paths(paths: list[str], field: str, path: Path) -> None:
    """Refuse anything `normalizeContractPath` (handoff-contract.ts) would drop.

    That function silently ignores an absolute path, a `..`-escaping one, a
    trailing slash, or -- the one an author reaches for by habit, since
    `--contract-task` manifests use them -- a glob. `writableFiles: [src/**]`
    passes this parser and the path lint (both work on exact strings), then
    the engine's own normalizer empties it out and the implementer can write
    nothing: a silent, wasted model call, not a refusal. Rejecting here means
    the CLI's exit-2 path catches what the engine would otherwise absorb
    quietly.
    """
    for candidate in paths:
        posix = candidate.replace("\\", "/")
        if not candidate or "\x00" in candidate:
            reason = "is empty or contains a null byte"
        elif candidate.startswith("/"):
            reason = "is an absolute path; the implementer only accepts workspace-relative ones"
        elif "*" in candidate:
            reason = (
                "is a glob; the implementer only accepts exact paths -- name "
                "each file explicitly"
            )
        elif posix in (".", "..") or any(
            segment == ".." for segment in posix.split("/")
        ):
            reason = "escapes the workspace with '..'"
        elif candidate.endswith("/"):
            reason = "names a directory, not a file"
        else:
            continue
        raise ContractFileError(f"{path}: {field} entry {candidate!r} {reason}")


def _split_front_matter(text: str, path: Path) -> tuple[str, str]:
    opening = _OPENING.match(text)
    if opening is None:
        raise ContractFileError(
            f"{path}: no front-matter. A contract starts with a '---' line, "
            "then the bounds as YAML, then '---', then the task prose."
        )
    closing = _CLOSING.search(text, opening.end())
    if closing is None:
        raise ContractFileError(
            f"{path}: the front-matter is never closed. Add a '---' line, "
            "alone on its own line, between the bounds and the task prose."
        )
    return text[opening.end() : closing.start()], text[closing.end() :]


def parse_contract_file(path: Path) -> HandoffContract:
    """Read `path` and build the contract the implementer child consumes.

    Raises `ContractFileError` for anything an author can fix.
    """
    if not path.is_file():
        raise ContractFileError(f"no contract file at {path}")

    head, body = _split_front_matter(path.read_text(), path)

    try:
        loaded = yaml.safe_load(head) or {}
    except yaml.YAMLError as error:
        raise ContractFileError(
            f"{path}: the front-matter is not valid YAML -- {error}"
        ) from error
    if not isinstance(loaded, dict):
        raise ContractFileError(
            f"{path}: the front-matter must be a mapping of fields, "
            f"got {type(loaded).__name__}"
        )

    task = body.strip()
    if not task:
        raise ContractFileError(
            f"{path}: the body is empty. The body is the task -- it is what "
            "tells the implementer which operations to perform."
        )

    writable = _string_list(loaded.get("writableFiles"), "writableFiles")
    if not writable:
        raise ContractFileError(
            f"{path}: writableFiles is required and must name at least one "
            "path. It is the bound the implementer is held to, and the lint "
            "cannot tell a file the contract means to create from one it "
            "named by mistake without it."
        )
    _reject_unusable_paths(writable, "writableFiles", path)

    readable = _string_list(loaded.get("readableFiles"), "readableFiles")
    _reject_unusable_paths(readable, "readableFiles", path)

    validation = loaded.get("validation")
    if not isinstance(validation, str) or not validation.strip():
        raise ContractFileError(
            f"{path}: validation is required -- the command the parent runs "
            "to judge the candidate, e.g. 'pytest -q'."
        )

    contract: HandoffContract = {
        "task": task,
        "writableFiles": [{"path": p} for p in writable],
        "readableFiles": readable,
        "acceptanceStrings": _string_list(
            loaded.get("acceptanceStrings"), "acceptanceStrings"
        ),
        "preservedBehavior": _string_list(
            loaded.get("preservedBehavior"), "preservedBehavior"
        ),
        "knownFacts": _string_list(loaded.get("knownFacts"), "knownFacts"),
        "validation": validation.strip(),
    }
    removable = _string_list(loaded.get("removableSymbols"), "removableSymbols")
    if removable:
        contract["removableSymbols"] = removable
    return contract

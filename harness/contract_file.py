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

from pathlib import Path

import yaml

from harness.typed_contract import HandoffContract

_DELIMITER = "---"


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


def _split_front_matter(text: str, path: Path) -> tuple[str, str]:
    if not text.startswith(_DELIMITER):
        raise ContractFileError(
            f"{path}: no front-matter. A contract starts with a '---' line, "
            "then the bounds as YAML, then '---', then the task prose."
        )
    parts = text.split(f"\n{_DELIMITER}", 2)
    if len(parts) < 2:
        raise ContractFileError(
            f"{path}: the front-matter is never closed. Add a '---' line "
            "between the bounds and the task prose."
        )
    return parts[0][len(_DELIMITER) :], parts[1]


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

    validation = loaded.get("validation")
    if not isinstance(validation, str) or not validation.strip():
        raise ContractFileError(
            f"{path}: validation is required -- the command the parent runs "
            "to judge the candidate, e.g. 'pytest -q'."
        )

    contract: HandoffContract = {
        "task": task,
        "writableFiles": [{"path": p} for p in writable],
        "readableFiles": _string_list(loaded.get("readableFiles"), "readableFiles"),
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

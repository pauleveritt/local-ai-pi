"""The experimental cell: what an arm *is*, declared once and checked.

Governing rule 3 requires prompt bytes, model, tools, budgets and
environment to be condition-recorded. It was honoured in prose and not
in code, and the cost was concrete: Experiment B's 32768 output cap
existed only in its driver and its output directory's name, so a record
moved out of that directory could not say what it ran under, and the
value was swapped mid-session and restored afterwards with nothing
attesting either event.

A cell file fixes that, but only because it is **verified rather than
believed**. A declared value nobody checks is the same drift wearing a
filename. `verify` compares the declaration against
`screen.resolve_cell`, which reads the live configuration -- the model
entry Pi will actually use, the extension's bytes on disk -- and a run
refuses to start on a mismatch rather than recording a number that
disagrees with reality.

Deliberately narrow. It carries the conditions that define an arm and
nothing else: not the grading rule (which regrades change on purpose),
not the Pi version or `models.json` digest (which move for legitimate
reasons and are recorded per attempt instead). A cell that grew to
cover everything would have to be edited constantly, and a file edited
constantly stops being a control.
"""

import tomllib
from dataclasses import dataclass
from pathlib import Path

# Compared on every run. Anything outside this list is recorded on the
# attempt but never gates it.
PINNED = (
    "model",
    "tools",
    "extensions",
    "extensions_sha256",
    "wall_clock_seconds",
    "max_tokens",
    "context_window",
    "base_url",
)


class CellMismatch(Exception):
    """The live configuration is not the cell the run claims to be in."""


@dataclass(frozen=True)
class Cell:
    name: str
    description: str
    pinned: dict[str, str]
    path: Path

    def verify(self, resolved: dict[str, str]) -> None:
        """Refuse the run if reality disagrees with the declaration.

        Missing keys count as mismatches. A resolver that silently fails
        to read `models.json` would otherwise produce an empty dict that
        matches everything, which is the failure mode this exists to
        prevent.
        """
        problems = []
        for key in PINNED:
            if key not in self.pinned:
                continue
            declared = str(self.pinned[key])
            actual = resolved.get(key)
            if actual is None:
                problems.append(f"{key}: declared {declared!r}, not resolvable")
            elif str(actual) != declared:
                problems.append(f"{key}: declared {declared!r}, live {actual!r}")
        if problems:
            raise CellMismatch(
                f"live configuration is not cell {self.name!r} ({self.path}):\n"
                + "\n".join(f"  {p}" for p in problems)
                + "\n\nEither the cell is stale or something was changed "
                "underneath it. Do not spend model calls until they agree."
            )


def load_cell(path: Path) -> Cell:
    data = tomllib.loads(path.read_text())
    pinned = {k: str(v) for k, v in data.get("pinned", {}).items()}
    unknown = set(pinned) - set(PINNED)
    if unknown:
        # A typo'd key would otherwise sit in the file looking like a
        # constraint while constraining nothing.
        raise CellMismatch(f"{path}: unknown pinned keys {sorted(unknown)}")
    return Cell(
        name=str(data.get("name", path.stem)),
        description=str(data.get("description", "")),
        pinned=pinned,
        path=path,
    )

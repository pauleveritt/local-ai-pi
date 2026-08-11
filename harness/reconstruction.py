"""Can a reader rebuild the fix from a document, without the repository?

The authoring prompt states the rule this module enforces: *if a competent
reader could reconstruct the change from your sentence without opening the
file, you have written the fix.* Everything else tried so far inspects the
document's **shape** -- fenced statements, keyword patterns -- and shape is
the wrong thing to look at, twice demonstrated:

- A draft passed the fenced-code gate at zero statements while handing over
  `registry-iter`'s whole fix in an English sentence.
- The next draft was rejected at three statements, all of them a quoted
  existing import and two caller-side usage examples.

A novelty check over prose would not have saved the first. The leaked span
`_services.values()` already exists in the base tree at `_core.py:627`; the
reference fix recombines tokens the repository already contains, which is
what most small fixes do.

So this measures the property directly instead of a proxy for it, and it
measures a **difference**. A brief that already names the answer is not the
contract's fault -- `flask-extensions`'s brief names
`app.extensions["svcs_registry"]` outright -- so the score that matters is
what the contract adds over the brief alone, never the absolute.

Comparison is semantic rather than textual. `return iter(self._services.values())`
and `yield from self._services.values()` are different strings and the same
disclosure, so signals are attribute chains and called names, with the
receiver dropped: both reduce to `_services.values`.
"""

import ast
import hashlib
from dataclasses import dataclass


def _chain(node: ast.Attribute) -> str | None:
    """`self._services.values` from the attribute node, or None if computed."""
    parts = [node.attr]
    current: ast.expr = node.value
    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value
    if not isinstance(current, ast.Name):
        return None
    parts.append(current.id)
    return ".".join(reversed(parts))


def signals(code: str) -> set[str]:
    """The disclosure content of a snippet: what it touches and what it calls.

    Receiver names are dropped -- `self._services.values` and
    `registry._services.values` disclose the same thing, and an author
    writing an example is free to name its variable anything. A bare local
    like `reg = Registry()` therefore contributes nothing, which is correct:
    caller-side setup is not the fix.
    """
    found: set[str] = set()
    for tree in _parse_forgivingly(code):
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute):
                chain = _chain(node)
                if chain and "." in chain:
                    # Drop the receiver, keep the path through it.
                    found.add(chain.split(".", 1)[1])
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                found.add(f"{node.func.id}()")
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                module = getattr(node, "module", "") or ""
                for alias in node.names:
                    found.add(f"import:{module}.{alias.name}".replace("..", "."))
    return found


def _parse_forgivingly(code: str) -> list[ast.AST]:
    """Parse what parses. Diff hunks and model output are not valid modules.

    Whole-blob first, then line by line inside a dummy function so that a
    bare `return` or `yield from` -- which is most of what a fix body is --
    still parses. Anything unparseable contributes nothing rather than
    raising: a probe that dies on one malformed line reports a false zero,
    and a false zero here reads as "the contract disclosed nothing".
    """
    trees: list[ast.AST] = []
    try:
        trees.append(ast.parse(code))
        return trees
    except SyntaxError:
        pass
    for line in code.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        for candidate in (stripped, f"def _f():\n    {stripped}"):
            try:
                trees.append(ast.parse(candidate))
                break
            except SyntaxError:
                continue
    return trees


def added_source_lines(patch: str, skip_prefixes: tuple[str, ...] = ("tests/",)) -> str:
    """The reference patch's added production lines, docstrings excluded.

    Test files are skipped because the executor is forbidden to write them,
    so a contract disclosing a test discloses nothing about the work being
    graded. Docstring and comment lines are skipped because prose in the
    reference answer is not the answer.
    """
    kept: list[str] = []
    current_file = ""
    in_docstring = False
    for line in patch.splitlines():
        if line.startswith("+++ b/"):
            current_file = line[6:].strip()
            in_docstring = False
            continue
        if not line.startswith("+") or line.startswith("+++"):
            continue
        if any(current_file.startswith(prefix) for prefix in skip_prefixes):
            continue
        body = line[1:]
        stripped = body.strip()
        if stripped.count('"""') == 1 or stripped.count("'''") == 1:
            in_docstring = not in_docstring
            continue
        if in_docstring or stripped.startswith("#") or not stripped:
            continue
        if stripped.startswith('"""') or stripped.startswith("'''"):
            continue
        kept.append(body)
    return "\n".join(kept)


@dataclass(frozen=True)
class Reconstruction:
    """One task's floor, ceiling, and the gap the contract is responsible for."""

    task_id: str
    target: tuple[str, ...]
    from_brief: tuple[str, ...]
    from_contract: tuple[str, ...]
    contract_sha256: str = ""
    """Hash of the contract text this result was measured against.

    An unattended re-authoring loop that overwrites a draft in place, or
    resumes into a directory holding a mix of old and new drafts, can
    silently point a screen at a probe result for bytes that no longer
    exist. `screen_workload`'s gate checks this against the draft on
    disk before trusting a clean verdict -- an unmeasured contract and a
    stale-measured one must both refuse, not just the first."""

    @property
    def leaked(self) -> tuple[str, ...]:
        """Disclosed by the contract and not by the brief.

        The subtraction is the whole design. Without it, a task whose brief
        already states the answer would condemn every contract written for
        it, forever, for something no author did.
        """
        return tuple(sorted(set(self.from_contract) - set(self.from_brief)))

    @property
    def floor(self) -> float:
        return _share(self.from_brief, self.target)

    @property
    def ceiling(self) -> float:
        return _share(self.from_contract, self.target)

    @property
    def margin(self) -> float:
        """How much of the fix the brief alone does not already give away.

        A task with no margin cannot host this experiment: there is nothing
        for a contract to withhold, so a clean contract and a leaking one
        are indistinguishable. Reported per task rather than averaged away.
        """
        return 1.0 - self.floor

    def payload(self) -> dict[str, object]:
        return {
            "task_id": self.task_id,
            "contract_sha256": self.contract_sha256,
            "target_signals": list(self.target),
            "reconstructed_from_brief": list(self.from_brief),
            "reconstructed_from_contract": list(self.from_contract),
            "leaked": list(self.leaked),
            "floor": round(self.floor, 3),
            "ceiling": round(self.ceiling, 3),
            "margin": round(self.margin, 3),
        }


def contract_hash(text: str) -> str:
    """The hash a probe result is bound to. Same normalization everywhere it's computed."""
    return hashlib.sha256(text.strip().encode()).hexdigest()


def _share(found: tuple[str, ...], target: tuple[str, ...]) -> float:
    if not target:
        return 0.0
    return len(set(found) & set(target)) / len(set(target))

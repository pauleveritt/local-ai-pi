"""Scoped, self-restoring edits to `pi-agent-dir/models.json`.

A cell like `gemma12b-implementer-v1.toml` can need a `maxTokens` value
different from a model's resting entry -- and `models.json` has exactly
one entry per model, shared by every cell that names it. The existing
practice (see that cell's own header comment) was to hand-edit the file,
run, and hand-edit it back -- workable, but nothing enforced the
restore, and a forgotten one would silently break the frozen envelope
cells' reproducibility (`gemma12b-envelope.toml` verifies against this
same shared entry at 8192). This makes the restore structural: a
context manager whose `finally` runs even if the caller raises.

Does not protect against the process being killed outright (SIGKILL) --
nothing at the Python level can. For that failure mode the existing
discipline still applies: check `git diff pi-agent-dir/models.json`
before trusting a cell's next verify().
"""

import json
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

MODELS_JSON = Path(__file__).resolve().parents[1] / "pi-agent-dir" / "models.json"


class ModelConfigError(Exception):
    """The named model, or its maxTokens field, is not where expected."""


def _find_model(data: dict, model_id: str) -> dict:
    for provider in data.get("providers", {}).values():
        for entry in provider.get("models", []):
            if entry.get("id") == model_id:
                return entry
    raise ModelConfigError(f"{model_id!r} is not in {MODELS_JSON}")


@contextmanager
def bumped_max_tokens(
    model_id: str, max_tokens: int, path: Path = MODELS_JSON
) -> Iterator[None]:
    """Set `model_id`'s maxTokens to `max_tokens` for the block, then restore the original value.

    Restores by value, not by re-reading git -- so this is safe to nest
    or call from a worktree with unrelated pre-existing changes to the
    same file. Writes only when the value actually differs, so a no-op
    call leaves the file's mtime and git status untouched.
    """
    original_text = path.read_text()
    data = json.loads(original_text)
    entry = _find_model(data, model_id)
    original = entry.get("maxTokens")
    if original is None:
        raise ModelConfigError(f"{model_id!r} in {path} has no maxTokens field")
    if original == max_tokens:
        yield
        return
    entry["maxTokens"] = max_tokens
    path.write_text(json.dumps(data, indent=2) + "\n")
    try:
        yield
    finally:
        path.write_text(original_text)

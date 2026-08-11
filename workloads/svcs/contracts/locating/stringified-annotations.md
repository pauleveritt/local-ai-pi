Now I have a clear picture. Let me write the contract.

---

# Implementation Contract: Handle String Annotations in Container Parameter Detection

## Behaviour Required

The function `_takes_container` in `src/svcs/_core.py` must recognise a factory's first parameter as requesting the container when its annotation is the string `"Container"` or `"svcs._core.Container"`, in addition to the already-handled cases of the live `Container` object and the string `"svcs.Container"`.

A factory whose container parameter is annotated as `"Container"` (e.g., under `from __future__ import annotations` with `from svcs import Container`) must be treated identically to one annotated with the live `Container` class.

A factory that does not take a container must continue to return `False`.

## Location of the Change

**File:** `src/svcs/_core.py`

**Function:** `_takes_container(factory: Callable) -> bool` (line ~296)

**Exact line to modify:** The annotation check on line ~311:

```python
if (annot := p.annotation) is Container or annot == "svcs.Container":
```

This is the single condition that determines whether the parameter's annotation indicates a container request. The existing pattern handles two cases: identity check against `Container`, and equality against the string `"svcs.Container"`. The change extends this same condition to cover the additional string forms a user's annotation can take.

## Public API

The function `_takes_container` is internal (name-mangled with leading underscore), called from `Registry._register_factory()`. Its signature does not change:

```python
def _takes_container(factory: Callable) -> bool:
```

The public-facing behaviour changes: `Registry.register_factory()` and `Container._lookup()` will now correctly pass the container to factories whose first parameter is annotated with `Container` as a string (from `from __future__ import annotations` or forward references), not just as the live object or the `"svcs.Container"` string.

## Invariants That Must Not Change

1. **Parameter count check:** Factories with zero parameters still return `False`. Factories with more than one parameter still raise `TypeError` with the message `"Factories must take 0 or 1 parameters."`

2. **Name-based detection:** A parameter named `svcs_container` (with no annotation) still triggers `True` regardless of annotation.

3. **Wrong annotations still return `False`:** An annotation of `svcs.Registry` (whether live or string) must still return `False`. The existing test `wrong_annotation` confirms this.

4. **Signature failure safety:** If `inspect.signature()` raises, the function still returns `False` (tested by `test_signature_fails` with `int`).

5. **The `annot` walrus capture:** The existing pattern `(annot := p.annotation)` must remain intact; the change is only in the condition that uses `annot`.

6. **No new imports or dependencies:** The module's existing imports (`inspect`, `attrs`, `Callable`) are sufficient.

## How a Reader Would Know the Work Is Done

1. The condition on the annotation-checking line in `_takes_container` matches the string `"Container"` and `"svcs._core.Container"` in addition to `"svcs.Container"` and `Container` identity.

2. The existing test `test_annotation_str` (checking `"svcs.Container"`) continues to pass.

3. A new test case covering the `"Container"` string form (as produced by `from __future__ import annotations` with `from svcs import Container`) passes.

4. The test `test_nope` with the `wrong_annotation` fixture (annotated as `svcs.Registry`) continues to assert `False` — confirming that not all string annotations match.

5. A factory registered with a string-annotated `Container` parameter receives the container instance when called via `Container._lookup()`.

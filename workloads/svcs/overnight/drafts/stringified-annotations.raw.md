

The `write` tool is not available in this environment. Here is the complete contract content:

---

# Contract: Handle string annotations when detecting the container parameter

## Problem

`_takes_container()` in `src/svcs/_core.py` determines whether a factory
function wants the container injected by inspecting its first parameter. It
recognises the container via two signals:

1. The parameter is named `svcs_container` (any annotation).
2. The parameter's annotation is the `Container` class object, or the string
   `"svcs.Container"`.

Under `from __future__ import annotations`, **all** annotations become strings
at runtime. A user who writes:

```python
from __future__ import annotations
from svcs import Container

def factory(con: Container):
    ...
```

gets the annotation `"Container"` (the bare name), not `"svcs.Container"` and
not the class object. The current check on line 422 of `_core.py` does not
match this case, so the factory is not recognised as wanting the container.

## Target

**File:** `src/svcs/_core.py`

**Function:** `_takes_container` (lines 401–424)

**Specific line to change:** line 422

```python
# Current:
if (annot := p.annotation) is Container or annot == "svcs.Container":
    return True
```

## Required change

Extend the annotation check so that string annotations of `"Container"` (bare
name) are treated equivalently to `"svcs.Container"` (fully qualified) and to
the actual `Container` class object.

The check must recognise **all three** forms as indicating the factory wants
the container:

| Form | When it appears |
|---|---|
| `annot is Container` | No `from __future__ import annotations` in the caller's module |
| `annot == "svcs.Container"` | Explicit string annotation, or future annotations with `svcs.Container` in source |
| `annot == "Container"` | Future annotations with bare `Container` in source (e.g. `from svcs import Container`) |

A correct replacement for line 422 is:

```python
if (annot := p.annotation) is Container or annot in (
    "svcs.Container",
    "Container",
):
    return True
```

Equivalently, any logic that produces the same three-way match is acceptable.

## Invariants that must be preserved

1. **Name-based detection still works.** A parameter named `svcs_container`
   must still trigger `True` regardless of annotation. This check (line 420)
   must not be altered.

2. **No false positives.** Parameters annotated with types that are *not*
   `svcs.Container` must still return `False`. In particular:
   - `annot == "svcs.Registry"` → `False`
   - `annot == "SomeOtherContainer"` → `False`
   - `annot is inspect.Parameter.empty` → `False` (unannotated params)

3. **Zero-parameter factories still return `False`.** The early return on
   lines 416–417 must not be affected.

4. **Multi-parameter factories still raise `TypeError`.** The check on
   lines 419–421 must not be affected.

5. **Signature extraction failures still return `False`.** The try/except on
   lines 411–413 must not be affected.

6. **No new imports.** The change must not add any new imports to `_core.py`.

## Public API surface

- `_takes_container` is a private function (single leading underscore). It is
  called from `Registry._register_factory()` and is directly tested in
  `tests/test_registry.py::TestTakesContainer`.
- The public-facing behaviour is: `Registry.register_factory()` sets
  `takes_container=True` on the resulting `RegisteredService` when the factory
  wants the container. This drives `Container._lookup()` which decides whether
  to call `factory(container)` or `factory()`.
- No public API signatures change.

## Existing tests that must continue to pass

All tests in `tests/test_registry.py::TestTakesContainer`:

- `test_nope` (parametrised: `no_args`, `diff_name`, `wrong_annotation`) —
  these factories must still return `False`.
- `test_name` — `svcs_container` name detection.
- `test_annotation` — class-object annotation detection.
- `test_annotation_str` — `"svcs.Container"` string annotation detection.
- `test_catches_invalid_sigs` — TypeError on multi-param factories.
- `test_call_works` — callable class instances.
- `test_signature_fails` — graceful fallback when signature extraction fails.

## How a reader would know the work is done

1. The annotation check on line 422 of `src/svcs/_core.py` matches `"Container"`
   as well as `"svcs.Container"` and the class object.

2. A new test case in `tests/test_registry.py::TestTakesContainer` demonstrates
   the fix. It defines a factory in a module-level scope (or uses `eval`/
   `exec`) where the annotation is the bare string `"Container"` — not
   `"svcs.Container"` — and asserts `_takes_container` returns `True`.

   The test must exercise the *bare name* string form specifically. The
   existing `test_annotation_str` already covers `"svcs.Container"`, so the
   new test must distinguish itself by using the string `"Container"`.

3. All pre-existing tests pass unchanged.

4. Factories that do not take a container (zero-parameter factories, factories
   with unrelated annotations) continue to have `takes_container=False`.


I only have the `read` tool available, so I cannot write files directly. Here is the complete contract content for `contract.md`:

---

```markdown
# Contract: `autowire` and `aautowire`

## Objective

Add two public functions, `autowire` and `aautowire`, to the `svcs` package.
Both are importable directly from `svcs` (i.e. `from svcs import autowire, aautowire`).

They produce factory callables that resolve a target callable's annotated
parameters from a `svcs.Container` at call time.

---

## Files to change

| File | Change |
|------|--------|
| `src/svcs/_core.py` | Add `autowire` and `aautowire` functions. Import `dataclasses` for `InitVar` handling. |
| `src/svcs/__init__.py` | Export `autowire` and `aautowire` from `__all__`. |

No other files should be modified.

---

## Public API

### `svcs.autowire(fn_or_cls: Callable) -> Callable[[Container], Any]`

Returns a **synchronous factory** — a callable that:

1. Accepts a single `svcs.Container` argument.
2. Inspects the signature of `fn_or_cls`.
3. For each **annotated, non-variadic** parameter:
   - If the annotation is `svcs.Container`, pass the container itself.
   - Otherwise, look up the service from the container using `container.get(annotation)`.
   - If lookup raises `ServiceNotFoundError` **and** the parameter has a default
     value (`param.default is not inspect.Parameter.empty`), use the default instead.
   - If lookup raises `ServiceNotFoundError` and the parameter has **no** default,
     propagate the exception.
4. Call `fn_or_cls` with the resolved positional arguments (in parameter order).
5. Return the result.

### `svcs.aautowire(fn_or_cls: Callable) -> Callable[[Container], Awaitable[Any]]`

Returns an **async factory** — a callable that:

1. Accepts a single `svcs.Container` argument.
2. Inspects the signature of `fn_or_cls`.
3. For each **annotated, non-variadic** parameter:
   - If the annotation is `svcs.Container`, pass the container itself.
   - Otherwise, look up the service from the container using
     `await container.aget(annotation)`.
   - If lookup raises `ServiceNotFoundError` **and** the parameter has a default
     value, use the default instead.
   - If lookup raises `ServiceNotFoundError` and the parameter has **no** default,
     propagate the exception.
4. Call `fn_or_cls` with the resolved positional arguments (in parameter order).
5. If the result is awaitable (`inspect.isawaitable`), await it and return.
6. Otherwise return the result directly.

---

## Signature inspection rules

Both functions must inspect the signature of `fn_or_cls` using
`_robust_signature()` (the existing internal helper at line ~330 of `_core.py`). This provides:

- String annotation resolution via `eval_str=True` with `Container` in the
  locals namespace.
- Graceful fallback if signature inspection fails.

For each parameter in the signature:

| Condition | Action |
|-----------|--------|
| `kind` is `VAR_POSITIONAL` (`*args`) | **Skip** — do not attempt resolution. |
| `kind` is `VAR_KEYWORD` (`**kwargs`) | **Skip** — do not attempt resolution. |
| `annotation` is `inspect.Parameter.empty` **and** `default` is `inspect.Parameter.empty` | **Raise `TypeError`** with a message identifying the parameter name. |
| `annotation` is `inspect.Parameter.empty` (but has a default) | **Skip** — no type to look up, value comes from default. |
| `annotation` is `svcs.Container` (or resolves to it via string) | Pass the container itself. |
| `annotation` is `dataclasses.InitVar[SomeType]` | Unwrap to `SomeType` and resolve that. |
| `annotation` is a string (forward reference) | `_robust_signature` handles evaluation; if evaluation fails at factory-call time, the exception propagates. |
| Any other annotation | Resolve via `container.get()` / `await container.aget()`. |

**Important:** Only parameters with an annotation (after unwrapping `InitVar`)
are resolved from the container. Parameters without annotations are not
resolved — if they also lack a default, that is an error.

### `InitVar` unwrapping

`dataclasses.InitVar` is a special form, not a proper type. Check via:

```python
import dataclasses

def _unwrap_init_var(annotation):
    """Unwrap InitVar[X] to X."""
    if (
        hasattr(annotation, "__origin__")
        and annotation.__origin__ is dataclasses.InitVar
    ):
        return annotation.__args__[0]
    return annotation
```

---

## Default value handling

The rule is: **a default value only masks a missing service for the parameter
whose annotation is the missing type.** It does **not** mask failures that
occur transitively (e.g. if the service factory itself has missing
dependencies).

Implementation: catch `ServiceNotFoundError` specifically during the
`get()` / `aget()` call for that parameter. If caught and the parameter has a
default, use the default. Any other exception (including `ServiceNotFoundError`
raised by a nested factory) propagates.

```python
for name, param in sig.parameters.items():
    # ... skip variadics, handle Container annotation, etc.
    try:
        svc = container.get(resolved_annotation)  # or await container.aget()
    except ServiceNotFoundError:
        if param.default is not inspect.Parameter.empty:
            resolved[name] = param.default
            continue
        raise
```

---

## Bare generator rejection

In `autowire()` (synchronous variant only):

- If `fn_or_cls` is a bare generator function
  (`inspect.isgeneratorfunction(fn_or_cls)` is `True`), raise `TypeError`.
- This check is done at `autowire()` call time (when the factory is created),
  not at factory-call time.
- A callable decorated with `@contextlib.contextmanager` is **not** a bare
  generator function and is allowed.

**`aautowire()` does NOT perform this check.** Async generators are handled
correctly by the container's lifecycle machinery.

---

## Invariants that must be preserved

1. **No changes to existing public API.** `Registry`, `Container`,
   `RegisteredService`, `ServicePing`, `ServiceNotFoundError`, and all their
   methods must behave identically.

2. **No changes to `_robust_signature` or `_takes_container`.** These are
   internal helpers used by the registration machinery.

3. **Container lifecycle is unchanged.** The autowire factory is just a
   regular factory callable — it returns a value (or context manager, or
   awaitable) and the container handles entering/cleaning up as it normally
   would via `register_factory`.

4. **`autowire` returns a sync callable; `aautowire` returns an async callable.**
   This matters because `Container.get()` vs `Container.aget()` distinguishes
   between them.

5. **`aautowire` works with sync callables.** It calls the sync callable
   directly (no threading), then checks if the result is awaitable.

6. **`aautowire` works with sync services.** It uses `await container.aget()`
   which already handles sync factories correctly.

---

## Error handling summary

| Condition | Exception | When raised |
|-----------|-----------|-------------|
| Parameter has no annotation and no default | `TypeError` | At `autowire`/`aautowire` call time (signature inspection). |
| `autowire` target is a bare generator function | `TypeError` | At `autowire` call time. |
| Service not found, parameter has no default | `ServiceNotFoundError` | At factory-call time (when container.get/aget is called). |
| Service not found, parameter has default | (no error) | Default is used silently. |
| String annotation cannot be resolved | `NameError` or similar | At factory-call time (eval_str fails). |
| Signature cannot be inspected (`_robust_signature` returns `None`) | `TypeError` | At `autowire`/`aautowire` call time. |

---

## Acceptance criteria

A reader can verify the work is done by confirming:

1. `from svcs import autowire, aautowire` succeeds.
2. `autowire` and `aautowire` are listed in `svcs.__all__`.
3. `autowire(fn)` returns a sync callable accepting a `Container`.
4. `aautowire(fn)` returns an async callable accepting a `Container`.
5. Annotated parameters are resolved from the container by their annotation.
6. A parameter annotated as `svcs.Container` receives the container itself.
7. Missing services fall back to parameter defaults when available.
8. Missing services without defaults raise `ServiceNotFoundError`.
9. `*args` and `**kwargs` parameters are ignored.
10. `dataclasses.InitVar[X]` annotations resolve as `X`.
11. Unannotated parameters without defaults raise `TypeError`.
12. String annotations (from `from __future__ import annotations`) resolve
    correctly.
13. Bare generator functions passed to `autowire` raise `TypeError`.
14. `@contextlib.contextmanager` decorated callables work with `autowire`.
15. `aautowire` awaits the result of `fn_or_cls` when it is awaitable.
16. `aautowire` works correctly with synchronous callables and synchronous
    services.
17. Existing tests continue to pass (no regression in registry, container, or
    lifecycle behaviour).

---

## Implementation notes

- Both functions should be placed in `src/svcs/_core.py` alongside the other
  core functions.
- Use `_robust_signature()` for signature inspection (it already handles
  string annotations and `Container` in locals).
- The factory returned by `autowire` should be a regular function (not a
  lambda) for better debuggability.
- The factory returned by `aautowire` should be an `async def` function.
- Both factories should accept exactly one positional argument (the container).
- Import `dataclasses` at the top of `_core.py` if not already imported.
- `ServiceNotFoundError` is already imported in `_core.py` from `.exceptions`.
- Use `isgeneratorfunction` from `inspect` (already imported) for the bare
  generator check.
- Use `isawaitable` from `inspect` (already imported) in `aautowire` to check
  if the result of calling `fn_or_cls` needs awaiting.
```

---

**Note:** I only have the `read` tool available, so I cannot write this file directly. The contract above is the complete content for `contract.md`.
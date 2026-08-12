

Now I have a complete picture. Let me write the contract.

---

# Implementation Contract: Enter Context Managers Returned by Async Factories

## Problem Statement

`Container.aget()` currently fails to enter context managers when the factory's *result* is a context manager but the factory call itself produces an awaitable. This occurs when:

1. An **async factory** returns a context manager (sync or async) — the factory call produces a coroutine, which `aget()` awaits, but the resulting CM is never entered.
2. A **sync factory** returns an awaitable that resolves to a context manager — same issue.

The synchronous `get()` method does not have this problem because `_lookup()` calls sync factories directly, so the returned CM is visible before the `aget()` / `get()` dispatch.

## Required Behavior

After `aget()` awaits a factory's coroutine/awaitable, if the *result* of that await is a context manager and the service was registered with `enter=True`, the container must:

- Enter the context manager (using `__aenter__` for async CMs, `__enter__` for sync CMs),
- Register the CM in `self._on_close` so that `aclose()` / `close()` will exit it,
- Cache and return the *entered value* (the result of `__aenter__` / `__enter__`), not the unentered CM.

Both `AbstractAsyncContextManager` and `AbstractContextManager` returned this way must be handled.

## File and Location

**File:** `src/svcs/_core.py`

**Method:** `Container.aget()` (line ~730 in the current file, the final method of the `Container` class)

The change is confined to the body of `aget()`. No other methods, classes, or files need modification. No new public API is introduced.

## Existing Code Pattern (Reference)

The current `aget()` body iterates `svc_types` and for each uncached service has this structure:

```
if enter and isinstance(svc, AbstractAsyncContextManager):
    <enter async CM>
elif enter and isinstance(svc, AbstractContextManager):
    <enter sync CM>
elif isawaitable(svc):
    svc = await svc
```

The synchronous `get()` method, for comparison, has:

```
if enter and isinstance(svc, AbstractContextManager):
    self._on_close.append((name, svc))
    svc = svc.__enter__()
```

The existing `aget()` branches for CMs use the same pattern as `get()`: append `(name, svc)` to `self._on_close`, then rebind `svc` to the result of entering.

## The Gap

The `elif isawaitable(svc)` branch awaits the value but performs no subsequent check for context managers. If the awaited result is a CM, it is cached and returned unentered.

## What Must Change

After the `svc = await svc` line inside the `isawaitable` branch, the code must check whether the *awaited result* is a context manager. If `enter` is `True` and the result is:

- An `AbstractAsyncContextManager`: register it in `self._on_close` and `await` its `__aenter__()`.
- An `AbstractContextManager`: register it in `self._on_close` and call its `__enter__()`.

The registration and entry pattern must match the existing CM-handling branches above it (append `(name, svc)` to `self._on_close`, rebind `svc`).

## Public API

No public API signatures change. The affected method is:

```python
async def aget(self, *svc_types: type) -> object
```

Its contract (from the docstring) already states: "Same as `get` but instantiates asynchronously, if necessary." This change makes that contract hold for CM-returning async factories.

## Invariants That Must Not Change

1. **Synchronous `get()` behavior is unchanged.** The `get()` method must not be modified. Its handling of sync CMs, its `TypeError` for async factories, and its caching behavior are all invariant.

2. **`enter=False` is respected.** When a service is registered with `enter=False`, context managers returned by any factory (sync or async) must NOT be entered, regardless of whether the factory is awaited.

3. **Cached services are returned directly.** The `if cached` branch at the top of the loop must remain unchanged — cached services bypass all factory and CM logic.

4. **`_lookup()` is unchanged.** The `_lookup()` method's behavior — calling the factory synchronously and returning `(False, factory_result, name, enter)` — must not change.

5. **Cleanup registration shape.** Entries in `self._on_close` remain `(str, AbstractContextManager | AbstractAsyncContextManager)` tuples. The `close()` and `aclose()` methods handle dispatching based on `isinstance` checks.

6. **Single-type vs multi-type return.** The final `if len(rv) == 1: return rv[0]; return rv` pattern is unchanged.

7. **`aget()` still handles directly-returned CMs.** The existing `if`/`elif` branches for `AbstractAsyncContextManager` and `AbstractContextManager` (before the `isawaitable` check) must remain functional. These handle the case where `_lookup()` returns a CM directly (e.g., a sync factory that returns a CM).

## How a Reader Would Know the Work Is Done

The change is complete when:

1. **Only `aget()` is modified** in `src/svcs/_core.py`. No other methods or files are touched.

2. **The `isawaitable` branch in `aget()`** now checks the awaited result for `AbstractAsyncContextManager` and `AbstractContextManager` (when `enter` is `True`), entering and registering them using the same `(name, svc)` append pattern as the existing CM branches.

3. **The existing CM-handling branches** (the `if` and first `elif`) are preserved and unchanged.

4. **The existing test** `TestContainer.test_aget_enters_sync_contextmanagers` continues to pass (it exercises a sync factory returning a sync CM via `aget()`).

5. A caller doing this gets the entered value, not the CM:
   ```python
   async def factory():
       return some_async_context_manager()  # returns AbstractAsyncContextManager


   registry.register_factory(MyService, factory)
   async with Container(registry) as con:
       svc = await con.aget(MyService)
       # svc is the result of __aenter__, not the CM itself
   ```

6. The same holds for a sync factory returning an awaitable that resolves to a CM, and for async factories returning sync CMs.
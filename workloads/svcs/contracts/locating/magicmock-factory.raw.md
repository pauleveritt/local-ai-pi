

Now I have a clear picture of the codebase. Let me write the contract.

---

# Implementation Contract: Do Not Crash When a Factory Returns a Mock

## Background

`unittest.mock.MagicMock` and `AsyncMock` objects answer *any* attribute access with another mock. This means `isinstance(mock, AbstractContextManager)` and `isawaitable(mock)` both return `True` for mocks that are neither genuine context managers nor awaitables. When a service factory is replaced with a mock in tests, `Container.get()` and `Container.aget()` currently attempt cleanup/enter/await operations on the mock, which crashes or produces incorrect results.

## File and Location

**File:** `src/svcs/_core.py`

**Target methods on class `Container`:**
- `get(self, *svc_types: type) -> object` — lines ~760–785
- `aget(self, *svc_types: type) -> object` — lines ~870–910

Both methods contain a `for svc_type in svc_types:` loop. Inside each loop, after `self._lookup(svc_type)` returns `(cached, svc, rs)`, the code checks whether `svc` is a coroutine, awaitable, or context manager and handles each case. The fix inserts a guard **before** those existing checks.

## Required Behavior

### `Container.get()`

When a factory registered with `enter=True` returns a `MagicMock` (or subclass), the mock must be returned directly:
- It must **not** be treated as an `AbstractContextManager` — no `__enter__()` call, no entry into `_on_close`.
- It must **not** raise `TypeError("Use aget() for async factories.")` even though `isinstance(mock, AbstractAsyncContextManager)` is `True`.
- The mock must still be cached in `self._instantiated[svc_type]` so subsequent calls return the same object.

### `Container.aget()`

Same as `get()`, plus:
- An `AsyncMock` (which is `isawaitable`) must be returned directly — **not** awaited.
- It must **not** be treated as an `AbstractAsyncContextManager` or `AbstractContextManager` — no `__aenter__()` or `__enter__()` call, no entry into `_on_close`.
- The mock must still be cached in `self._instantiated[svc_type]`.

### Unchanged behavior

- Real factories returning genuine context managers, async context managers, coroutines, awaitables, or plain objects must behave identically to before.
- The `rs.enter` flag must still control whether real context managers are entered.
- The `TypeError` raised by `get()` for async factories must still fire for **non-mock** coroutines and async context managers.
- Caching (`_instantiated`) and cleanup registration (`_on_close`) for real services must be unaffected.

## Public API Involved

No public API signatures change. The change is purely internal:

- `Container.get(*svc_types: type) -> object` — same signature, same return contract
- `Container.aget(*svc_types: type) -> object` — same signature, same return contract

The change is observable by callers who register mock factories:

```python
from unittest.mock import MagicMock, AsyncMock

container.registry.register_factory(MyService, MagicMock)
svc = container.get(MyService)  # must return the mock, not crash

container.registry.register_factory(MyService, AsyncMock)
svc = await container.aget(MyService)  # must return the mock, not crash
```

## Invariants That Must Not Change

1. **Caching invariant:** After `get()` or `aget()` resolves a service, `svc_type in container._instantiated` must be `True`, and subsequent calls return the cached value.
2. **Cleanup invariant:** For real context managers with `rs.enter=True`, the `(rs, cm)` tuple is appended to `_on_close` and `__enter__()` / `__aenter__()` is called. This must not change for non-mock services.
3. **Async rejection invariant:** `Container.get()` must still raise `TypeError("Use aget() for async factories.")` when a **non-mock** coroutine or `AbstractAsyncContextManager` is returned by the factory.
4. **`enter` flag invariant:** When `rs.enter` is `False`, real context managers must still not be entered (mock or not).
5. **`_lookup` behavior:** The `_lookup` method and its return contract `(cached: bool, svc: object, rs: RegisteredService)` must not change.

## Detection Strategy

The code must distinguish a `MagicMock`/`AsyncMock` from a real object. The detection target is `svc` — the return value of `rs.factory(self)` or `rs.factory()` produced by `_lookup`. The check should use `isinstance` against `unittest.mock.MagicMock` (which covers both `MagicMock` and `AsyncMock` as `AsyncMock` is a subclass of `MagicMock`).

The import `from unittest.mock import MagicMock` (or equivalent) may be added to the file if not already present.

## Placement

In both `get()` and `aget()`, the new guard must sit **after** the `if cached:` early-continue and **before** the existing type checks (`iscoroutine`, `isinstance(svc, AbstractAsyncContextManager)`, `isinstance(svc, AbstractContextManager)`, `isawaitable`).

The guard must follow the same `continue` pattern as the cached branch: when a mock is detected, cache it in `_instantiated`, append it to `rv`, and `continue` to the next service type.

## How a Reader Would Know the Work Is Done

1. A test registering a `MagicMock` factory and calling `container.get()` returns the mock without raising an exception or calling `__enter__()`.
2. A test registering an `AsyncMock` factory and calling `await container.aget()` returns the mock without awaiting it or calling `__aenter__()`.
3. The mock appears in `container._instantiated` after resolution.
4. No entry for the mock appears in `container._on_close`.
5. All existing tests pass — real context managers, async context managers, coroutines, and awaitables behave identically to before.
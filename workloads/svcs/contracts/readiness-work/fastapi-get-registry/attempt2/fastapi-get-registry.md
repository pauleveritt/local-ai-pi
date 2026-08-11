Now I have enough context. Let me write the contract.

---

# Implementation Contract: `get_registry()` for FastAPI and Starlette

## Objective

Add a `get_registry()` function to both `svcs.fastapi` and `svcs.starlette` that retrieves the `svcs.Registry` attached by the `lifespan` integration, from either the application object or a test client wrapper.

## Files That Must Change

1. **`src/svcs/fastapi.py`** — add `get_registry` function and its type alias(es)
2. **`src/svcs/starlette.py`** — add `get_registry` function and its type alias(es)

No other source files should be modified.

---

## Behaviour

### Signature (FastAPI)

```python
def get_registry(
    app_or_client: FastAPI | TestClient
) -> svcs.Registry: ...
```

Where `TestClient` is `fastapi.testclient.TestClient`.

### Signature (Starlette)

```python
def get_registry(
    app_or_client: Starlette | TestClient
) -> svcs.Registry: ...
```

Where `TestClient` is `starlette.testclient.TestClient`.

### Contract

| Condition | Required behaviour |
|---|---|
| Given a `FastAPI` / `Starlette` app whose `svcs.fastapi.lifespan` / `svcs.starlette.lifespan` has started (lifespan context is active) | Returns the `svcs.Registry` instance that the lifespan attached to `app.state` under the key `_KEY_REGISTRY` (`"svcs_registry"`). |
| Given a `TestClient` wrapping such an app | Same as above — extracts the underlying app via `client.app` and returns its registry. |
| The returned registry is the *same object* that request-scoped code receives (e.g. via `container(request)` in FastAPI or `svcs_from(request)` in Starlette) | Identity equality: `get_registry(app) is request.state.svcs_registry`. |
| Given an app whose lifespan has not started, or has already shut down | Raises `RuntimeError` (or a subclass) with a message indicating the app has no svcs registry. |
| Given an app that was never configured with `svcs.fastapi.lifespan` / `svcs.starlette.lifespan` | Raises `RuntimeError` (or a subclass). |
| The app and an included router both declare lifespans | Returns the registry from the top-level app's state (the one the lifespan yielded). |

### Invariants That Must Not Change

1. **`lifespan.__call__` behaviour** — The `lifespan` class's `__call__` method already stores `self.registry` into `self._state[_KEY_REGISTRY]` and yields `self._state`. That mechanism must not be altered.

2. **Request-scoped access** — The existing `container(request)` dependency (FastAPI) and `svcs_from(request)` / `SVCSMiddleware` (Starlette) must continue to work identically. No changes to how the registry is looked up during a request.

3. **`_KEY_REGISTRY` constant** — The key `"svcs_registry"` from `svcs._core` is the canonical storage key. The new function must use it (or `getattr` on `app.state` with that attribute name).

4. **No module-level state** — The function must not create or cache any module-level variables. It is a pure accessor.

---

## Placement

### `src/svcs/fastapi.py`

- The new `get_registry` function must be a module-level function, placed **after `DepContainer`** (the last existing module-level item, line ~89).
- It follows the same docstring style as `container()`: a one-paragraph description, no Args/Yields sections for this simple function.
- If a `TypeAlias` is needed for the union type, place it near the top of the file alongside the existing `AsyncGenLifespan`, `AsyncCMLifespan`, `SomeLifespan` aliases (lines 24–30).

### `src/svcs/starlette.py`

- The new `get_registry` function must be a module-level function, placed **after `svcs_from`** (line ~45) and **before `lifespan`** (line ~52). This keeps app-level accessors grouped with `svcs_from` and before the larger class definitions.
- Same docstring style as `svcs_from`.
- Any needed `TypeAlias` placed near the top alongside existing imports.

---

## Key Implementation Hints (What to Check, Not What to Do)

- The registry is stored on `app.state` as an attribute named by `_KEY_REGISTRY` (`"svcs_registry"`). Access via `getattr(app.state, _KEY_REGISTRY, <sentinel>)` — **not** via `app.state._KEY_REGISTRY` (dot notation doesn't work with the string key).
- A `TestClient` (both FastAPI and Starlette) exposes the wrapped application as `client.app`. Detect a test client by checking for the presence of an `app` attribute.
- The `RuntimeError` must be raised (not returned, not silently swallowed) when the registry attribute is absent.
- The function is synchronous — it does not `await` anything. The registry is a plain object on `app.state`, not an async resource.

---

## Existing Patterns to Follow

| Pattern | Example |
|---|---|
| Import of `_KEY_REGISTRY` from `_core` | `from svcs._core import _KEY_REGISTRY` (already present in `starlette.py`; `fastapi.py` imports it directly) |
| Simple accessor function | `aiohttp.get_registry(app)` at line 58 of `aiohttp.py` — takes an app, returns the registry from app state |
| Flask accessor | `flask.get_registry(app)` at line 43 of `flask.py` — takes an app, returns `app.extensions[_KEY_REGISTRY]` |
| Type alias for unions | `SomeLifespan: TypeAlias = AsyncGenLifespan | AsyncCMLifespan` in `fastapi.py` |
| Docstring style | One-line summary, no parameter section for trivial functions (e.g. `aiohttp.get_registry`) |

---

## How a Reader Would Know the Work Is Done

1. `from svcs.fastapi import get_registry` and `from svcs.starlette import get_registry` both succeed without `ImportError`.

2. Calling `get_registry(app)` on a running app (lifespan active) returns a `svcs.Registry` instance that is `is`-equal to the one stored on `app.state.svcs_registry`.

3. Calling `get_registry(client)` on a `TestClient` returns the same registry as `get_registry(client.app)`.

4. Calling `get_registry(app)` on an app that has no lifespan attached (or whose lifespan hasn't started / has shut down) raises `RuntimeError`.

5. The existing `container(request)` dependency (FastAPI) and `svcs_from(request)` / `aget(request, ...)` (Starlette) continue to pass their existing tests unchanged.

6. No new files are created; no existing function signatures are modified.

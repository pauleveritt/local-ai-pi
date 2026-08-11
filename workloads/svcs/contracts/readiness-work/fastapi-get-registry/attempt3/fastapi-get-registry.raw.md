

Now I have enough context. Here is the contract:

---

# Implementation Contract: `get_registry()` for FastAPI and Starlette

## Objective

Add a `get_registry()` function to both `svcs.fastapi` and `svcs.starlette` that retrieves the `Registry` from an application object or a test client, without requiring a direct reference to the `lifespan` wrapper variable.

## Files to change

1. **`src/svcs/fastapi.py`** — add `get_registry` function
2. **`src/svcs/starlette.py`** — add `get_registry` function

Possibly:
3. **`src/svcs/exceptions.py`** — add a new exception type if a dedicated error is needed (see below)

## Existing reference implementations

- **`src/svcs/flask.py`** — `get_registry(app: Flask | None = None) -> Registry` (line ~56). Retrieves from `app.extensions[_KEY_REGISTRY]`.
- **`src/svcs/aiohttp.py`** — `get_registry(app: web.Application) -> svcs.Registry` (line ~44). Retrieves from `app[_AIOHTTP_KEY_REGISTRY]`.

Both raise `KeyError` when the registry is not present. The FastAPI and Starlette integrations should follow this precedent: raise a clear error when no svcs-managed registry is attached.

## Public API signatures

### `svcs.fastapi.get_registry`

```python
def get_registry(app_or_client: FastAPI | TestClient) -> Registry: ...
```

### `svcs.starlette.get_registry`

```python
def get_registry(app_or_client: Starlette | TestClient) -> Registry: ...
```

Both return `svcs.Registry`. Both accept either the application instance or a `TestClient` (from `fastapi.testclient` / `starlette.testclient`, which is `httpx.Client` / `httpx.AsyncClient`).

When given a test client, the function must extract the underlying application via `app_or_client.app` and proceed from there.

## Behavioural requirements

### 1. Returns the same registry object that request-scoped code uses

The registry returned by `get_registry(app)` must be the identical object that:

- **FastAPI**: `svcs.fastapi.container(request)` creates a `Container` from (i.e., `getattr(request.state, _KEY_REGISTRY)`)
- **Starlette**: `SVCSMiddleware` creates a `Container` from (i.e., `scope["state"][_KEY_REGISTRY]`)

Verifiable by asserting `get_registry(app) is <the registry passed to the user's lifespan function>`.

### 2. Works with apps that have both an app-level and router-level lifespan

When a `FastAPI` app includes a router that also declares a lifespan (wrapped with `svcs.fastapi.lifespan`), `get_registry(app)` must return the registry that is actually active in requests. FastAPI merges lifespan states from the app and all included routers; the last one to set `_KEY_REGISTRY` in the merged state wins. The function must return whatever registry request-scoped code would see.

### 3. Works when given a test client

`get_registry(client)` where `client` is a `TestClient` must return the same registry as `get_registry(client.app)`.

### 4. Raises on missing registry

If the application was **not** initialized with a `svcs.fastapi.lifespan` / `svcs.starlette.lifespan` wrapper, the function must raise an exception. It must not return `None`, a bare `Registry()`, or any other meaningless value.

The exception should be specific and informative. The existing Flask/aiohttp integrations raise `KeyError` implicitly. A dedicated exception (e.g., `NoRegistryError` in `svcs.exceptions`) would be preferable for discoverability, but `KeyError` or `RuntimeError` are acceptable if consistent with the project's error conventions.

### 5. Raises after the application has shut down

After the application's lifespan context has exited (the app has shut down), `get_registry(app)` must raise rather than returning the now-closed registry. This distinguishes the "never initialized" and "shut down" cases from the "currently running" case.

## Location details

### `src/svcs/fastapi.py`

The new `get_registry` function should be added at module level. It sits alongside the existing module-level functions and constants:

- `lifespan` (class, line 36)
- `container` (function, line 78)
- `DepContainer` (constant, line 92)

The function must import `_KEY_REGISTRY` from `svcs._core` (already imported at line 23). It must access the `lifespan` class defined in the same module.

The `lifespan` class is an `@attrs.define` with:
- `_lifespan`: the wrapped user lifespan callable
- `_state`: dict holding the merged lifespan state
- `registry`: the `svcs.Registry` instance

The function must locate the `lifespan` instance from the app. For FastAPI, the lifespan callable is stored on `app.router.lifespan_context`. The function must verify it is a `svcs.fastapi.lifespan` instance and return its `registry` attribute.

### `src/svcs/starlette.py`

The new `get_registry` function should be added at module level. It sits alongside the existing module-level functions:

- `svcs_from` (function, line 33)
- `lifespan` (class, line 40)
- `SVCSMiddleware` (class, line 93)
- `get_pings` (function, line 116)
- `aget_abstract` (function, line 130)
- `aget` (overloaded function, line 143+)

The function must import `_KEY_REGISTRY` from `svcs._core` (already imported at line 22). It must access the `lifespan` class defined in the same module.

For Starlette, the lifespan is stored on the app via `app._lifespan`. However, Starlette wraps the lifespan through `lifespan_from_factory()` (from `starlette.routing`). The function must navigate this wrapping to reach the `svcs.starlette.lifespan` instance and return its `registry` attribute.

## Invariants that must not change

1. **Request-scoped access is unchanged.** The `container` dependency (FastAPI) and `svcs_from` / `aget` / `SVCSMiddleware` (Starlette) must continue to work identically. No changes to how the registry is placed on `request.state` / `scope["state"]`.

2. **The `lifespan` class's `__call__` method is unchanged in its external contract.** It must still be an async context manager yielding `dict[str, object] | None`, and must still store `_KEY_REGISTRY` on the yielded state dict.

3. **The `lifespan.registry` attribute remains the authoritative registry.** The registry used by request-scoped containers is the one on the `lifespan` instance. `get_registry` must return that same object.

4. **No new required imports for callers.** The existing import pattern (`import svcs; svcs.fastapi.get_registry(...)`) must work without requiring additional imports beyond `svcs`, `FastAPI`/`Starlette`, and `TestClient`.

5. **Type annotations are correct.** The function's parameter type must accept both the application type and the test client type. The return type must be `svcs.Registry`.

## Verification

The work is done when:

1. `svcs.fastapi.get_registry` and `svcs.starlette.get_registry` are importable and callable.

2. Given an app initialized with `svcs.fastapi.lifespan` / `svcs.starlette.lifespan`, calling `get_registry(app)` after the app has started (inside a `TestClient` context) returns a `svcs.Registry` object.

3. That returned registry is `is`-identical to the registry that request-scoped code accesses (e.g., the one stored on `request.state` under `_KEY_REGISTRY`).

4. `get_registry(client)` where `client` is a `TestClient(app)` returns the same registry as `get_registry(app)`.

5. Calling `get_registry(app)` on an app that was **not** initialized with a svcs lifespan raises an exception (not `None`, not a bare registry).

6. Calling `get_registry(app)` after the app's lifespan context has exited (outside the `TestClient` context manager, after shutdown) raises an exception.

7. Existing tests in `tests/integrations/test_fastapi.py` and `tests/integrations/test_starlette.py` continue to pass.

8. The example test patterns in `docs/examples/fastapi/test_simple_fastapi_app.py` and `docs/examples/starlette/test_simple_starlette_app.py` (which currently use `lifespan.registry` directly) could equivalently use `get_registry(app)`.
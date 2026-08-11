Now I have a clear picture of the codebase. Let me write the contract.

---

# Implementation Contract: `get_registry()` for FastAPI and Starlette Integrations

## Goal

Add a `get_registry()` function to both `svcs.fastapi` and `svcs.starlette` that returns the `Registry` instance attached to an application by the `lifespan` wrapper, enabling access from outside a request context (tests, startup hooks, scripts).

## Files That Must Change

1. **`src/svcs/fastapi.py`** — add `get_registry()` function
2. **`src/svcs/starlette.py`** — add `get_registry()` function

Both modules' `lifespan` classes may also need a small internal change to support detecting whether the lifespan context is active.

## Public API

### `svcs.fastapi.get_registry`

```python
def get_registry(app: FastAPI | TestClient) -> svcs.Registry: ...
```

- **Parameter**: `app` — either a `fastapi.FastAPI` instance or a `fastapi.testclient.TestClient`.
- **Returns**: The `svcs.Registry` that the running lifespan attached to the application.
- **Raises**: `RuntimeError` if the application has no registry attached (lifespan not started, or lifespan already exited).

### `svcs.starlette.get_registry`

```python
def get_registry(app: Starlette | TestClient) -> svcs.Registry: ...
```

- **Parameter**: `app` — either a `starlette.applications.Starlette` instance or a `starlette.testclient.TestClient`.
- **Returns**: The `svcs.Registry` that the running lifespan attached to the application.
- **Raises**: `RuntimeError` if the application has no registry attached (lifespan not started, or lifespan already exited).

## Placement

- **`fastapi.py`**: The new function should be a module-level function, placed after the existing `container` dependency function (line ~82) and before or after the `DepContainer` alias. It follows the pattern of other public functions in the module (e.g., `container`).

- **`starlette.py`**: The new function should be a module-level function, placed after `SVCSMiddleware` and the existing request-scoped helpers (`svcs_from`, `get_pings`, `aget_abstract`, `aget`). It follows the same style as `svcs_from` and `get_pings`.

## Behavioural Requirements

### Returns the same registry object that request-scoped code receives

`get_registry(app)` must return the identical `Registry` instance that a request handler would access via `request.state` (through `_KEY_REGISTRY`). Concretely:

```python
registry = svcs.fastapi.get_registry(app)
# Inside a request handler:
assert request.state.svcs_registry is registry
```

### Works when given a test client

When passed a `TestClient` instead of the application, the function must unwrap it to reach the underlying application. Both `fastapi.testclient.TestClient` and `starlette.testclient.TestClient` expose the wrapped app via the `.app` attribute.

```python
with TestClient(app) as client:
    reg = svcs.fastapi.get_registry(client)  # works
```

### Works with nested lifespans (app + included router)

When both the main application and an included router declare lifespans, the function must still locate and return the correct registry. The `lifespan` wrapper instance is stored on the router; the function must find the `svcs` `lifespan` instance regardless of nesting.

### Raises on no registry

If the application was not created with a `svcs.fastapi.lifespan` / `svcs.starlette.lifespan` wrapper, or the lifespan has not yet started, `get_registry()` must raise `RuntimeError` with a clear message — it must not return `None`, an empty dict, or any other meaningless value.

### Stops returning a registry after shutdown

Once the lifespan context has exited (application shut down), `get_registry()` must raise `RuntimeError` rather than returning the registry. This is a distinct requirement from "no registry attached" — the registry existed but the application is no longer running.

## Invariants That Must Not Change

1. **`lifespan` class `__call__` signature and yield**: The `lifespan.__call__` method must continue to be an `@asynccontextmanager` yielding `dict[str, object] | None` (FastAPI) or `dict[str, object]` / `None` (Starlette). Its public interface is unchanged.

2. **`container` dependency (FastAPI)**: The `container` async generator dependency must continue to work exactly as before — reading from `request.state` via `_KEY_REGISTRY` and yielding a `Container`.

3. **`SVCSMiddleware` (Starlette)**: Must continue to read `_KEY_REGISTRY` from `scope["state"]` and attach `_KEY_CONTAINER`.

4. **`_KEY_REGISTRY` constant**: The string `"svcs_registry"` used as the state key must remain the same. Existing request-scoped code depends on it.

5. **`lifespan.registry` attribute**: The `registry` attribute on the `lifespan` instance remains the canonical registry object.

6. **`_state` population**: The pattern `self._state[_KEY_REGISTRY] = self.registry` inside the lifespan context must continue.

## Internal Mechanism Hints (Not Implementation)

- The `lifespan` class instance is what gets passed to the framework as the lifespan handler. It is accessible via the application's router — `app.router.lifespan_context` (FastAPI) or `app.router.lifespan` (Starlette).

- The `lifespan` class has a `registry` attribute (attrs field) that holds the `Registry` instance. This is the object `get_registry()` must return.

- To satisfy the "stops returning after shutdown" requirement, the `lifespan` class needs a way to know whether its `__call__` async context is currently active. The `_state` field (populated inside the context) or a new private tracking attribute on the `lifespan` class can serve this purpose.

- The function must check that the lifespan instance it finds is actually an instance of the `svcs` `lifespan` class (not some other lifespan), and that the lifespan is currently active.

## How a Reader Would Know the Work Is Done

1. **`svcs.fastapi.get_registry` exists** and is importable: `from svcs.fastapi import get_registry`.

2. **`svcs.starlette.get_registry` exists** and is importable: `from svcs.starlette import get_registry`.

3. **Given an app with a running lifespan**, calling `get_registry(app)` returns a `svcs.Registry` instance.

4. **Given a `TestClient` wrapping that app**, calling `get_registry(client)` returns the same `Registry` instance.

5. **The returned registry is the same object** accessible inside a request via `request.state.svcs_registry`.

6. **Given an app with no svcs lifespan**, `get_registry(app)` raises `RuntimeError`.

7. **After the lifespan context exits** (e.g., after `TestClient.__exit__`), `get_registry(app)` raises `RuntimeError`.

8. **Existing tests in `tests/integrations/test_fastapi.py` and `tests/integrations/test_starlette.py`** continue to pass without modification.

9. **Request-scoped access** (`svcs.fastapi.container` / `svcs.fastapi.DepContainer` for FastAPI, `svcs.starlette.svcs_from` / `svcs.starlette.aget` for Starlette) continues to work identically.

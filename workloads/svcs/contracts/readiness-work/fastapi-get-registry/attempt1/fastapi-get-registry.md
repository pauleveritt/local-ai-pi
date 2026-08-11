Now I have enough context. Here is the contract.

---

# Contract: `get_registry()` for FastAPI and Starlette integrations

## Objective

Add a `get_registry()` function to both `svcs.fastapi` and `svcs.starlette` that returns the `svcs.Registry` attached to an application by the `lifespan` wrapper, from outside a request context.

## Files that must change

1. **`src/svcs/fastapi.py`** — the FastAPI integration module.
2. **`src/svcs/starlette.py`** — the Starlette integration module.

No other source files are modified.

---

## Behaviour

### `get_registry(app_or_client) -> svcs.Registry`

A module-level function, added to both `svcs.fastapi` and `svcs.starlette`.

**Accepts:**
- The application object (`FastAPI` or `Starlette` respectively), **or**
- A test client wrapping that application (`fastapi.testclient.TestClient` or `starlette.testclient.TestClient` respectively)

**Returns:**
- The same `svcs.Registry` instance that request-scoped code receives via `request.state.svcs_registry` (FastAPI) or `scope["state"]["svcs_registry"]` (Starlette).

**Raises `RuntimeError` when:**
- The application's lifespan has not yet started (no registry attached yet).
- The application's lifespan has finished / shut down (registry removed).

The error message must identify the problem clearly (lifespan not started or already shut down).

### Test client extraction

When given a test client, the function extracts the underlying application object and proceeds as if given the application directly:

- **FastAPI `TestClient`:** the app is at `client.transport.app`.
- **Starlette `TestClient`:** the app is at `client.app`.

### Router lifespans

The function must return the correct registry when both the application and an included router declare their own lifespans. The registry returned is the one attached to the *application's* state, not a router's. This is the same registry that the application's `lifespan` wrapper attached.

---

## Where the work goes

### `src/svcs/fastapi.py`

1. **New function `get_registry`** — a module-level function placed after the existing `container` dependency function (line ~78) and before `DepContainer`. It sits at the same indentation level as `container` and `DepContainer`.

   **Signature:**
   ```python
   def get_registry(app_or_client: FastAPI | TestClient) -> svcs.Registry:
   ```

   The function must:
   - Accept either a `FastAPI` app or a `TestClient`.
   - Extract the app from a `TestClient` if needed (`client.transport.app`).
   - Retrieve the registry from `app.state` using the key `_KEY_REGISTRY` (imported from `svcs._core`).
   - Raise `RuntimeError` with a clear message if the key is absent.

   **Required new import:** `from fastapi.testclient import TestClient` (or a Union type annotation approach).

2. **Modify `lifespan.__call__`** (line ~54) — the existing async context manager method.

   Two changes inside the `async with self.registry, cm(app, self.registry) as state:` block:

   - **On entry (before `yield`):** store `self.registry` on `app.state` using the key `_KEY_REGISTRY`. This is the same key already used for `self._state[_KEY_REGISTRY]`. The store makes the registry reachable from `app.state` for the duration of the lifespan, enabling `get_registry()` outside a request.

   - **On exit (after `yield`, in an `else` or `finally` clause of the `async with`):** remove the registry key from `app.state`. This ensures `get_registry()` raises `RuntimeError` after shutdown rather than returning a stale/closed registry.

   The existing line `self._state[_KEY_REGISTRY] = self.registry` is **not removed**; it continues to serve request-scoped access.

### `src/svcs/starlette.py`

Mirror the FastAPI changes:

1. **New function `get_registry`** — a module-level function placed after `aget` (the implementation at line ~227) and before any trailing content. It sits at the same indentation level as the other module-level functions (`svcs_from`, `get_pings`, `aget_abstract`, `aget`).

   **Signature:**
   ```python
   def get_registry(app_or_client: Starlette | TestClient) -> svcs.Registry:
   ```

   The function must:
   - Accept either a `Starlette` app or a `TestClient`.
   - Extract the app from a `TestClient` if needed (`client.app`).
   - Retrieve the registry from `app.state` using the key `_KEY_REGISTRY`.
   - Raise `RuntimeError` with a clear message if the key is absent.

   **Required new import:** `from starlette.testclient import TestClient`.

2. **Modify `lifespan.__call__`** (line ~72) — same pattern as FastAPI.

   - **On entry:** store `self.registry` on `app.state` using `_KEY_REGISTRY`.
   - **On exit:** remove the key from `app.state`.

   The existing line `self._state[_KEY_REGISTRY] = self.registry` is **not removed**.

---

## Public API

### `svcs.fastapi.get_registry(app_or_client: FastAPI | TestClient) -> svcs.Registry`

### `svcs.starlette.get_registry(app_or_client: Starlette | TestClient) -> svcs.Registry`

Both are synchronous functions.

**Caller examples:**

```python
# Given the app object
reg = svcs.fastapi.get_registry(app)
reg = svcs.starlette.get_registry(app)

# Given a test client
reg = svcs.fastapi.get_registry(client)
reg = svcs.starlette.get_registry(client)
```

---

## Invariants that must not change

1. **`lifespan` class interface:** The `lifespan` class constructor signature, attributes (`_lifespan`, `_state`, `registry`), and the `__call__` method's return type (`AsyncGenerator[dict[str, object], None]`) remain unchanged.

2. **Request-scoped access:** The `container` dependency (FastAPI) and `svcs_from` / `SVCSMiddleware` (Starlette) continue to work exactly as before. Request handlers access the container through `request.state` / `scope["state"]` unchanged.

3. **`_KEY_REGISTRY` key on state dict:** The line `self._state[_KEY_REGISTRY] = self.registry` in both `lifespan.__call__` methods is preserved. The state dict yielded to the framework still contains the registry key.

4. **Registry lifecycle:** The `lifespan` wrapper still manages `self.registry` as an async context manager (`async with self.registry`). Registration and cleanup of services on the registry are unchanged.

5. **`DepContainer` alias (FastAPI):** The `DepContainer` type alias and the `container` dependency function are unchanged.

6. **Existing public functions:** `svcs_from`, `get_pings`, `aget_abstract`, `aget`, `SVCSMiddleware` (Starlette) and `container`, `DepContainer` (FastAPI) are all unchanged.

---

## How a reader knows the work is done

1. **`svcs.fastapi.get_registry` exists** and is callable with a `FastAPI` app or `TestClient`, returning the `svcs.Registry` instance.

2. **`svcs.starlette.get_registry` exists** and is callable with a `Starlette` app or `TestClient`, returning the `svcs.Registry` instance.

3. **Identity check:** `get_registry(app)` returns the *same object* (`is`) as the registry accessible inside a request via `request.state.svcs_registry`.

4. **Test client path:** `get_registry(client)` returns the same registry as `get_registry(client.transport.app)` (FastAPI) or `get_registry(client.app)` (Starlette).

5. **Before lifespan:** Calling `get_registry(app)` on an app whose lifespan has not started raises `RuntimeError`.

6. **After shutdown:** Calling `get_registry(app)` after the test client context exits (or the lifespan has finished) raises `RuntimeError`.

7. **Router lifespans:** When a FastAPI app includes a router with its own lifespan, `get_registry(app)` returns the app-level registry, not the router's.

8. **No regression:** All existing tests in `tests/integrations/test_fastapi.py` and `tests/integrations/test_starlette.py` pass unchanged.



I've read the necessary files. Here is the contract.

---

# Contract: Move Flask Registry from `app.config` to `app.extensions`

## Repository

`svcs` — a flexible service locator. The relevant source file is:

- **`src/svcs/flask.py`** — the Flask integration module.

The constant `_KEY_REGISTRY` is imported from `svcs._core` and has the value `"svcs_registry"`.

## Required Behaviour

After `svcs.flask.init_app(app)` returns, the `Registry` instance must be stored in `app.extensions["svcs_registry"]` rather than `app.config["svcs_registry"]`.

If the caller supplies an explicit `registry` argument to `init_app`, that exact object must be the one stored in `app.extensions["svcs_registry"]`.

All public functions that read the registry from the Flask app must source it from `app.extensions` instead of `app.config`. The functions that write or remove it must target `app.extensions` as well.

A verification checklist:

1. `app.extensions["svcs_registry"]` is a `Registry` after `init_app(app)`.
2. `app.config` does **not** contain a key `"svcs_registry"` after `init_app(app)`.
3. Calling `svcs.flask.get_registry(app)` returns the `Registry` from `app.extensions`.
4. Calling `svcs.flask.close_registry(app)` removes the key from `app.extensions` and calls `.close()` on the registry.
5. Request-scoped containers created via `svcs.flask.svcs_from()` still wrap the correct registry.
6. The `teardown` function continues to close request-scoped containers (it operates on `g`, not `app.config`/`app.extensions`, so its body is unaffected).
7. The `registry` and `container` `LocalProxy` objects continue to resolve correctly.

## Affected Functions and Exact Locations

All changes are in **`src/svcs/flask.py`**. The file currently accesses `app.config[_KEY_REGISTRY]` in six locations. Each must be changed to `app.extensions[_KEY_REGISTRY]`.

### 1. `svcs_from(g)` — line ~27

**Current access:** `current_app.config[_KEY_REGISTRY]`

This function creates a `Container` from the registry. The registry source must change from `current_app.config` to `current_app.extensions`.

**Signature (unchanged):**
```python
def svcs_from(g: _AppCtxGlobals = g) -> Container:
```

### 2. `get_registry(app)` — line ~42

**Current access:** `app.config[_KEY_REGISTRY]`

This function returns the registry. The return value must come from `app.extensions` instead of `app.config`.

**Signature (unchanged):**
```python
def get_registry(app: Flask | None = None) -> Registry:
```

### 3. `init_app(app, *, registry=None)` — line ~60

**Current access:** `app.config[_KEY_REGISTRY] = registry or Registry()`

The assignment target must change from `app.config` to `app.extensions`.

**Signature (unchanged):**
```python
def init_app(app: FlaskAppT, *, registry: Registry | None = None) -> FlaskAppT:
```

### 4. `register_factory(app, svc_type, factory, ...)` — line ~80

**Current access:** `app.config[_KEY_REGISTRY].register_factory(...)`

The registry lookup must change from `app.config` to `app.extensions`.

**Signature (unchanged):**
```python
def register_factory(
    app: Flask,
    svc_type: type,
    factory: Callable,
    *,
    enter: bool = True,
    ping: Callable | None = None,
    on_registry_close: Callable | None = None,
) -> None:
```

### 5. `register_value(app, svc_type, value, ...)` — line ~98

**Current access:** `app.config[_KEY_REGISTRY].register_value(...)`

The registry lookup must change from `app.config` to `app.extensions`.

**Signature (unchanged):**
```python
def register_value(
    app: Flask,
    svc_type: type,
    value: object,
    *,
    enter: bool = False,
    ping: Callable | None = None,
    on_registry_close: Callable | None = None,
) -> None:
```

### 6. `close_registry(app)` — line ~157

**Current access:** `app.config.pop(_KEY_REGISTRY, None)`

The `pop` call must target `app.extensions` instead of `app.config`.

**Signature (unchanged):**
```python
def close_registry(app: Flask) -> None:
```

## Invariants That Must Not Change

1. **`_KEY_REGISTRY` value:** The key string `"svcs_registry"` is unchanged. It is imported from `svcs._core` and must remain the lookup key.

2. **`teardown` function:** The teardown handler (line ~150) operates on `g` (`_KEY_CONTAINER`), not on `app.config` or `app.extensions`. Its body must not be modified.

3. **`LocalProxy` objects:** `registry` and `container` are `LocalProxy` instances backed by `get_registry` and `svcs_from` respectively. Their creation expressions must not change; only the internal functions they delegate to are affected.

4. **`overwrite_factory` and `overwrite_value`:** These functions obtain the container via `svcs_from()` and then access `container.registry`. They do not directly access `app.config` or `app.extensions`. Their bodies must not be modified.

5. **`get`, `get_abstract`, `get_pings`:** These functions operate on the container from `g` via `svcs_from()`. They do not directly access `app.config` or `app.extensions`. Their bodies must not be modified.

6. **`init_app` teardown registration:** The call to `app.teardown_appcontext(teardown)` in `init_app` must remain unchanged.

7. **Return type of `init_app`:** Must still return the same `FlaskAppT` instance.

## Documentation Note

The file `docs/integrations/flask.md` contains the sentence:

> *svcs*'s Flask integration uses the {attr}`flask.Flask.config` object to store the {class}`svcs.Registry`

This sentence must be updated to reference {attr}`flask.Flask.extensions` instead of {attr}`flask.Flask.config`.

## How a Reader Knows the Work Is Done

1. A grep for `app\.config\[` or `current_app\.config\[` in `src/svcs/flask.py` returns zero hits.
2. A grep for `app\.extensions\[` or `current_app\.extensions\[` in `src/svcs/flask.py` finds six matches (one per function listed above).
3. The `docs/integrations/flask.md` first paragraph references `Flask.extensions`, not `Flask.config`.
4. No other file in the repository is modified.
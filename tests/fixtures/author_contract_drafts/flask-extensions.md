Now I have a complete understanding of the codebase. Here is the contract:

# Contract: Migrate `svcs` Flask Registry Storage from `app.config` to `app.extensions`

## Objective

Migrate the `svcs` Flask integration's `Registry` storage from `app.config` to `app.extensions` under the key `"svcs_registry"` (defined as `_KEY_REGISTRY` in `src/svcs/_core.py`).

This is the Flask best practice: `app.config` is for configuration values; `app.extensions` is the designated storage location for extension state objects.

## Scope

### Files to Modify

1. **`src/svcs/flask.py`** — All `app.config[_KEY_REGISTRY]` accesses must become `app.extensions[_KEY_REGISTRY]`.
2. **`docs/integrations/flask.md`** — Update any documentation referencing `app.config` for the registry to reference `app.extensions` instead.

### Files NOT to Modify

- `src/svcs/_core.py` — The constant `_KEY_REGISTRY = "svcs_registry"` stays as-is.
- `src/svcs/__init__.py` — No changes.
- `tests/test_flask.py` — Tests should continue to pass without modification (they use the public API).
- Any other files.

## Detailed Changes

### `src/svcs/flask.py` — 6 locations

The constant `_KEY_REGISTRY` is imported from `_core` and used with `app.config` in exactly 6 locations. Each must be changed from `app.config` to `app.extensions`:

| # | Function | Line Pattern | Before | After |
|---|----------|-------------|--------|-------|
| 1 | `svcs_from` | `con = Container(current_app.config[_KEY_REGISTRY])` | `current_app.config[_KEY_REGISTRY]` | `current_app.extensions[_KEY_REGISTRY]` |
| 2 | `get_registry` | `return app.config[_KEY_REGISTRY]` | `app.config[_KEY_REGISTRY]` | `app.extensions[_KEY_REGISTRY]` |
| 3 | `init_app` | `app.config[_KEY_REGISTRY] = registry or Registry()` | `app.config[_KEY_REGISTRY] = ...` | `app.extensions[_KEY_REGISTRY] = ...` |
| 4 | `register_factory` | `app.config[_KEY_REGISTRY].register_factory(...)` | `app.config[_KEY_REGISTRY]` | `app.extensions[_KEY_REGISTRY]` |
| 5 | `register_value` | `app.config[_KEY_REGISTRY].register_value(...)` | `app.config[_KEY_REGISTRY]` | `app.extensions[_KEY_REGISTRY]` |
| 6 | `close_registry` | `app.config.pop(_KEY_REGISTRY, None)` | `app.config.pop(_KEY_REGISTRY, None)` | `app.extensions.pop(_KEY_REGISTRY, None)` |

### `docs/integrations/flask.md` — Documentation update

Search for references to `app.config` in the context of the registry and update them to `app.extensions`. The specific text to look for and update will be in the section describing how the registry is stored on the Flask app object.

## Invariants (Must Not Change)

1. **Request-scoped container lifecycle**: The `Container` is still created per-request on `flask.g` via `svcs_from()`, lazily instantiated from the registry. The `_KEY_CONTAINER` key on `g` is unchanged.
2. **Teardown logic**: The `teardown` function still pops `_KEY_CONTAINER` from `g` and calls `container.close()`. No changes.
3. **Explicit registry passing**: `init_app(app, registry=my_registry)` still works identically.
4. **`LocalProxy` instances**: `registry` and `container` module-level `LocalProxy` objects remain unchanged.
5. **Public API surface**: All function signatures, return types, and docstrings remain identical.
6. **The `_KEY_REGISTRY` constant value**: Remains `"svcs_registry"` (defined in `_core.py`).
7. **`overwrite_factory` / `overwrite_value`**: These functions operate on the container on `g`, not directly on `app.config`/`app.extensions`. They are unaffected.
8. **`get_pings`**: Unaffected (operates on container on `g`).
9. **`get` / `get_abstract`**: Unaffected (operate on container on `g`).

## Verification

### Tests
All existing tests in `tests/test_flask.py` must pass without modification:
```bash
pytest tests/test_flask.py -v
```

### Type checking
```bash
mypy src/svcs/flask.py
```

## Completion Criteria

1. All 6 occurrences of `app.config[_KEY_REGISTRY]` (and `app.config.pop(_KEY_REGISTRY, ...)`) in `src/svcs/flask.py` replaced with the `app.extensions` equivalent.
2. Documentation in `docs/integrations/flask.md` updated to reflect `app.extensions` usage.
3. All tests pass: `pytest tests/test_flask.py -v`.
4. Type checking passes: `mypy src/svcs/flask.py`.
5. No other files modified.

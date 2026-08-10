

I don't have a write tool available, so I'll present the complete contract content here. The full file content for `contract.md` follows:

---

```markdown
# Contract: Make `Registry` Iterable

## Goal

Add `__iter__` to `svcs.Registry` so that callers can walk the registered
services using standard Python iteration (`for service in registry:`) and
collection (`list(registry)`), without reaching into private attributes.

Iterating a registry yields the `RegisteredService` objects that the registry
stores for each registered type — the same objects returned by
`get_registered_service_for()`.

## Repository State

- **Repository:** `svcs` — a dependency container for Python.
- **Key file:** `src/svcs/_core.py` — contains `Registry`, `Container`,
  `RegisteredService`, and `ServicePing`.
- **Registry storage:** `_services: dict[type, RegisteredService]` — a private
  `attrs` field holding the mapping from service type to its
  `RegisteredService` descriptor.
- **Existing dunder:** `__contains__(self, svc_type: type) -> bool` already
  delegates to `svc_type in self._services`.
- **Existing public accessor:** `get_registered_service_for(svc_type)` returns
  `self._services[svc_type]` (or raises `ServiceNotFoundError`).
- **Current gap:** `Container.get_pings()` reaches into
  `self.registry._services.values()` directly because no public iteration
  exists.

## Required Change

### File: `src/svcs/_core.py`

Add a single method to the `Registry` class:

```python
def __iter__(self) -> Iterator[RegisteredService]:
    """
    Iterate over the registered services.

    Yields:
        The :class:`RegisteredService` objects for every type registered on
        this registry.
    """
    return iter(self._services.values())
```

**Placement:** Add this method alongside the other dunder methods
(`__repr__`, `__contains__`, `__enter__`, `__exit__`, `__aenter__`,
`__aexit__`, `__del__`). A natural position is immediately after
`__contains__` (around line 126), since it is the next logical
container-protocol method.

**Import:** `Iterator` must be available. Check the existing import from
`collections.abc` (line 17):

```python
from collections.abc import Awaitable, Callable
```

Add `Iterator` to this import:

```python
from collections.abc import Awaitable, Callable, Iterator
```

That is the **only** code change required.

## Behavior Specification

1. **`for svc in registry:`** — yields each `RegisteredService` in the
   registry, one per registered type.

2. **`list(registry)`** — returns a list of all `RegisteredService` objects.

3. **`len(list(registry))`** — equals the number shown in `repr(registry)`
   (i.e., `len(registry._services)`).

4. **Empty registry:** Iterating an empty registry yields nothing;
   `list(empty_registry) == []`.

5. **Iteration order:** Dict insertion order (Python 3.7+ guarantee). No
   specific ordering is promised beyond that — iteration mirrors
   `self._services.values()`.

6. **Identity:** The objects yielded are the *same* objects stored internally.
   `registry.get_registered_service_for(T) is next(s for s in registry if s.svc_type is T)`.

7. **Mutability during iteration:** The same caveats as dict iteration apply.
   Registering or clearing services while iterating may raise `RuntimeError`
   or produce inconsistent results — this is acceptable and matches standard
   Python container semantics.

## Invariants That Must Be Preserved

| Invariant | Detail |
|-----------|--------|
| **Registration unchanged** | `register_factory`, `register_value`, `_register_factory` must behave identically. |
| **Lookup unchanged** | `get_registered_service_for` must still raise `ServiceNotFoundError` for missing types and return the stored `RegisteredService` for present ones. |
| **Lifecycle unchanged** | `close()`, `aclose()`, context manager entry/exit, `__del__` warning — all unchanged. |
| **`__contains__` unchanged** | `type in registry` still delegates to `self._services`. |
| **`__repr__` unchanged** | Still shows `num_services=N` based on `len(self._services)`. |
| **No new public attributes** | `_services` remains private (leading underscore). No new public fields. |
| **No changes to `Container`** | The `Container` class is untouched by this change. |
| **No changes to `RegisteredService`** | The dataclass itself is untouched. |
| **`attrs.define` compatibility** | The method is a plain instance method; no attrs interaction is affected. |

## Public API Surface

### Before

```python
class Registry:
    __repr__(self) -> str
    __contains__(self, svc_type: type) -> bool
    __enter__(self) -> Registry
    __exit__(...) -> None
    __aenter__(self) -> Registry
    __aexit__(...) -> None
    __del__(self) -> None
    register_factory(...)
    register_value(...)
    get_registered_service_for(svc_type: type) -> RegisteredService
    close() -> None
    aclose() -> None
```

### After

```python
class Registry:
    __repr__(self) -> str
    __contains__(self, svc_type: type) -> bool
    __iter__(self) -> Iterator[RegisteredService]   # ← NEW
    __enter__(self) -> Registry
    __exit__(...) -> None
    __aenter__(self) -> Registry
    __aexit__(...) -> None
    __del__(self) -> None
    register_factory(...)
    register_value(...)
    get_registered_service_for(svc_type: type) -> RegisteredService
    close() -> None
    aclose() -> None
```

## Files That Should Change

| File | Change |
|------|--------|
| `src/svcs/_core.py` | Add `Iterator` to the `collections.abc` import. Add `__iter__` method to `Registry`. |

**Files that must NOT change:**

- `src/svcs/__init__.py` — no new exports needed; `__iter__` is a dunder.
- `src/svcs/exceptions.py` — untouched.
- `src/svcs/_core.py` (other classes) — `Container`, `RegisteredService`,
  `ServicePing` are untouched.
- All integration modules (`aiohttp.py`, `fastapi.py`, `flask.py`,
  `pyramid.py`, `starlette.py`) — untouched.
- All test files — untouched (the existing test suite must continue to pass
  as-is).

## Verification — How a Reader Knows the Work Is Done

1. **The `__iter__` method exists** on `Registry` and returns
   `iter(self._services.values())`.

2. **`Iterator` is imported** from `collections.abc`.

3. **`list(registry)` works** and returns a list of `RegisteredService`
   objects whose length matches `len(registry._services)`.

4. **`for service in registry:` works** and each yielded item is a
   `RegisteredService` with a `svc_type` attribute.

5. **Empty registry iterates to nothing:** `list(svcs.Registry()) == []`.

6. **Identity check:** For any registered type `T`,
   `registry.get_registered_service_for(T)` is the same object (`is`) as
   the corresponding item yielded by iteration.

7. **All existing tests pass** without modification.

8. **No other methods or attributes** on `Registry` have been altered.

## Example Usage (for reader verification)

```python
import svcs

reg = svcs.Registry()
reg.register_factory(str, str)
reg.register_factory(int, int)

# list() works
services = list(reg)
assert len(services) == 2

# for-in works
for rs in reg:
    assert isinstance(rs, svcs.RegisteredService)
    assert rs.svc_type in (str, int)

# identity with get_registered_service_for
for rs in reg:
    assert rs is reg.get_registered_service_for(rs.svc_type)
```
```
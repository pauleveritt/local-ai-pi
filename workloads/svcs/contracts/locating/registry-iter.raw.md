

Now I have a clear picture. Here's the contract:

---

# Implementation Contract: Make `Registry` Iterable

## Repository State

- **File:** `src/svcs/_core.py`
- **Class:** `Registry` (line 93, `@attrs.define`)
- **Private storage:** `_services: dict[type, RegisteredService]` (line 124)

## Required Behaviour

After the change, a `Registry` instance must be iterable, yielding the `RegisteredService` objects it holds:

- `for rs in registry:` iterates over all registered services
- `list(registry)` produces a list of `RegisteredService` instances
- The yielded objects are the same `RegisteredService` instances stored as values in `self._services`
- Iteration order follows dict value iteration order (insertion order in CPython 3.7+)

## Location of Change

Add a single method to the `Registry` class in `src/svcs/_core.py`:

- **Method:** `__iter__`
- **Position:** Beside the existing dunder methods — specifically, place it adjacent to `__contains__` (line 134) or within the existing cluster of dunder methods (`__repr__`, `__contains__`, `__enter__`, `__exit__`, `__aenter__`, `__aexit__`, `__del__`)
- **Follow the pattern of:** `__contains__` (line 134), which also operates on `self._services`

## Public API

```python
def __iter__(self) -> Iterator[RegisteredService]: ...
```

The return type annotation should use `collections.abc.Iterator[RegisteredService]`. The `Iterator` import must be added to the existing `collections.abc` import on line 13:

```python
from collections.abc import Awaitable, Callable, Iterator
```

## Existing Usage as Precedent

`Container.get_pings()` (line 505) already accesses `self.registry._services.values()` via a list comprehension. The iterable should expose the same values, making that internal reach unnecessary for callers who simply want to walk registrations.

## Invariants That Must Not Change

1. **`_services` dict integrity:** The `_services` attribute remains a `dict[type, RegisteredService]`. No new storage attribute is added.
2. **Registration behaviour:** `register_factory`, `register_value`, and `_register_factory` are unchanged. Overwriting a registration still replaces the value in `_services`.
3. **`__contains__` semantics:** `svc_type in registry` continues to check dict key membership, not iteration.
4. **Lifecycle methods:** `close()`, `aclose()`, `__enter__`, `__exit__`, `__aenter__`, `__aexit__`, and `__del__` are untouched.
5. **`get_registered_service_for()` behaviour:** Lookup by type and `ServiceNotFoundError` raising on missing types are unchanged.
6. **No mutation during iteration:** The iterator must not mutate `_services`. Callers may register or unregister services during iteration at their own risk (same as dict iteration).

## Verification

The work is complete when:

1. `for rs in registry:` executes without error and yields `RegisteredService` instances
2. `list(registry)` returns a list whose elements are exactly the `RegisteredService` objects stored in `registry._services.values()`
3. An empty registry iterates to zero items: `list(svcs.Registry()) == []`
4. The `Iterator` import is present in the `collections.abc` import line
5. No existing test in `tests/test_registry.py` breaks
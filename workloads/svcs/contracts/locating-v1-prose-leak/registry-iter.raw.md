

# Implementation Contract: Make `Registry` Iterable

## Behaviour

After this change, `Registry` instances must be iterable over the `RegisteredService` objects they hold. Concretely:

1. `for service in registry:` yields each `RegisteredService` stored in the registry.
2. `list(registry)` produces a list of all `RegisteredService` instances.
3. The yielded objects are the same `RegisteredService` instances returned by `registry.get_registered_service_for(svc_type)` — identity equality, not copies.
4. Iteration order is not guaranteed (dict values order), but iteration is consistent with the internal `_services` dict.

## File and Location

**File:** `src/svcs/_core.py`

**Class:** `Registry` (the `@attrs.define` class beginning at the module-level `@attrs.define` decorator)

**Placement:** Add a new `__iter__` method on `Registry`, adjacent to the existing `__contains__` method. The existing dunder methods form a cluster (`__repr__`, `__contains__`, `__enter__`, `__exit__`, `__aenter__`, `__aexit__`, `__del__`); `__iter__` belongs in that same group.

## Public API

Add one method to `Registry`:

```python
def __iter__(self) -> Iterator[RegisteredService]: ...
```

No new imports to `__init__.py` are required — `__iter__` is a data model dunder, not a public name.

The return type annotation should use `collections.abc.Iterator` (or `collections.abc.Iter` as a base class), consistent with the existing `from collections.abc import Awaitable, Callable` import at the top of the file. The `Iterator` (or `Iterable`) name must be added to that import if not already present.

**Note:** A generator function using `yield` naturally satisfies the `Iterator` protocol and returns an iterator, so the implementation is a simple generator that yields from `self._services.values()`.

## Invariants That Must Not Change

1. **`_services` ownership:** The `_services` dict remains private (single underscore). No new public attribute exposing it.
2. **Registration behaviour:** `register_factory`, `register_value`, and `_register_factory` are unchanged.
3. **Lookup behaviour:** `get_registered_service_for` continues to raise `ServiceNotFoundError` for missing types.
4. **Lifecycle methods:** `close`, `aclose`, `__enter__`, `__exit__`, `__aenter__`, `__aexit__`, `__del__` are untouched.
5. **`__contains__` semantics:** The existing `svc_type in registry` check (membership by type) is unaffected — iteration yields `RegisteredService` objects, not types.
6. **`__repr__` output:** The string representation format remains `<svcs.Registry(num_services=…)>`.
7. **`Container` class:** No changes to `Container` or any of its methods.

## Verification

The work is done when:

1. `list(svcs.Registry())` returns `[]` on an empty registry.
2. After `reg.register_value(int, 42)` and `reg.register_value(str, "hello")`, `len(list(reg))` is `2`.
3. Each element of `list(reg)` is a `RegisteredService` instance (identity check: `isinstance(svc, svcs.RegisteredService)`).
4. For any registered type `T`, the `RegisteredService` yielded by iteration is the same object as `reg.get_registered_service_for(T)` (identity: `is` comparison).
5. The existing doctest for `__contains__` (lines ~120–130 of `_core.py`) and all other existing doctests continue to pass.
6. `for service in registry:` is syntactically valid and executes without error.
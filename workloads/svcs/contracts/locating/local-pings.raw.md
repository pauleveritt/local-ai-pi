

Now I have a clear picture of the codebase. Here is the contract:

---

# Implementation Contract: Include Local Services in `Container.get_pings()`

## Behaviour

After the change, `Container.get_pings()` must return `ServicePing` objects for every service type the container would resolve, not only those registered on the `Registry`. Specifically:

1. A service registered via `register_local_factory()` or `register_local_value()` that declares a `ping` callable must appear in the returned list.
2. Where a type is registered on both the container's local registry (`_lazy_local_registry`) and the main `registry`, the local registration's ping is the one reported — if the local registration has no ping, no `ServicePing` is emitted for that type at all (the registry's ping is not used as a fallback).
3. Types registered only on the main `registry` with a ping continue to appear as before.
4. Services (local or registry) that declare no ping continue to produce no `ServicePing`.

## File and Location

**File:** `src/svcs/_core.py`

**Method:** `Container.get_pings` (line ~577). This is the sole method that changes.

It sits between `Container.aclose()` and `Container.get_abstract()`. Its current signature:

```python
def get_pings(self) -> list[ServicePing]:
```

The signature and return type remain unchanged.

## Public API

- **`Container.get_pings() -> list[ServicePing]`** — existing public method. Its contract expands to include locally-registered services.
- **`Container.register_local_factory(svc_type, factory, *, enter, ping, on_registry_close)`** — existing method that populates `_lazy_local_registry`.
- **`Container.register_local_value(svc_type, value, *, enter, ping, on_registry_close)`** — existing method, syntactic sugar for `register_local_factory`.
- **`ServicePing(name, is_async, _svc_type, _ping, _container)`** — existing attrs class, constructed the same way as today.

## Relevant Internal Structure

The `Container` class (attrs.define) has these attributes involved:

| Attribute | Type | Role |
|---|---|---|
| `registry` | `Registry` | Main registry; source of globally registered services |
| `_lazy_local_registry` | `Registry \| None` | Per-container local registry; created on first `register_local_*` call |
| `_instantiated` | `dict[type, tuple[object, RegisteredService]]` | Instance cache (not relevant to this change) |

Both `Registry` instances expose `_services: dict[type, RegisteredService]` and `get_registered_service_for(svc_type) -> RegisteredService`.

The current `get_pings()` iterates only over `self.registry._services.values()`. The `_lookup()` method (line ~612) demonstrates the resolution order: `_instantiated` → `_lazy_local_registry` → `registry`.

## Invariants That Must Not Change

1. **Return type:** `get_pings()` returns `list[ServicePing]` — same type, same element type.
2. **`ServicePing` construction:** Each `ServicePing` is created with `(name, is_async, svc_type, ping_callable, container)` — the same five-argument pattern already in use.
3. **`is_async` determination:** `iscoroutinefunction(rs.ping)` determines `is_async`, as it does today.
4. **No ping, no entry:** A `RegisteredService` with `ping is None` produces no `ServicePing` entry.
5. **Registry-only types unchanged:** A type registered only on `self.registry` with a ping must still appear.
6. **No side effects:** `get_pings()` must not instantiate services or modify container state. It is a read-only introspection method.
7. **`_lazy_local_registry` may be `None`:** The method must handle the case where no local registrations have been made.

## Determination of Correctness

A reader verifies the work by checking:

1. **Local ping inclusion:** After calling `container.register_local_factory(Foo, factory, ping=foo_ping)`, `container.get_pings()` contains a `ServicePing` whose `name` corresponds to `Foo` and whose `_ping` is `foo_ping`.
2. **Shadowing with ping:** When both `registry.register_factory(Foo, ..., ping=reg_ping)` and `container.register_local_factory(Foo, ..., ping=local_ping)` exist, `get_pings()` contains exactly one `ServicePing` for `Foo`, and its `_ping` is `local_ping`.
3. **Shadowing without ping:** When `registry.register_factory(Foo, ..., ping=reg_ping)` and `container.register_local_factory(Foo, ..., ping=None)` (or no ping argument) exist, `get_pings()` contains no `ServicePing` for `Foo`.
4. **Registry-only unchanged:** A type registered only on `registry` with a ping still appears in the returned list.
5. **No local registry:** A container with `_lazy_local_registry is None` produces the same results as before the change.
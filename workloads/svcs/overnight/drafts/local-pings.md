I don't have a write tool available, so I'll provide the complete contract content below. Save it as `contract.md` in the repo root.

---

# Contract: Include locally registered services in health pings

## Problem

`Container.get_pings()` currently only iterates `self.registry._services.values()`.
It ignores services registered locally on the container via
`register_local_factory()` / `register_local_value()`, which live in
`self._lazy_local_registry`.

## Required Behavior

After the change, `get_pings()` must return pings for every service type the
container would actually resolve, respecting the same shadowing rules as
`_lookup()`:

1. **Local-only with ping** — A service registered only on the container that
   declares a `ping` callback **is** included in the result.

2. **Local shadows registry (with ping)** — Where both the container and the
   registry register a service for the same type, and the local registration
   declares a ping, the **local** ping is reported (not the registry's).

3. **Local shadows registry (no ping)** — Where both register the same type but
   the local registration declares **no** ping, **no ping is reported** for that
   type. The registry's ping is **not** used as a fallback.

4. **Registry-only (unchanged)** — Types registered only on the registry with a
   ping continue to be reported exactly as today.

5. **No ping anywhere (unchanged)** — Types with no ping on either the container
   or the registry are not reported.

## Files to Change

- **`src/svcs/_core.py`** — The `Container.get_pings()` method (lines ~714–733).

No other files need modification. The public API surface (`get_pings()` return
type, `ServicePing` attributes) is unchanged.

## Implementation Guidance

The current implementation (lines 724–733) is:

```python
def get_pings(self) -> list[ServicePing]:
    return [
        ServicePing(
            rs.name,
            iscoroutinefunction(rs.ping),
            rs.svc_type,
            rs.ping,
            self,
        )
        for rs in self.registry._services.values()
        if rs.ping is not None
    ]
```

The `_lookup()` method (lines 756–780) already establishes the shadowing
precedence: it checks `_lazy_local_registry` first, then falls back to
`self.registry`. The same precedence must apply to pings.

A correct approach:

1. Build the ping list from the registry's services (same as today).
2. If `self._lazy_local_registry` is not `None`, iterate its services and
   overlay them:
   - For each local `RegisteredService` whose `svc_type` is **not** already in
     the result, and which has a `ping`, append it.
   - For each local `RegisteredService` whose `svc_type` **is** already in the
     result but which has `ping is None`, remove the existing entry (the local
     registration shadows the registry one and contributes no ping).
   - For each local `RegisteredService` whose `svc_type` **is** already in the
     result and which has a `ping`, replace the existing entry with the local
     one (the local ping shadows the registry ping).

The `_lookup` method uses `suppress(ServiceNotFoundError)` when probing the
local registry. The `get_pings` method does not need to call
`get_registered_service_for()` at all — it can directly iterate
`_lazy_local_registry._services.values()` since it's just collecting
information, not resolving a specific type.

### Key structural approach

A clean implementation pattern:

```python
def get_pings(self) -> list[ServicePing]:
    # Start with registry pings
    pings: dict[type, RegisteredService] = {
        rs.svc_type: rs
        for rs in self.registry._services.values()
        if rs.ping is not None
    }

    # Overlay local registrations
    if self._lazy_local_registry is not None:
        for rs in self._lazy_local_registry._services.values():
            if rs.ping is not None:
                pings[rs.svc_type] = rs  # add or replace
            else:
                pings.pop(rs.svc_type, None)  # shadow with no-ping

    return [
        ServicePing(
            rs.name,
            iscoroutinefunction(rs.ping),
            rs.svc_type,
            rs.ping,
            self,
        )
        for rs in pings.values()
    ]
```

This uses a `dict[type, RegisteredService]` keyed by `svc_type` to naturally
handle add/replace/remove semantics in a single pass.

## Invariants to Preserve

1. **Return type** — `get_pings()` must still return `list[ServicePing]`.

2. **`ServicePing` construction** — Each `ServicePing` is constructed with
   `(name, is_async, svc_type, ping, container)` exactly as before. The
   `iscoroutinefunction(rs.ping)` check must use the **local** ping callable
   when shadowing, not the registry's.

3. **No side effects** — `get_pings()` must not instantiate services, modify
   `_instantiated`, or modify `_on_close`. It is a pure query.

4. **`_lazy_local_registry` may be `None`** — The method must handle the case
   where no local registrations exist (the lazy registry was never created).

5. **Registry-only behavior unchanged** — If `_lazy_local_registry` is `None`,
   the behavior must be identical to the current implementation.

6. **`_lookup` shadowing consistency** — The set of types reported by
   `get_pings()` must be a subset of the types the container can resolve via
   `_lookup`. Specifically, if `get_pings()` reports a ping for type `T`, then
   `container.get(T)` must succeed (assuming the type is registered somewhere).

## How to Know the Work Is Done

A reader can verify correctness by checking:

1. **The method body** — `get_pings()` now references `self._lazy_local_registry`
   and handles the overlay/shadowing logic described above.

2. **Registry-only path** — When `_lazy_local_registry is None`, the code path
   produces the same result as the original implementation (only registry
   services with pings).

3. **Shadowing logic** — The overlay step uses `dict` key overwrite for
   local-with-ping (add/replace) and `pop` for local-without-ping (remove).

4. **No other changes** — No other methods, classes, or files are modified.
   The `ServicePing` class is untouched. `_lookup()` is untouched.

# Resolve dependencies from type annotations

Add two public functions to `svcs`: `autowire` and `aautowire`.

`autowire(fn_or_cls)` returns a *factory* — a callable that takes a
`svcs.Container`, resolves each of `fn_or_cls`'s annotated parameters from that
container, and calls `fn_or_cls` with the resolved services. It is meant to
replace hand-written factories that do nothing but pull each dependency out of
the container:

```python
registry.register_factory(Handler, autowire(Handler))
```

should behave like a factory that looks up every service `Handler` declares and
passes them in.

## Required behaviour

- Each annotated parameter is resolved from the container by its annotation.
- A parameter annotated as `svcs.Container` receives the container itself rather
  than a looked-up service.
- If a service is not registered and that parameter has a default value, the
  default is used instead of raising. This applies only when the *missing*
  service is the parameter's own annotation — if resolving a parameter fails
  because something it depends on is missing, that failure propagates rather
  than being masked by the default.
- Variadic parameters (`*args`, `**kwargs`) are ignored.
- `dataclasses.InitVar` annotations are unwrapped to the type they wrap.
- A required parameter with neither an annotation nor a default is an error:
  raise `TypeError`.
- String annotations — as produced by `from __future__ import annotations`, or
  written as forward references — resolve to the same services as the
  equivalent non-string annotations. Resolution must tolerate a name that is not
  resolvable at decoration time but is by the time the factory runs.
- Factories that return context managers are entered and cleaned up as usual.
- A bare generator function is rejected with `TypeError`, because its cleanup
  would be silently lost; a callable decorated with `contextlib.contextmanager`
  is fine.

`aautowire` is the asynchronous counterpart. It resolves services through the
container's asynchronous lookup, returns an async factory, and awaits the result
of `fn_or_cls` when that result is awaitable. It also works with synchronous
callables and synchronous services, so an async application can use it
throughout.

Both names are importable directly from `svcs`.

Existing registry, container, and lifecycle behaviour must not change.

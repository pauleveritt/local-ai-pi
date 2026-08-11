

Now I have a thorough understanding of the codebase. Here is the contract:

---

# Implementation Contract: `autowire` and `aautowire`

## Objective

Add two public functions, `autowire` and `aautowire`, to the `svcs` package. Each accepts a callable (`fn_or_cls`) and returns a *factory* — itself a callable accepting a `svcs.Container` — that inspects `fn_or_cls`'s signature, resolves annotated parameters from the container, and invokes `fn_or_cls` with the resolved services.

## Files to Modify / Create

### New file: `src/svcs/_autowire.py`

All implementation logic for `autowire` and `aautowire` lives here. This follows the existing convention of private implementation modules (`_core.py`, `exceptions.py`).

### Modified file: `src/svcs/__init__.py`

- Add `autowire` and `aautowire` to the imports from `._autowire` (or wherever they are defined).
- Add `"autowire"` and `"aautowire"` to `__all__`.

These must be directly importable as `from svcs import autowire, aautowire`.

## Public API Signatures

```python
def autowire(fn_or_cls: Callable) -> Callable[[Container], Any]: ...
def aautowire(fn_or_cls: Callable) -> Callable[[Container], Awaitable[Any]]: ...
```

- `autowire(fn_or_cls)` returns a synchronous factory callable.
- `aautowire(fn_or_cls)` returns an async factory callable (an `async def` or equivalent).

Both return callables that accept a single positional argument: a `svcs.Container`.

## Behavioural Requirements

### Signature Inspection

The factory must inspect `fn_or_cls`'s signature using `inspect.signature`. The existing helper `_robust_signature` in `_core.py` (lines ~300-315) demonstrates the pattern: use `eval_str=True` with `locals={"Container": Container}` to resolve string annotations, and fall back to inspection without `eval_str`. The new code may reuse or replicate this approach.

### Parameter Resolution — `autowire`

For each parameter of `fn_or_cls` (iterating over `sig.parameters`):

1. **Skip** parameters with `kind` of `VAR_POSITIONAL` or `VAR_KEYWORD` (`*args`, `**kwargs`).
2. **Skip** parameters with `POSITIONAL_ONLY`, `POSITIONAL_OR_KEYWORD`, or `KEYWORD_ONLY` kind that have `PARAMETER.empty` as their annotation *and* `PARAMETER.empty` as their default — raise `TypeError` for these (required parameter with no annotation and no default).
3. **`svcs.Container` annotation**: If a parameter's annotation is `svcs.Container` (or its string forms), pass the container object itself as the argument value. Do not perform a lookup.
4. **`dataclasses.InitVar` annotation**: Unwrap `InitVar[T]` to `T` before resolution. Use `typing.get_origin` / `typing.get_args` or equivalent to detect and unwrap.
5. **Annotated parameter with registered service**: Resolve via `container.get(annotation)`. The annotation (after InitVar unwrapping and string evaluation) is the service type key.
6. **Annotated parameter with unregistered service but has a default**: If `container.get(annotation)` raises `ServiceNotFoundError` and the parameter's `default` is not `PARAMETER.empty`, use the default value instead of propagating the error. This masking applies *only* to the direct resolution failure — not to failures that occur transitively inside the service's own factory.
7. **Annotated parameter with unregistered service and no default**: Let the `ServiceNotFoundError` propagate.
8. **Parameter with no annotation but has a default**: Use the default value directly (no lookup attempted).

### Parameter Resolution — `aautowire`

Identical to `autowire` except:

- Use `await container.aget(annotation)` instead of `container.get(annotation)` for service resolution.
- The returned factory is an `async def` that accepts a `Container`.
- After resolving all parameters and calling `fn_or_cls`, if the result is awaitable (check with `inspect.isawaitable`), `await` it before returning.

### Bare Generator Rejection

Before any signature work, check if `fn_or_cls` is a bare generator function using `inspect.isgeneratorfunction`. If it is, raise `TypeError` immediately. A function decorated with `@contextlib.contextmanager` is *not* a generator function (the decorator transforms it), so it passes this check.

Similarly for `aautowire`, check `inspect.isasyncgenfunction` and raise `TypeError`.

### String Annotations

The signature inspection must use `eval_str=True` so that string annotations (from `from __future__ import annotations` or explicit forward references like `"SomeClass"`) are evaluated. The `locals` passed to `inspect.signature` must include `{"Container": Container}` so that `"Container"` or `"svcs.Container"` resolves. The existing `_robust_signature` in `_core.py` shows this pattern. The evaluation may fail at decoration time (when `autowire` is called) for forward references that are not yet defined; the implementation must defer evaluation or tolerate this. One approach: capture the signature at factory-creation time with `eval_str=True`, but if that fails for string annotations, re-evaluate at factory-call time.

### Interaction with Container Lifecycle

The factory returned by `autowire` or `aautowire` is itself a callable that will be passed to `registry.register_factory()`. The container's existing lifecycle logic (`_lookup`, context manager entering, cleanup registration) applies normally to the *result* of calling `fn_or_cls`. The autowire factory's job is solely to gather arguments and call `fn_or_cls`.

## Invariants That Must Not Change

1. **`Container.get` / `Container.aget` signatures and behaviour**: No modifications to these methods.
2. **`Registry.register_factory` / `register_value` signatures and behaviour**: No modifications.
3. **`RegisteredService` structure**: No modifications.
4. **`_takes_container` detection**: The existing convention of detecting container arguments by name (`svcs_container`) or annotation remains unchanged. The autowire factory must be compatible with this — it accepts a single `Container` argument.
5. **`ServiceNotFoundError`**: This exception class is unchanged and is the signal for "service not registered."
6. **`_robust_signature`**: If reused, this function is not modified.
7. **Context manager handling**: The container's `enter` flag and context manager entering logic is untouched. The autowire factory produces whatever `fn_or_cls` produces; the container handles it as it always has.

## How a Reader Knows the Work Is Done

1. `from svcs import autowire, aautowire` succeeds without ImportError.
2. `"autowire"` and `"aautowire"` appear in `svcs.__all__`.
3. `autowire(lambda x: x)(container)` returns the result of calling the lambda with resolved services (or the lambda itself if it takes no annotated parameters).
4. `autowire` raises `TypeError` when given a bare generator function.
5. `aautowire` raises `TypeError` when given a bare async generator function.
6. Calling the returned factory with a container resolves annotated parameters from that container.
7. A parameter annotated as `svcs.Container` receives the container instance.
8. A parameter with a missing service and a default value uses the default.
9. A parameter with no annotation and no default raises `TypeError` at decoration time.
10. String annotations resolve correctly.
11. `dataclasses.InitVar[T]` annotations are treated as `T`.
12. `*args` and `**kwargs` parameters are silently ignored.
13. The `aautowire` factory awaits the result of `fn_or_cls` when it is awaitable.
14. Existing tests for `Container`, `Registry`, and `RegisteredService` continue to pass.
# Make a registry iterable

`Registry` holds the services that have been registered on it, but there is no
supported way to walk them: a caller who wants to inspect what a registry knows
about has to reach past the public API.

Make `Registry` iterable. Iterating one yields the registered services — the
same objects the registry stores for each registered type — so that
`list(registry)` and `for service in registry:` both work.

Registration, lookup, and lifecycle behaviour must not change.

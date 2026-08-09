# Registering a value should not enter it by default

`register_value()` and `register_factory()` both take an *enter* argument
controlling whether the registered object is treated as a context manager to be
entered and later cleaned up.

For a *factory* it defaults to true, which is right: a factory usually builds
something that owns a resource. For a *value* the same default is wrong. A value
is an already-constructed object the caller owns — a connection pool, a client —
and entering it means the container takes over its lifecycle and closes
something the caller did not ask it to close.

Change the default of *enter* to false for `register_value()` in the core
registry and in every framework integration that exposes its own
`register_value()`. Passing *enter* explicitly must keep working in both
directions, and `register_factory()`'s default must not change.

# Let a factory's cleanup see, and swallow, an error

When a container closes, it exits the context managers of the services it
entered. If the block that used the container raised, that exception is
currently not passed to those cleanups: they are exited as though nothing went
wrong, so a factory cannot react to a failure, and cannot suppress it.

Add a *suppress_context_exit* option to `register_factory()` and
`register_value()`. When set, the error that ended the container's context is
passed into the registered service's cleanup context manager, which may then act
on it — including suppressing it, in which case the error does not propagate out
of the container.

The default must preserve today's behaviour. Both synchronous and asynchronous
factories must support it, and the option must be visible on the registered
service the registry stores.

# Enter context managers returned by async factories

A factory may return a context manager, in which case the container enters it,
hands the caller the entered value, and cleans it up when the container closes.

For asynchronous resolution this is incomplete. When a factory resolved through
`Container.aget()` returns a context manager — whether the factory itself is
synchronous or asynchronous — the container must enter it and register its
cleanup, exactly as the synchronous path does, rather than handing back the
unentered context manager.

Both asynchronous and synchronous context managers returned this way must be
handled, and existing synchronous resolution must not change.

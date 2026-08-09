# Do not crash when a factory returns a mock

Service factories are often replaced with `unittest.mock.MagicMock` (or
`AsyncMock`) in tests. A mock answers *any* attribute access with another mock,
which means checks of the form "does this look like a context manager?" or "is
this awaitable?" answer yes for a mock that is neither.

Resolving a service whose factory returns a `MagicMock` currently fails because
of that. Make it work: `container.get()` returns the mock, and
`container.aget()` returns the mock for an `AsyncMock`-based factory, without
attempting cleanup or awaiting that the mock cannot actually support.

Resolution of real factories — including genuine context managers and genuine
awaitables — must not change.

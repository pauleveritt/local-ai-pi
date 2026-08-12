# Example brief: `add-iter`

Add an `__iter__` method to `Registry` so callers can write `list(registry)`
to get every registered service, in registration order. Do not copy the
registry when iterating, and do not let callers reach into its private
storage from outside the class.

Done when a caller can iterate a `Registry` directly with a `for` loop or
`list()` and get back exactly what was registered, in order.

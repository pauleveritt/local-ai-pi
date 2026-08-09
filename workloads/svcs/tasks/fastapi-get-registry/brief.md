# Reach the registry from an app or test client

The FastAPI and Starlette integrations attach a `Registry` to the application
during its lifespan. Request handlers can get at it, but code outside a
request — a test, a startup hook, a script holding the app object — has no
supported way to reach it.

Add `get_registry()` to both the FastAPI and Starlette integrations. It accepts
either the application or a test client, and returns the registry that the
running lifespan attached to that application.

Requirements:

- it returns the same registry object that request-scoped code receives;
- it works when the application and an included router both declare lifespans;
- it works when given a test client instead of the application;
- it raises a clear error when the application has no registry attached, rather
  than returning something meaningless;
- it stops returning a registry once the application has shut down.

Both integrations must expose it, and existing request-scoped access must not
change.

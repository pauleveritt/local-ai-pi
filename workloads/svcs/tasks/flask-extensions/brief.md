# Store the Flask registry where extensions belong

The Flask integration keeps its `Registry` on the application's `config`
mapping. Flask provides `app.extensions` for exactly this purpose: state that
belongs to an extension rather than user configuration, which should not appear
alongside a user's own settings or be dumped with them.

Move the registry to `app.extensions`, under the same key. After
`svcs.flask.init_app(app)`, the registry must be reachable at
`app.extensions["svcs_registry"]`, and an explicitly supplied registry must be
the object stored there.

Every other part of the Flask integration — request-scoped containers, teardown,
and registry closing — must keep working.

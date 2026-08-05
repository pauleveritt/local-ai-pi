## Technology

The solution is a **Python** web application built with **FastAPI**, rendering
**Jinja2** templates. FastAPI is required: the acceptance tests drive the
application through an ASGI test client, and a WSGI framework such as Flask
will fail before any assertion runs.

The graded module is **`app.py` at the project root**, exposing a module-level
object named `app`. It may import from other files, but that module must exist
at that path under that name.

Everything else is your choice: template filenames, route function names, and
where tests live are not prescribed.

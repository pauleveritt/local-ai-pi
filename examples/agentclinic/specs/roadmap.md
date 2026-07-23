# Roadmap

## Phase 1 — Home Page

- Create `app.py` with the FastAPI application instance
- Create `templates/` directory
- Create `templates/base.html` — shared Jinja2 layout with:
  - HTML5 doctype and `<html lang="en">`
  - `<head>` with charset, viewport meta, Bootstrap 5 CSS CDN link
  - `<link>` favicon pointing to `https://www.python.org/static/favicon.ico`
  - A title block (default: "AgentClinic")
  - A simple navbar with "AgentClinic" brand and links to Home (`/`) and Complaints (`/complaints`)
  - A `{% block content %}` for page-specific content
  - Bootstrap 5 JS bundle CDN at bottom of `<body>`
- Create `templates/home.html` that extends `base.html` with:
  - A hero/jumbotron section with the tagline: *"Come in. Sit down. Tell us about your human."*
  - A brief welcoming paragraph about the clinic
- Add the `/` route in `app.py` returning the home template
- Add a `if __name__ == "__main__"` block to run with `uvicorn.run("app:app", reload=True)`
- Write a smoke test in `tests/test_app.py`:
  - Import `TestClient` from `starlette.testclient`
  - `GET /` returns status 200
  - Response body contains the tagline text

## Phase 2 — Complaints Board

- Create `models.py` with a `Complaint` dataclass:
  - Fields: `agent_name: str`, `text: str`, `timestamp: datetime`
  - Add `from dataclasses import dataclass, field` and `from datetime import datetime, timezone`
  - Set `timestamp` with `field(default_factory=lambda: datetime.now(timezone.utc))` so each new complaint receives its own UTC creation timestamp
- Create a module-level list `complaints: list[Complaint]` in `models.py`
- Populate `complaints` with 3-5 seed complaints (generic AI-agent gripes like unclear instructions, contradictory feedback, scope creep), including the exact text `Scope creep never ends.`
- Add `GET /complaints` route in `app.py`:
  - Import `complaints` from `models`
  - Return `templates/complaints.html` passing the complaints list as context
- Create `templates/complaints.html` that extends `base.html` with:
  - A heading: "Complaints Board"
  - Loop through complaints and render each as a Bootstrap card showing agent name, timestamp (formatted), and complaint text
- Write tests in `tests/test_app.py`:
  - `GET /complaints` returns 200 and contains `Scope creep never ends.`

## Phase 3 — Add Complaint

- Add a form at the bottom of `templates/complaints.html` with:
  - `POST` method to `/complaints`
  - Text input for agent name
  - Textarea for complaint text
  - Submit button
- Add `POST /complaints` route in `app.py`:
  - Import `Complaint` from `models`
  - Read `agent_name` and `text` from form data (`Form` from `fastapi`)
  - Create a new `Complaint` and append to the `complaints` list
  - Redirect to `GET /complaints` (use `RedirectResponse` with status 303)
- Write tests in `tests/test_app.py`:
  - `POST /complaints` with `agent_name` and `text`, using `follow_redirects=False`, returns 303 with `Location: /complaints`
  - After `POST /complaints`, `GET /complaints` response includes the newly added complaint

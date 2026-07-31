# Model-Server Liveness Check Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `check_model_server_alive`, a function that confirms the local
model server is responding before cycle 8 ever invokes `pi` against it, and
raises a single dedicated exception when it isn't.

**Architecture:** One new module, `harness/liveness.py`, with one exception
class and one function. The function issues an HTTP GET to the server's
`/v1/models` endpoint via stdlib `urllib.request` and either returns `None`
(alive) or raises `ModelServerDown` (anything else). Tests use a stub HTTP
server (stdlib `http.server`) run in a background thread on an ephemeral
port — no real model server, no new dependency, hermetic and fast, same
discipline cycles 1–6 used for grading.

**Tech Stack:** Python 3.14 stdlib only — `urllib.request`, `urllib.error`,
`json`, `http.server`, `socket`, `threading`. pytest 8.3.4 for tests.

## Global Constraints

- No new dependency. `urllib.request` and `http.server` are stdlib; nothing
  is added to `pyproject.toml`.
- `check_model_server_alive(base_url: str = "http://127.0.0.1:8001") -> None`
  is the exact signature — the default matches `BRIEF.md`'s recorded `omlx`
  server address, as a seam (parameter), not a hardcode.
- Liveness means the server responds at all. Do not inspect which models are
  listed — that is out of scope for this cycle per the design doc.
- No retry/backoff logic — a single attempt, single timeout (2 seconds).
- `ModelServerDown` is the only exception type callers ever need to catch;
  every failure path (connection refused, timeout, a non-2xx status raised
  by `urlopen` as `HTTPError`, unparseable body) is wrapped into it with
  `from` to preserve the original cause.

---

## File Structure

```
harness/
  liveness.py          # CREATE: ModelServerDown, check_model_server_alive
tests/
  test_liveness.py      # CREATE: stub-server test helpers + 3 tests
```

---

### Task 1: `check_model_server_alive` — the alive case

**Files:**
- Create: `harness/liveness.py`
- Create: `tests/test_liveness.py`

**Interfaces:**
- Produces: `harness.liveness.ModelServerDown` (exception class, no
  constructor arguments beyond the standard `Exception` message);
  `harness.liveness.check_model_server_alive(base_url: str =
  "http://127.0.0.1:8001") -> None`.

- [ ] **Step 1: Write the failing test, with its stub-server helper**

Create `tests/test_liveness.py`:

```python
import contextlib
import socket
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from harness.liveness import ModelServerDown, check_model_server_alive


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("localhost", 0))
        return sock.getsockname()[1]


@contextlib.contextmanager
def _stub_server(status: int, body: bytes):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    server = HTTPServer(("localhost", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://localhost:{server.server_port}"
    finally:
        server.shutdown()
        thread.join()
        server.server_close()


def test_check_model_server_alive_returns_none_when_server_responds_ok():
    with _stub_server(200, b'{"data": []}') as base_url:
        assert check_model_server_alive(base_url) is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_liveness.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'harness.liveness'`

- [ ] **Step 3: Write minimal implementation**

Create `harness/liveness.py`:

```python
import json
import urllib.request

TIMEOUT_SECONDS = 2


class ModelServerDown(Exception):
    """Raised when the model server does not respond at the expected endpoint."""


def check_model_server_alive(base_url: str = "http://127.0.0.1:8001") -> None:
    url = f"{base_url}/v1/models"
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT_SECONDS) as response:
            json.loads(response.read())
    except Exception as exc:
        raise ModelServerDown(f"model server not reachable at {url}") from exc
```

No explicit status check: `urllib.request.urlopen` already raises
`HTTPError` for any non-2xx response before the `with` body runs, so a
second check here would be untested dead code for the one case (200) the
`with` body ever actually sees.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_liveness.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add harness/liveness.py tests/test_liveness.py
git commit -m "feat(liveness): check_model_server_alive confirms the server responds"
```

---

### Task 2: Down case — nothing listening

**Files:**
- Modify: `tests/test_liveness.py`

**Interfaces:**
- Consumes: `_free_port()` and `ModelServerDown`/`check_model_server_alive`
  from Task 1 — no changes to their signatures.

- [ ] **Step 1: Write the failing test**

Add to `tests/test_liveness.py`:

```python
import pytest
```

(add this import at the top of the file, alongside the existing imports)

```python
def test_check_model_server_alive_raises_when_nothing_is_listening():
    port = _free_port()
    with pytest.raises(ModelServerDown):
        check_model_server_alive(f"http://localhost:{port}")
```

- [ ] **Step 2: Run test to verify it fails or passes for the right reason**

Run: `uv run pytest tests/test_liveness.py -v`
Expected: PASS already — Task 1's implementation should already raise
`ModelServerDown` on connection refused, since `urllib.request.urlopen`
raises `ConnectionRefusedError`/`URLError` in that case, which the `except
Exception` clause wraps. This step exists to confirm that expectation
against real behavior, not to drive new code.

If it does NOT pass, investigate before moving on — it means the wrapping
in Task 1 is narrower than the design requires (e.g. it only catches a
specific `urllib` exception type instead of the general case), and that
gap must be closed here before adding the next test.

- [ ] **Step 3: Commit**

```bash
git add tests/test_liveness.py
git commit -m "test(liveness): prove ModelServerDown when nothing is listening"
```

---

### Task 3: Down case — server responds, wrong shape (non-vacuity check)

**Files:**
- Modify: `tests/test_liveness.py`

**Interfaces:**
- Consumes: `_stub_server` from Task 1, `ModelServerDown`/
  `check_model_server_alive` from Task 1 — no signature changes.

**Purpose:** Task 2 proves the check reacts to "nothing there at all" — but
that alone can't distinguish a real check from one that swallows a bad
response and returns `None` anyway, since "nothing listening" never
reaches far enough to expose that bug. This task proves the check
completes a real HTTP exchange, gets back an actual (bad) response, and
still classifies it as down. Both tests passing together is the proof;
either alone is not.

- [ ] **Step 1: Write the failing test... expected to already pass**

Add to `tests/test_liveness.py`:

```python
def test_check_model_server_alive_raises_when_server_returns_non_200():
    with _stub_server(500, b"") as base_url:
        with pytest.raises(ModelServerDown):
            check_model_server_alive(base_url)
```

- [ ] **Step 2: Run the full test file**

Run: `uv run pytest tests/test_liveness.py -v`
Expected: PASS, 3 passed. As with Task 2, this confirms the design's
existing behavior rather than driving new code — `urllib.request.urlopen`
raises `HTTPError` for a 500 status, which the same `except Exception`
clause in `check_model_server_alive` wraps into `ModelServerDown`.

If any of the 3 tests fail here, stop and fix `harness/liveness.py` before
continuing — a failure means the implementation doesn't yet match the
design for one of the three proven behaviors.

- [ ] **Step 3: Run the whole suite to confirm no regressions**

Run: `uv run pytest -q`
Expected: all tests pass (32 from prior cycles + 3 new = 35).

- [ ] **Step 4: Commit**

```bash
git add tests/test_liveness.py
git commit -m "test(liveness): prove ModelServerDown on a malformed response, not just silence"
```

---

## Plan Self-Review Notes

- **Spec coverage:** interface (exception + function signature) — Task 1.
  `urllib`-based GET with 2s timeout — Task 1. Alive case — Task 1. Two
  distinct down-modes, deliberately not one — Tasks 2 and 3. Non-vacuity
  rationale — stated in Task 3's purpose. Out-of-scope items (retry,
  model-name check, runner wiring) — none implemented, per Global
  Constraints; nothing in this plan touches them.
- **Type consistency:** `check_model_server_alive(base_url: str =
  "http://127.0.0.1:8001") -> None` and `ModelServerDown` are identical
  across Tasks 1–3; no drift. Fixed during review: the default was
  originally `localhost:1234` (LM Studio's port, from a different branch);
  `BRIEF.md` records this environment's server as `omlx` on
  `127.0.0.1:8001`, so both spec and plan now use that.
- **No placeholders:** every step shows complete, runnable code and an
  exact command with an expected result.

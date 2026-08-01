# Cycle 14 — Live-server suite execution

**Phase:** 1 — Reproduce AgentClinic Phase 1 with a trustworthy engine
**Status:** design, awaiting plan

## Why this cycle

The acceptance suite currently does `from app import app` and drives the
model's application through `starlette.testclient.TestClient`. Two
problems follow from that single line, and the fidelity one is the reason
this cycle exists.

**Fidelity.** `TestClient` is not how the app runs. It bypasses the real
ASGI server, lifespan events, and HTTP serialization. A solution that
passes under `TestClient` but fails under uvicorn is a solution that does
not actually work — and Phase 1's entire purpose is producing a number
worth trusting. Grading against a live server is grading against reality.

**Isolation, as a consequence.** Because the suite imports `app`,
model-authored code executes *inside the pytest process*, alongside
`harness/grading_plugin.py`. That is the root cause behind the Backlog's
forged-results-file entry. This cycle removes model code from the pytest
process entirely; **cycle 15 closes the remaining forgery channel**, which
this cycle deliberately does not (see "What this cycle is not").

## What this cycle is not

- **Not the security fix.** Cycle 14's brainstorm established
  empirically that running the app in a separate process does *not* by
  itself close the forged-results-file gap: the app subprocess globs
  `$TMPDIR/satyrn-grade-results-*.txt` and forges a passing verdict,
  because it runs as the same UID that owns the `0600` file. A broken
  solution graded as `accepted` in that demonstration. Cycle 15 fixes
  this by holding the results file's fd and unlinking its path. Cycle 14
  is honest about shipping with the gap still open — it narrows the
  attack surface without closing it.
- **Not the n=16 re-baseline.** Changing the suite changes the conditions
  the trusted number was produced under, so the reproduction claim needs
  re-establishing. This cycle proves the mechanism with one live run, the
  way cycle 8 did. Re-running the full batch is deferred until after
  cycle 15, because cycle 15 changes the same code path and running n=16
  twice would waste sixteen model runs to answer the same question once.
- Not a change to what the acceptance suite *asserts*. Every assertion
  keeps its current meaning; only the transport changes.

## Architecture

One new module, `harness/app_server.py`, owns launching and tearing down
the model's app as a real uvicorn subprocess. `grade()` gains one phase.

The single grading directory splits in two, with **zero overlap**:

| Directory | Contains | Process that uses it |
|---|---|---|
| `app_dir` | allowlisted model files only (`app.py`, `templates`) | the uvicorn subprocess |
| `suite_dir` | the acceptance suite only | the pytest subprocess |

This is the cycle's main structural win. With the suite talking HTTP, the
pytest process needs nothing model-written at all, so it becomes
**model-free by construction** rather than by a list of things we
remembered to exclude. It also closes a vector nobody had named: today
`app.py` could read `test_acceptance.py` at import time and craft
responses against the contract literals it finds there. After this cycle
the app never sees the test file.

## Interface

```python
# harness/app_server.py

class AppServerFailed(Exception):
    """Raised when the app subprocess never becomes ready."""


@dataclass
class AppServer:
    base_url: str
    output: str = ""   # populated on teardown


@contextmanager
def serve_app(app_dir: Path, timeout: float = 15.0) -> Iterator[AppServer]:
    ...
```

- Launches `python -m uvicorn app:app --host 127.0.0.1 --port <port>`
  with `cwd=app_dir`. uvicorn puts `cwd` on `sys.path`, which is how
  `app.py` is found, and `Jinja2Templates(directory="templates")`
  resolves relative to the same `cwd` — verified working for the
  `reference` fixture.
- Port: bound-then-closed to find a free one, then passed explicitly.
  This carries the same benign TOCTOU race as `_free_port` in
  `tests/test_liveness.py`; accepted on the same grounds.
- Readiness: poll TCP connect until the port accepts, or the process
  exits, or `timeout` elapses. Exiting early or timing out raises
  `AppServerFailed` carrying the captured output.
- Teardown is guaranteed by the context manager: `terminate()`, wait,
  then `kill()` if it does not stop. A hung app must never leak past the
  grading call.

`GradeResult` gains one field, `app_output: str`. This is cycle 8's
lesson applied before it bites: when the `pi` invocation's output was
discarded, a broken flag set looked like a model failure for far longer
than it should have. If the app crashes on a request, uvicorn's traceback
is the first thing anyone will want.

## Behavior

`grade()`'s sequence becomes:

1. `_test_count(suite)` — unchanged.
2. `_refused_config(workspace)` — unchanged, still against the original
   workspace, still first. Its diagnostic value in `refused_config`
   survives even though the allowlist already keeps those files out.
3. Build `app_dir`: copy each existing `source_allowlist` path from the
   workspace. Missing paths are skipped, not an error — `broken` has no
   `templates/`.
4. Build `suite_dir`: copy the acceptance suite, and nothing else.
5. `serve_app(app_dir)`. If it raises `AppServerFailed`, return a
   rejection — `accepted=False`, `tests_executed=0`, `returncode=None`,
   `app_output` carrying uvicorn's output. An app that will not start
   cannot pass the suite; that is a model failure and grades as one,
   rather than crashing the run.
6. Run pytest with `cwd=suite_dir`, passing `SATYRN_APP_BASE_URL` in the
   environment alongside the existing results-path and `PYTHONPATH`
   variables. Everything else about the invocation is unchanged: same
   `-p harness.grading_plugin`, same suite-filename argument.
7. Verdict from the results file, as today, plus `app_output` from the
   torn-down server.

Both temporary directories are removed in a `finally`, as the single
grading directory is today.

## Suite rewrite

`examples/agentclinic/phase-1/acceptance/test_acceptance.py` changes its
first four lines and nothing else:

```python
import os
import httpx
from turbohtml import Doctype, parse

client = httpx.Client(base_url=os.environ["SATYRN_APP_BASE_URL"])
```

Every `client.get("/")` call and every assertion body stays byte-identical
— `httpx.Client(base_url=...)` and `TestClient` share the same request
API, which is why this is a four-line diff rather than a rewrite.

`httpx` becomes a declared dependency in `pyproject.toml`. It is already
installed as a transitive dependency of `fastapi[standard]` (via
`TestClient`), but the suite now imports it directly, and a direct import
deserves a direct declaration.

Reading `SATYRN_APP_BASE_URL` at module scope means the suite raises
`KeyError` if collected outside `grade()`. That is correct — it has no
meaning without a server — and `norecursedirs` in `pyproject.toml`
already keeps the harness's own pytest run from collecting it.

## Two tests get removed

`tests/test_workspace.py::test_prepare_workspace_accepts_the_reference_solution`
and `::test_prepare_workspace_rejects_the_broken_solution` copy the suite
into a workspace and run plain pytest, bypassing `grade()` and relying on
`TestClient` working with no server. They cannot survive this change.

They are removed rather than repaired, because their claim — reference
accepted, broken rejected — is already proven by
`tests/test_grading.py::test_grade_accepts_the_reference_solution` and
`::test_grade_rejects_the_broken_solution`, through the path that
actually matters. Repairing them would mean duplicating the
server-launching machinery outside `harness/` to re-prove something
already proven. This follows cycle 9's precedent for removing a test its
own change made vacuous.

## Testing

- **`serve_app` in isolation**, hermetically: it serves the `reference`
  fixture and returns 200 with the tagline, and serves the `broken`
  fixture and returns 404 — both confirmed against real uvicorn
  subprocesses during brainstorming, including that `broken`'s missing
  `templates/` does not prevent startup. It must also raise
  `AppServerFailed` for an `app.py` that cannot import (a deliberate
  syntax error), carrying output that names the failure; that third case
  was *not* exercised during brainstorming and is a genuine unknown for
  the implementer to prove, not a restatement of something already
  demonstrated.
- **Teardown is real**: after the context manager exits, the port no
  longer accepts connections. Without this, a leaked server could make a
  later run pass against a stale app — the kind of false pass this whole
  phase exists to prevent.
- **`grade()` end to end**: the existing reference/broken/model-written-
  tests/shadowing tests all keep passing unchanged. That they pass
  through an entirely new transport without edits is the strongest
  available evidence the change preserves meaning.
- **One live run** of `run_agentclinic_phase1()` against the real `omlx`
  server, confirming a real model solution still grades `accepted=True`
  with `tests_executed == tests_expected == 4`.

## Non-goals recap

The forged-results-file fix (cycle 15), the n=16 re-baseline (deferred
until after cycle 15), and any change to what the suite asserts are all
explicitly out of scope, per the discussion above.

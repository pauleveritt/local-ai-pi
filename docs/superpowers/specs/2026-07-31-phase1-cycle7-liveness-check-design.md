# Cycle 7 — Model-server liveness check

**Phase:** 1 — Reproduce AgentClinic Phase 1 with a trustworthy engine
**Status:** implemented — cycle marked Done in `ROADMAP.md`

## Why this cycle

Cycle 8 is the first cycle that invokes `pi` against a real model. Per
`BRIEF.md`, the model is served locally by `omlx` on `127.0.0.1:8001`. If
that server is not running when `pi` is invoked, the
failure that comes back — a hang, a connection error surfacing through `pi`,
or a garbled response — has no obvious relationship to "the server is down."
It would look like a model problem, or an engine problem, and cycles 1–6
exist precisely so that kind of confusion can't happen at the grading layer.
This cycle closes the matching gap one layer earlier: before `pi` runs at
all.

This is the last piece of judging apparatus built before cycle 8. Like
cycles 3–6, it is provable with no model in the loop.

## What this cycle is not

- Not a retry/backoff policy. No evidence yet that the server flaps in the
  seconds around a run starting. If cycle 8 turns up real flakiness, that's
  a concrete Backlog candidate then — not a guess encoded now.
- Not a check of *which* model is loaded. Liveness means "the server is up
  and answering," full stop. Which model it's serving is a different
  question from whether anything is listening.
- Not wired into cycle 8's runner. This cycle builds and proves the check in
  isolation; calling it from the first real run is cycle 8's job.

## Interface

```python
# harness/liveness.py

class ModelServerDown(Exception):
    """Raised when the model server does not respond at the expected endpoint."""

def check_model_server_alive(base_url: str = "http://127.0.0.1:8001") -> None:
    ...
```

- `base_url` is a parameter with a `127.0.0.1:8001` default — matching
  `BRIEF.md`'s recorded `omlx` server address — as a seam, not a hardcode,
  per `BRIEF.md`'s stated principle. Nothing calls it with a different
  value today; the parameter exists so nothing has to change if that ever
  stops being true.
- Returns `None` on success. Raises `ModelServerDown` on any failure to
  confirm liveness. There is no third outcome — this is a precondition
  check, not a graded result. A stopped server is an environment failure,
  not a verdict, so it never enters the `GradeResult` shape cycle 3–6 built.

## Behavior

1. `GET {base_url}/v1/models` via `urllib.request` (stdlib — no new
   dependency), with a short timeout (2 seconds: long enough to absorb
   normal latency, short enough that a hung check doesn't itself stall a
   run).
2. A response with HTTP status 200 and a parseable JSON body: liveness
   confirmed, function returns.
3. Anything else — connection refused, timeout, a non-2xx status (which
   `urlopen` itself raises `HTTPError` for), a body that isn't parseable
   JSON — raises `ModelServerDown`, chaining the underlying exception
   (`raise ModelServerDown(...) from original`) so the real cause is never
   lost, but every caller only ever needs to catch the one type.

## Testing

No real network calls. This needs to be provable without a real model
server running, the same discipline cycles 1–6 used for grading: a fixture
stands in for the real thing, and the test proves the check's actual
behavior against it.

- **Alive case:** a minimal local HTTP server (stdlib `http.server`, bound
  to an ephemeral port) that answers `GET /v1/models` with 200 and a small
  JSON body. `check_model_server_alive` against it returns `None`.
- **Down case, nothing listening:** point the check at a port nothing is
  bound to. Raises `ModelServerDown`.
- **Down case, wrong shape:** a minimal local HTTP server that answers with
  a non-200 status (e.g. 500). Raises `ModelServerDown`.

Two distinct down-modes, not one, on purpose: this is this cycle's
non-vacuity check. A single "nothing listening" test proves the check
reacts to *something*, but it can't distinguish a real check from one that
swallows any non-200 response and returns `None` anyway — that mistake
would still fail the "nothing listening" case correctly, since that case
never gets far enough to reach such a bug. Testing a second down-mode that
completes a real HTTP exchange, gets back an actual (bad) response, and is
still classified as down — rules that out.

## Non-goals recap

Retry policy, model-name verification, and runner wiring are explicitly
deferred, per the design discussion above and the "What this cycle is not"
section. If any surfaces again during cycle 8, it goes to the Backlog with
the evidence that raised it — the same pattern cycles 4's and 5's
deferrals followed.

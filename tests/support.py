"""Shared construction for `RunConditions` in tests.

Every field added to `RunConditions` otherwise means editing every
positional construction in the suite. Phase 5 cycle 1 added four at once
and found seventeen sites; this exists so the next addition edits one
place. Tests that care about a field pass it explicitly, which also makes
each test say which condition it is actually about.

Deliberately not a `conftest.py`. The repo root already has one, empty, so
that `import harness` resolves during collection; pytest puts both the repo
root and `tests/` on `sys.path`, so a second module named `conftest` would
be an ambiguous import. `make_conditions` is a plain helper rather than a
fixture, so it has no reason to live in a conftest anyway.

Built with `dataclasses.replace` over a real instance rather than by
unpacking a `dict` of defaults: a `dict` widens every value to a union, and
the type checker then rejects all twelve keyword arguments at once.
"""

import dataclasses

from harness.runner import RunConditions

PRE_PHASE5 = "<pre-phase5>"

_DEFAULTS = RunConditions(
    model="model",
    pi_command=("pi",),
    pi_version="0.83.0",
    task_spec_sha256="task-spec-sha",
    harness_revision="rev",
    run_timeout=600,
    grade_timeout=30,
    extension_digests=("digest",),
    improvement_name="none",
    improvement_digest="<none>",
    acceptance_sha256="acceptance-sha",
    source_allowlist=("app.py",),
    agent_dir_digest="agent-dir-digest",
)


def make_conditions(**overrides) -> RunConditions:
    return dataclasses.replace(_DEFAULTS, **overrides)

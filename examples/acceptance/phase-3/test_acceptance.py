"""Acceptance contract — Phase 3 (Add Complaint). Harness-owned.

Cumulative scope: Phases 1, 2 AND 3.

Contract source: examples/agentclinic/specs/roadmap.md, "## Phase 3 — Add Complaint".

STATUS: SKELETON — needs authoring. See the checklist below, then delete
test_suite_is_authored.

NOTE — the known semantic trap (lessons.md #13): TestClient follows redirects
by default, so a test for the 303 MUST pass follow_redirects=False or it will
silently assert against the followed page and pass for the wrong reason. This
suite is the one place that trap must not be fallen into, since it is what
grades everyone else.
"""
from starlette.testclient import TestClient

from app import app

client = TestClient(app)

TAGLINE = "Come in. Sit down. Tell us about your human."
SEED_COMPLAINT = "Scope creep never ends."


# ---------------------------------------------------------------------------
# Phases 1-2 carried forward — preservation checks. Do not delete.
# ---------------------------------------------------------------------------

def test_home_still_returns_200_and_tagline():
    response = client.get("/")
    assert response.status_code == 200
    assert TAGLINE in response.text


def test_complaints_board_still_lists_seed_complaint():
    response = client.get("/complaints")
    assert response.status_code == 200
    assert SEED_COMPLAINT in response.text


# ---------------------------------------------------------------------------
# Phase 3 contract — TO AUTHOR
#
#   [ ] POST /complaints with form fields agent_name and text returns 303
#       *** use follow_redirects=False — see the module docstring ***
#   [ ] The 303 response carries Location: /complaints
#   [ ] After a POST, GET /complaints includes the newly added complaint
#       (post a distinctive string and assert it renders)
#   [ ] The complaints page serves a form that POSTs to /complaints, with an
#       agent-name input, a text textarea, and a submit control
#       (assert on rendered output; do not assert on template internals)
#
# Judgment calls worth making deliberately:
#   - Whether to assert the form's exact field *names* (agent_name, text).
#     The POST test already pins them functionally; asserting the HTML too is
#     belt-and-suspenders but risks failing a solution that uses a different
#     input ordering or markup shape.
#   - Test isolation: appending to a module-level list mutates state across
#     tests in the same session. Decide whether to assert on a unique
#     per-test string (simplest) or to snapshot/restore the list.
# ---------------------------------------------------------------------------


def test_suite_is_authored():
    """Guard: fails until the Phase 3 contract above is actually asserted.
    Delete once authored. See phase-2's guard for why this exists."""
    raise AssertionError(
        "Phase 3 acceptance suite is a skeleton — author the contract checks "
        "above, then delete this guard."
    )

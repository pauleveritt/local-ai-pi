"""Acceptance contract — Phase 2 (Complaints Board). Harness-owned.

Cumulative scope: Phases 1 AND 2. The Phase 1 assertions below are not
redundant — they are how preservation breakage is detected. A run that builds
the complaints board while erasing the home page must FAIL here.

Contract source: examples/agentclinic/specs/roadmap.md, "## Phase 2 — Complaints Board".

STATUS: SKELETON — needs authoring. See the checklist below, then delete
test_suite_is_authored.
"""
from starlette.testclient import TestClient

from app import app

client = TestClient(app)

TAGLINE = "Come in. Sit down. Tell us about your human."
SEED_COMPLAINT = "Scope creep never ends."


# ---------------------------------------------------------------------------
# Phase 1 carried forward — preservation checks. Do not delete these.
# ---------------------------------------------------------------------------

def test_home_still_returns_200_and_tagline():
    response = client.get("/")
    assert response.status_code == 200
    assert TAGLINE in response.text


def test_home_still_extends_the_shared_layout():
    body = client.get("/").text
    assert "AgentClinic" in body
    assert 'href="/"' in body
    assert 'href="/complaints"' in body


# ---------------------------------------------------------------------------
# Phase 2 contract — TO AUTHOR
#
# The roadmap requires, and this suite should assert:
#
#   [ ] GET /complaints returns 200
#   [ ] The seeded complaint literal "Scope creep never ends." appears
#   [ ] Each complaint renders its agent name, its text, and a formatted
#       timestamp (assert on rendered output, not on the template file)
#   [ ] The page carries the heading "Complaints Board"
#   [ ] The complaints page extends base.html (navbar present, as above)
#   [ ] models.Complaint exists with fields agent_name, text, timestamp
#   [ ] Complaint.timestamp defaults per-instance and is UTC-aware
#       (construct two and assert the timestamps are independent and
#       tz-aware — this is the field(default_factory=...) requirement, and a
#       shared mutable default is a real failure mode worth catching)
#   [ ] models.complaints is a module-level list with 3-5 seed entries
#
# Judgment calls worth making deliberately:
#   - How strictly to assert timestamp *format*. The roadmap says "formatted"
#     without specifying. Over-asserting here fails correct solutions.
#   - Whether to require the exact heading string or accept a case variant.
# ---------------------------------------------------------------------------


def test_suite_is_authored():
    """Guard: fails until the Phase 2 contract above is actually asserted.

    Without this, an unfinished suite would collect only the preservation
    checks and grade every run as passing Phase 2 — a vacuous oracle, the
    exact failure Amendment 3 exists to prevent. Delete once authored."""
    raise AssertionError(
        "Phase 2 acceptance suite is a skeleton — author the contract checks "
        "above, then delete this guard."
    )

"""Acceptance contract — Phase 1 (Home Page). Harness-owned; the model cannot edit this.

Cumulative scope: Phase 1 only.

Contract source: examples/agentclinic/specs/roadmap.md, "## Phase 1 — Home Page".
Assert user-visible behavior and exact literals. Do not assert on internal
function names or file layout — a correct-but-different solution must pass.
"""
from starlette.testclient import TestClient

from app import app

client = TestClient(app)

TAGLINE = "Come in. Sit down. Tell us about your human."


def test_home_returns_200():
    assert client.get("/").status_code == 200


def test_home_shows_the_tagline_verbatim():
    """The roadmap names this string exactly; it is a contract literal."""
    assert TAGLINE in client.get("/").text


def test_home_extends_the_shared_layout():
    """base.html supplies the navbar; home.html must extend it rather than
    duplicate a standalone page. Asserted through rendered output (the navbar
    brand and both nav links), not by inspecting template source."""
    body = client.get("/").text
    assert "AgentClinic" in body
    assert 'href="/"' in body
    assert 'href="/complaints"' in body


def test_home_declares_html5_and_language():
    body = client.get("/").text
    assert "<!DOCTYPE html>" in body or "<!doctype html>" in body
    assert 'lang="en"' in body

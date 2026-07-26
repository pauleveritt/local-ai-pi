"""Acceptance contract — Phase 1 (Home Page). Harness-owned; the model cannot edit this.

Cumulative scope: Phase 1 only.

Contract source: examples/agentclinic/specs/roadmap.md, "## Phase 1 — Home Page".
Assert user-visible behavior and exact literals. Do not assert on internal
function names or file layout — a correct-but-different solution must pass.
"""
from starlette.testclient import TestClient
from turbohtml import Doctype, parse

from app import app

client = TestClient(app)

TAGLINE = "Come in. Sit down. Tell us about your human."


def _normalized_text(element) -> str:
    return " ".join(element.text.split())


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
    document = parse(body)

    assert "AgentClinic" in body
    assert any(
        link.attr("href") == "/" and _normalized_text(link).casefold() == "home"
        for link in document.select("a")
    )
    assert any(
        link.attr("href") == "/complaints"
        and _normalized_text(link).casefold() == "complaints"
        for link in document.select("a")
    )


def test_home_declares_html5_and_language():
    document = parse(client.get("/").text)

    assert any(
        isinstance(node, Doctype) and node.name.casefold() == "html"
        for node in document.children
    )
    html = document.select_one("html")
    assert html is not None and html.attr("lang").casefold() == "en"

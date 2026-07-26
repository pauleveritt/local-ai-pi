"""Acceptance contract — Phase 2 (Complaints Board). Harness-owned.

Cumulative scope: Phases 1 AND 2. The Phase 1 assertions below are not
redundant — they are how preservation breakage is detected. A run that builds
the complaints board while erasing the home page must FAIL here.

Contract source: examples/agentclinic/specs/roadmap.md, "## Phase 2 — Complaints Board".
"""

from dataclasses import fields, MISSING

from starlette.testclient import TestClient
from turbohtml import Doctype, parse

from app import app
import models
from models import Complaint

client = TestClient(app)

TAGLINE = "Come in. Sit down. Tell us about your human."
SEED_COMPLAINT = "Scope creep never ends."


def _normalized_text(element) -> str:
    return " ".join(element.text.split())


def _has_html5_doctype(document) -> bool:
    return any(
        isinstance(node, Doctype) and node.name.casefold() == "html"
        for node in document.children
    )


# ---------------------------------------------------------------------------
# Phase 1 carried forward — preservation checks. Do not delete these.
# ---------------------------------------------------------------------------

def test_home_still_returns_200_and_tagline():
    response = client.get("/")
    assert response.status_code == 200
    assert TAGLINE in response.text


def test_home_has_html5_doctype():
    document = parse(client.get("/").text)

    assert _has_html5_doctype(document)


def test_home_html_element_declares_english_language():
    document = parse(client.get("/").text)
    html = document.select_one("html")

    assert html is not None and html.attr("lang").casefold() == "en"


def test_home_still_extends_the_shared_layout():
    body = client.get("/").text
    assert "AgentClinic" in body
    assert 'href="/"' in body
    assert 'href="/complaints"' in body

def test_complaints_exists():
    assert client.get("/complaints").status_code == 200

def test_complaint_literal_seed():
    # We have the SEED_COMPLAINT above, make sure it is in the page
    assert SEED_COMPLAINT in client.get("/complaints").text


def test_complaints_board_preserves_shared_layout():
    document = parse(client.get("/complaints").text)
    html = document.select_one("html")

    assert _has_html5_doctype(document)
    assert html is not None and html.attr("lang").casefold() == "en"


def test_each_complaint_renders_its_details_and_formatted_timestamp():
    document = parse(client.get("/complaints").text)
    cards = [_normalized_text(card) for card in document.select(".card")]
    assert len(cards) >= len(models.complaints)

    for complaint in models.complaints:
        matching_cards = [
            text
            for text in cards
            if complaint.agent_name in text and complaint.text in text
        ]
        assert matching_cards, (
            f"Complaint details not rendered for {complaint.agent_name!r}"
        )

        month_tokens = {
            str(complaint.timestamp.month),
            f"{complaint.timestamp.month:02d}",
            complaint.timestamp.strftime("%B"),
            complaint.timestamp.strftime("%b"),
        }
        day_tokens = {str(complaint.timestamp.day), f"{complaint.timestamp.day:02d}"}
        assert any(
            str(complaint.timestamp.year) in text
            and any(token in text for token in month_tokens)
            and any(token in text for token in day_tokens)
            for text in matching_cards
        ), f"Formatted timestamp not rendered for {complaint.agent_name!r}"

def test_complaint_page_heading():
    document = parse(client.get("/complaints").text)

    assert any(
        _normalized_text(element).casefold() == "complaints board"
        for element in document.select("*")
    )

def test_navbar_exists():
    body = client.get("/complaints").text
    assert "AgentClinic" in body
    assert "Home" in body
    assert "Complaints" in body

def test_complaint_model_structure():
    field_map = {f.name: f for f in fields(Complaint)}
    assert "agent_name" in field_map
    assert "text" in field_map
    assert "timestamp" in field_map
    # Has a default?
    f = field_map["timestamp"]
    assert f.default_factory is not MISSING, "timestamp must use default_factory"


def test_complaint_different_timestamps():
    # Does a new Complaint have a timestamp?
    complaint1 = Complaint("agent1", "some text")
    complaint2 = Complaint("agent1", "other text")
    assert complaint1.timestamp is not complaint2.timestamp

def test_complaint_timestamp_has_timezone():
    complaint1 = Complaint("agent1", "some text")
    dt = complaint1.timestamp
    assert dt.tzinfo is not None and dt.tzinfo.utcoffset(dt) is not None

def test_complaint_default_can_mutate():
    # Did it set a mutable default?
    complaint1 = Complaint("agent1", "some text")
    complaint2 = Complaint("agent1", "other text")
    # Rely on identity check
    assert getattr(complaint1, "timestamp") is not getattr(complaint2, "timestamp")

def test_complain_module_level_collection():
    # Not sure I like testing this, but it's in the spec
    assert hasattr(models, "complaints")
    complaints = getattr(models, "complaints")
    assert isinstance(complaints, list)
    assert 3 <= len(complaints) <= 5

# ---------------------------------------------------------------------------
# Carried-forward obligations — open, from the non-vacuity gate
#
# The gate (tests/test_oracle.py) applies each break below to a solution that
# violates ONLY that roadmap bullet, leaving every other phase intact. This
# suite must FAIL each one. What to assert, and how strictly, is open — the
# obligation is only that the violation is caught.
#
#   [X] p1-doctype  — "HTML5 doctype and `<html lang="en">`"
#   [X] p1-lang     — "HTML5 doctype and `<html lang="en">`"
#
# Check both directions:
#   uv run pytest tests/test_oracle.py -k "doctype or lang or accepts_reference"
# ---------------------------------------------------------------------------

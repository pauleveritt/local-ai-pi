"""Regression: the phase-3 model-facing spec must state the behavioral
contract without leaking the answer to its own known traps.

Motivated by docs/superpowers/specs/2026-07-27-next-phase-decision-design.md
(Decision 1) and lessons.md #13 (the follow_redirects trap). The acceptance
suite (examples/acceptance/phase-3/test_acceptance.py) requires exactly
response.status_code == 303 on POST /complaints -- that numeric requirement
must stay in the spec. What must NOT stay: the FastAPI class name that
implements it, and the test-authoring instruction that tells the model
exactly how its own tests must observe the redirect.
"""
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ROADMAP = REPO_ROOT / "examples" / "agentclinic" / "specs" / "roadmap.md"


def _phase_section(phase: int) -> str:
    text = ROADMAP.read_text()
    lines = text.splitlines()
    pattern_start = f"## Phase {phase} "
    pattern_next = f"## Phase {phase + 1} "
    start = None
    for i, line in enumerate(lines):
        if line.startswith(pattern_start) and start is None:
            start = i
        elif start is not None and line.startswith(pattern_next):
            return "\n".join(lines[start:i])
    if start is not None:
        return "\n".join(lines[start:])
    raise ValueError(f"Phase {phase} not found in roadmap")


def test_phase3_spec_does_not_name_the_redirect_implementation():
    section = _phase_section(3)
    assert "RedirectResponse" not in section, (
        "Phase 3 spec names the FastAPI redirect class directly -- this "
        "hands the model the implementation, not just the contract"
    )


def test_phase3_spec_does_not_leak_the_test_technique():
    section = _phase_section(3)
    assert "follow_redirects" not in section, (
        "Phase 3 spec tells the model exactly how its own tests must "
        "observe the redirect -- this is the follow_redirects trap "
        "(lessons.md #13) stated as an instruction instead of left for "
        "the model to discover"
    )


def test_phase3_spec_still_states_the_303_behavioral_contract():
    section = _phase_section(3)
    assert "303" in section, (
        "removing the implementation hint must not also remove the actual "
        "behavioral requirement the acceptance suite grades -- see design "
        "doc Decision 1 rationale 2"
    )

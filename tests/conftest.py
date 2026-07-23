# tests/conftest.py
import shutil
from pathlib import Path

import pytest

from harness.session import InvocationProfile


@pytest.fixture
def pi_binary() -> str:
    path = shutil.which("pi")
    if not path:
        pytest.skip("pi not on PATH")
    return path


@pytest.fixture
def model() -> str:
    return "omlx/gemma-4-12B-it-MLX-8bit"


@pytest.fixture
def app_source() -> Path:
    return Path(__file__).resolve().parent.parent / "examples" / "agentclinic"


@pytest.fixture
def sample_session_path() -> Path:
    return Path(__file__).resolve().parent / "fixtures" / "sample-session.jsonl"


def _extract_phase(roadmap_text: str, phase_number: int) -> str:
    """Extract the verbatim text of a phase section from the roadmap."""
    lines = roadmap_text.splitlines()
    marker = f"## Phase {phase_number} "
    start = None
    for i, line in enumerate(lines):
        if line.startswith(marker):
            start = i
            break
    if start is None:
        raise ValueError(f"Phase {phase_number} not found in roadmap")
    body: list[str] = []
    for line in lines[start + 1 :]:
        if line.startswith("## Phase "):
            break
        body.append(line)
    return "\n".join(body).strip()


@pytest.fixture
def phase1_prompt() -> str:
    roadmap = Path(__file__).resolve().parent.parent / "examples" / "agentclinic" / "specs" / "roadmap.md"
    return _extract_phase(roadmap.read_text(), 1)


@pytest.fixture
def phase2_prompt() -> str:
    roadmap = Path(__file__).resolve().parent.parent / "examples" / "agentclinic" / "specs" / "roadmap.md"
    return _extract_phase(roadmap.read_text(), 2)


@pytest.fixture
def phase3_prompt() -> str:
    roadmap = Path(__file__).resolve().parent.parent / "examples" / "agentclinic" / "specs" / "roadmap.md"
    return _extract_phase(roadmap.read_text(), 3)


@pytest.fixture
def sp1_profile() -> InvocationProfile:
    return InvocationProfile.sp1()


@pytest.fixture
def sp2_profile() -> InvocationProfile:
    subagent_path_file = Path(__file__).resolve().parent.parent / ".pi" / "subagent-extension-path.txt"
    if subagent_path_file.exists():
        path = subagent_path_file.read_text().strip()
    else:
        path = ""
    return InvocationProfile.sp2(path)

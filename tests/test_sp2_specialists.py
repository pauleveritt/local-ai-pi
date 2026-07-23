# tests/test_sp2_specialists.py
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """Parse YAML-like frontmatter from a markdown file.
    The shipped 'agents.ts' parseFrontmatter handles this server-side;
    we validate the frontmatter shape here."""
    if not text.startswith("---"):
        raise ValueError("Missing frontmatter delimiter")
    parts = text.split("---", 2)
    if len(parts) < 3:
        raise ValueError("Missing closing frontmatter delimiter")
    frontmatter = {}
    for line in parts[1].strip().split("\n"):
        line = line.strip()
        if ":" in line:
            key, _, value = line.partition(":")
            frontmatter[key.strip()] = value.strip()
    return frontmatter, parts[2].strip()


def test_implementer_md_exists():
    path = REPO_ROOT / ".pi" / "agents" / "implementer.md"
    assert path.exists(), f"{path} not found"


def test_implementer_md_has_valid_frontmatter():
    path = REPO_ROOT / ".pi" / "agents" / "implementer.md"
    text = path.read_text()
    fm, body = _parse_frontmatter(text)
    assert fm.get("name") == "implementer", "frontmatter must have name: implementer"
    assert "description" in fm, "frontmatter must have description"
    assert "tools" in fm, "frontmatter must have tools"
    tools = [t.strip() for t in fm["tools"].split(",")]
    assert "read" in tools
    assert "write" in tools
    assert "bash" in tools
    assert fm.get("model") == "omlx/gemma-4-12B-it-MLX-8bit"


def test_implementer_md_has_system_prompt_body():
    path = REPO_ROOT / ".pi" / "agents" / "implementer.md"
    text = path.read_text()
    fm, body = _parse_frontmatter(text)
    assert len(body) > 100, "system prompt body should be substantial"
    assert "implementer" in body.lower()
    assert "packet" in body.lower()

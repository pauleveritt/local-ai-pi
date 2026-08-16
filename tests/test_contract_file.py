"""harness/contract_file.py: a markdown contract file -> HandoffContract.

Deterministic, no model calls. The file is what an agent writes in-session;
the TypedDict is the wire format implementer.ts already validates.
"""

import pytest

from harness.contract_file import ContractFileError, parse_contract_file

MINIMAL = """\
---
writableFiles: [src/svcs/_core.py]
validation: pytest -q
---
# Enter async context managers

Append `(name, svc)` to `self._on_close`, rebind `svc`.
"""


def _write(tmp_path, text, name="contract.md"):
    path = tmp_path / name
    path.write_text(text)
    return path


def test_body_becomes_the_task_and_front_matter_is_stripped(tmp_path):
    contract = parse_contract_file(_write(tmp_path, MINIMAL))
    assert contract["task"].startswith("# Enter async context managers")
    assert "writableFiles" not in contract["task"]


def test_writable_files_become_the_wire_format_dicts(tmp_path):
    contract = parse_contract_file(_write(tmp_path, MINIMAL))
    assert contract["writableFiles"] == [{"path": "src/svcs/_core.py"}]


def test_optional_lists_default_to_empty_so_the_child_accepts_the_shape(tmp_path):
    contract = parse_contract_file(_write(tmp_path, MINIMAL))
    assert contract["readableFiles"] == []
    assert contract["acceptanceStrings"] == []
    assert contract["preservedBehavior"] == []
    assert contract["knownFacts"] == []


def test_optional_fields_are_carried_through_when_present(tmp_path):
    text = """\
---
writableFiles: [src/svcs/_core.py]
readableFiles: [src/svcs/**, tests/**]
validation: pytest -q
knownFacts:
  - The app is ASGI, not WSGI.
acceptanceStrings:
  - aget returns the entered value
---
Body.
"""
    contract = parse_contract_file(_write(tmp_path, text))
    assert contract["readableFiles"] == ["src/svcs/**", "tests/**"]
    assert contract["knownFacts"] == ["The app is ASGI, not WSGI."]
    assert contract["acceptanceStrings"] == ["aget returns the entered value"]


def test_missing_file_is_a_contract_file_error(tmp_path):
    with pytest.raises(ContractFileError, match="no contract file"):
        parse_contract_file(tmp_path / "absent.md")


def test_missing_front_matter_names_the_delimiter(tmp_path):
    with pytest.raises(ContractFileError, match="front-matter"):
        parse_contract_file(_write(tmp_path, "# Just a body\n"))


def test_unparseable_yaml_is_reported_as_such(tmp_path):
    text = "---\nwritableFiles: [unclosed\n---\nBody.\n"
    with pytest.raises(ContractFileError, match="front-matter is not valid YAML"):
        parse_contract_file(_write(tmp_path, text))


def test_writable_files_is_required(tmp_path):
    text = "---\nvalidation: pytest -q\n---\nBody.\n"
    with pytest.raises(ContractFileError, match="writableFiles"):
        parse_contract_file(_write(tmp_path, text))


def test_empty_writable_files_is_refused_not_silently_accepted(tmp_path):
    text = "---\nwritableFiles: []\nvalidation: pytest -q\n---\nBody.\n"
    with pytest.raises(ContractFileError, match="writableFiles"):
        parse_contract_file(_write(tmp_path, text))


def test_validation_is_required(tmp_path):
    text = "---\nwritableFiles: [src/svcs/_core.py]\n---\nBody.\n"
    with pytest.raises(ContractFileError, match="validation"):
        parse_contract_file(_write(tmp_path, text))


def test_an_empty_body_is_refused(tmp_path):
    text = "---\nwritableFiles: [a/b.py]\nvalidation: pytest -q\n---\n\n"
    with pytest.raises(ContractFileError, match="body is empty"):
        parse_contract_file(_write(tmp_path, text))


def test_a_scalar_where_a_list_belongs_names_the_field(tmp_path):
    text = "---\nwritableFiles: src/svcs/_core.py\nvalidation: pytest -q\n---\nBody.\n"
    with pytest.raises(ContractFileError, match="writableFiles"):
        parse_contract_file(_write(tmp_path, text))

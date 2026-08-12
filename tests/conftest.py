"""Fixtures shared across the harness test modules.

`synthetic_clone` lives here rather than in `tests/test_workload.py`
because two modules now need it -- `test_workload.py` and the
`test_qualification.py` split out beside it. Importing a fixture from
another test module works at runtime but makes every consuming test
signature read as a redefinition, so pytest's own mechanism is the right
one.

The plain helpers (`_write_manifest`, `_suite_result`, and friends) stay
in `test_workload.py` and are imported normally; they are functions, not
fixtures, and cross-module imports of those are already the convention
here -- `test_screen.py` does the same.
"""

from tests.test_workload import (
    synthetic_clone,  # noqa: F401 -- re-exported as a fixture
)

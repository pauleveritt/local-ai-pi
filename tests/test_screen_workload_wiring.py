"""`tools/screen_workload.py`'s extension selection.

Narrow on purpose. This exists because the `--probe` arm was silently
broken for a day: commit dc29de6 moved `PROBE_EXTENSION` out of
`harness/screen.py` into `harness/cell_resolution.py` and did not update
this caller, so `screen.PROBE_EXTENSION` raised `AttributeError` on every
probe-budget run. Nothing caught it -- ruff does not resolve attributes,
and pyrefly (which would have) did not cover `tools/` at the time.

An import-time smoke test is not enough: the broken name is read inside
`main()`, so the module imports fine either way.
"""

import tools.screen_workload as screen_workload
from harness.cell_resolution import PROBE_EXTENSION


def test_the_probe_extension_name_this_module_uses_actually_resolves():
    # The specific failure: reading the constant, not importing the module.
    assert PROBE_EXTENSION.name == "probe-cap.ts"
    assert PROBE_EXTENSION.is_file(), "the extension file the probe arm loads must exist"


def test_the_envelope_extension_is_still_read_from_harness_screen():
    # The other half of the same selection line. Kept distinct so a future
    # move of *this* constant fails with its own name rather than being
    # absorbed into the probe assertion.
    assert screen_workload.screen.ENVELOPE_EXTENSION.name == "envelope-cap.ts"
    assert screen_workload.screen.ENVELOPE_EXTENSION.is_file()


def test_both_arms_select_a_different_extension():
    # The selection is the point: if these ever collapse to one path, the
    # --probe flag stops meaning anything and the arms become the same
    # cell under two names.
    assert PROBE_EXTENSION != screen_workload.screen.ENVELOPE_EXTENSION

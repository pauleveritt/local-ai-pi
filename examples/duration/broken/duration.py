"""Known-broken solution for the duration suite. Harness-owned fixture.

One defect: it stops at the first unit, so every multi-unit input is
wrong. `"1h30m"` returns 3600 and `"2h15m30s"` returns 7200. Single-unit
inputs and the unparseable case are handled correctly, so this fixture
proves the grader discriminates on behavior rather than rejecting anything
that merely looks different.
"""
import re

_UNITS = {"h": 3600, "m": 60, "s": 1}
_PATTERN = re.compile(r"(\d+)([hms])")


def parse_duration(text: str) -> int:
    """Return the number of seconds in a duration string like "1h30m"."""
    match = _PATTERN.match(text)
    if match is None:
        raise ValueError(f"cannot parse duration: {text!r}")
    return int(match.group(1)) * _UNITS[match.group(2)]

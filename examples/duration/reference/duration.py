"""Known-good solution for the duration suite. Harness-owned fixture."""
import re

_PATTERN = re.compile(r"(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?")


def parse_duration(text: str) -> int:
    """Return the number of seconds in a duration string like "1h30m"."""
    match = _PATTERN.fullmatch(text)
    if match is None or not any(match.groups()):
        raise ValueError(f"cannot parse duration: {text!r}")
    hours, minutes, seconds = (int(group or 0) for group in match.groups())
    return hours * 3600 + minutes * 60 + seconds

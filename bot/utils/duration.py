"""Parse human durations like "10m", "1h30m", "2 days" or "1w 2d"."""

from __future__ import annotations

import re
from datetime import timedelta

UNITS = {
    "s": 1, "sec": 1, "secs": 1, "second": 1, "seconds": 1,
    "m": 60, "min": 60, "mins": 60, "minute": 60, "minutes": 60,
    "h": 3600, "hr": 3600, "hrs": 3600, "hour": 3600, "hours": 3600,
    "d": 86400, "day": 86400, "days": 86400,
    "w": 604800, "week": 604800, "weeks": 604800,
}  # fmt: skip

_PART = re.compile(r"(\d+(?:\.\d+)?)\s*([a-z]+)")


def parse_duration(text: str) -> timedelta:
    """Return the duration, or raise ValueError with a message fit to show a user."""
    s = text.strip().lower().replace(",", " ").replace(" and ", " ")
    if not s:
        raise ValueError("Give a duration like `10m`, `2h` or `1d 6h`.")
    total = 0.0
    pos = 0
    for m in _PART.finditer(s):
        if s[pos : m.start()].strip():
            break
        unit = UNITS.get(m.group(2))
        if unit is None:
            raise ValueError(f"I don't know the unit `{m.group(2)}`. Use s, m, h, d or w.")
        total += float(m.group(1)) * unit
        pos = m.end()
    if pos == 0 or s[pos:].strip():
        raise ValueError(f"I couldn't read `{text}` as a duration. Try `10m`, `2h` or `1d 6h`.")
    if total <= 0:
        raise ValueError("The duration has to be more than zero.")
    return timedelta(seconds=total)


def humanize(delta: timedelta) -> str:
    seconds = int(delta.total_seconds())
    parts = []
    for name, size in (("week", 604800), ("day", 86400), ("hour", 3600), ("minute", 60), ("second", 1)):
        n, seconds = divmod(seconds, size)
        if n:
            parts.append(f"{n} {name}{'' if n == 1 else 's'}")
    return ", ".join(parts[:2]) or "0 seconds"

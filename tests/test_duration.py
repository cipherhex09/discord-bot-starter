from datetime import timedelta

import pytest

from bot.utils.duration import humanize, parse_duration


@pytest.mark.parametrize(
    "text, seconds",
    [
        ("10m", 600),
        ("1h30m", 5400),
        ("1h 30m", 5400),
        ("2 days", 172800),
        ("1w 2d", 777600),
        ("1.5h", 5400),
        ("1 hour and 5 minutes", 3900),
        ("90s", 90),
    ],
)
def test_parse(text, seconds):
    assert parse_duration(text) == timedelta(seconds=seconds)


@pytest.mark.parametrize("text", ["", "soon", "10", "5x", "10m later", "0m", "m10"])
def test_parse_rejects(text):
    with pytest.raises(ValueError):
        parse_duration(text)


def test_humanize():
    assert humanize(timedelta(seconds=5400)) == "1 hour, 30 minutes"
    assert humanize(timedelta(days=8, hours=3)) == "1 week, 1 day"
    assert humanize(timedelta(0)) == "0 seconds"

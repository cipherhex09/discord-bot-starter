"""Console logging plus a size-capped log file, so a busy bot never fills the disk."""

from __future__ import annotations

import logging
import logging.handlers
from pathlib import Path

FORMAT = "%(asctime)s %(levelname)-7s %(name)s: %(message)s"


def setup_logging(level: str = "INFO", log_dir: Path | None = None) -> None:
    root = logging.getLogger()
    root.setLevel(level)
    for h in list(root.handlers):
        root.removeHandler(h)

    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter(FORMAT, "%H:%M:%S"))
    root.addHandler(console)

    if log_dir is not None:
        log_dir.mkdir(parents=True, exist_ok=True)
        file = logging.handlers.RotatingFileHandler(
            log_dir / "bot.log", maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
        )
        file.setFormatter(logging.Formatter(FORMAT))
        root.addHandler(file)

    # discord.py's gateway chatter is useful when debugging, noise otherwise.
    logging.getLogger("discord").setLevel(max(logging.getLevelName(level), logging.INFO))
    logging.getLogger("discord.http").setLevel(logging.WARNING)

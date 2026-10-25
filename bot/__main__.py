"""Run with `python -m bot`."""

from __future__ import annotations

import asyncio
import contextlib
import logging
import signal
import sys

import discord

from .client import Bot
from .config import Config, ConfigError
from .log import setup_logging


async def main() -> int:
    try:
        config = Config.from_env()
    except ConfigError as e:
        print(f"config error: {e}", file=sys.stderr)
        return 2

    setup_logging(config.log_level, config.log_dir)
    log = logging.getLogger("bot")
    bot = Bot(config)

    # Docker and systemd stop a service with SIGTERM. Close the gateway and the
    # database cleanly instead of dying mid-write.
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        with contextlib.suppress(NotImplementedError):  # Windows has no signal handlers
            loop.add_signal_handler(sig, lambda: asyncio.create_task(bot.close()))

    try:
        async with bot:
            await bot.start(config.token)
    except discord.LoginFailure:
        log.error("Discord rejected the token. Reset it in the developer portal and update DISCORD_TOKEN.")
        return 1
    except discord.PrivilegedIntentsRequired:
        log.error("This bot asks for a privileged intent that is off in the developer portal.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

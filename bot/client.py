from __future__ import annotations

import logging
import time
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands

from .config import Config
from .db import Database
from .errors import handle_app_command_error

log = logging.getLogger(__name__)

COGS_DIR = Path(__file__).parent / "cogs"


def discover_cogs() -> list[str]:
    """Every module in bot/cogs is a cog. Files starting with _ are skipped."""
    return sorted(f"bot.cogs.{p.stem}" for p in COGS_DIR.glob("*.py") if not p.name.startswith("_"))


class Bot(commands.Bot):
    def __init__(self, config: Config):
        # Only the default intents. Members, presences and message content are
        # privileged: turn them on here and in the developer portal only if a
        # feature truly needs them.
        intents = discord.Intents.default()
        super().__init__(
            command_prefix=commands.when_mentioned,
            intents=intents,
            owner_ids=set(config.owner_ids) or None,
            allowed_mentions=discord.AllowedMentions(everyone=False, roles=False, users=True, replied_user=False),
            help_command=None,
        )
        self.config = config
        self.db = Database(config.database_path)
        self.started_at = time.time()
        self.tree.on_error = self._on_tree_error

    async def setup_hook(self) -> None:
        await self.db.connect()
        for ext in discover_cogs():
            await self.load_extension(ext)
            log.info("loaded %s", ext)
        if self.config.sync_commands:
            await self.sync_commands()

    async def sync_commands(self) -> list[app_commands.AppCommand]:
        if self.config.dev_guild_ids:
            synced: list[app_commands.AppCommand] = []
            for gid in self.config.dev_guild_ids:
                guild = discord.Object(id=gid)
                self.tree.copy_global_to(guild=guild)
                synced = await self.tree.sync(guild=guild)
                log.info("synced %d commands to dev guild %s", len(synced), gid)
            return synced
        synced = await self.tree.sync()
        log.info("synced %d global commands", len(synced))
        return synced

    async def on_ready(self) -> None:
        assert self.user is not None
        log.info("ready as %s (%s) in %d servers", self.user, self.user.id, len(self.guilds))

    async def _on_tree_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError) -> None:
        await handle_app_command_error(interaction, error)

    async def close(self) -> None:
        log.info("shutting down")
        await super().close()
        await self.db.close()

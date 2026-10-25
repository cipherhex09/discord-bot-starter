from __future__ import annotations

import platform
import time
from datetime import timedelta

import discord
from discord import app_commands
from discord.ext import commands

from .. import __version__
from ..client import Bot
from ..utils.duration import humanize


class General(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @app_commands.command(description="Check that the bot is alive and how fast it answers.")
    @app_commands.checks.cooldown(1, 5)
    async def ping(self, interaction: discord.Interaction) -> None:
        start = time.perf_counter()
        await interaction.response.send_message("Pong...", ephemeral=True)
        roundtrip = (time.perf_counter() - start) * 1000
        await interaction.edit_original_response(
            content=f"Pong. Gateway {self.bot.latency * 1000:.0f} ms, round trip {roundtrip:.0f} ms."
        )

    @app_commands.command(description="What this bot is and how long it has been running.")
    async def about(self, interaction: discord.Interaction) -> None:
        uptime = humanize(timedelta(seconds=time.time() - self.bot.started_at))
        embed = discord.Embed(title=self.bot.user.name if self.bot.user else "Bot", color=discord.Color.dark_grey())
        embed.add_field(name="Uptime", value=uptime)
        embed.add_field(name="Servers", value=str(len(self.bot.guilds)))
        embed.add_field(name="Version", value=__version__)
        embed.set_footer(text=f"discord.py {discord.__version__} on Python {platform.python_version()}")
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: Bot) -> None:
    await bot.add_cog(General(bot))

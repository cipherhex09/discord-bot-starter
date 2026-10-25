"""Copy this file to start a new cog. Files starting with _ are not loaded."""

from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from ..client import Bot


class Example(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @app_commands.command(description="Say hello.")
    async def hello(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(f"Hello {interaction.user.mention}!", ephemeral=True)

    @app_commands.command(description="An example of slow work.")
    async def slow(self, interaction: discord.Interaction) -> None:
        # Discord gives you 3 seconds to respond. Defer first, then take your time.
        await interaction.response.defer(thinking=True, ephemeral=True)
        result = "done"  # await something slow here
        await interaction.followup.send(result)


async def setup(bot: Bot) -> None:
    await bot.add_cog(Example(bot))

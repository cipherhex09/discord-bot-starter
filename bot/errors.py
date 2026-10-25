"""One place that turns command errors into a reply the user understands.

Expected problems (missing permissions, cooldowns, bad input) get a plain
message. Anything unexpected is logged with a short id, and the user sees the
id so they can quote it when they report the bug.
"""

from __future__ import annotations

import logging
import secrets

import discord
from discord import app_commands

log = logging.getLogger("bot.errors")


class UserError(app_commands.AppCommandError):
    """Raise this from a command to show the message to the user as is."""


async def reply(interaction: discord.Interaction, content: str) -> None:
    try:
        if interaction.response.is_done():
            await interaction.followup.send(content, ephemeral=True)
        else:
            await interaction.response.send_message(content, ephemeral=True)
    except discord.HTTPException:
        # The interaction expired or the channel vanished. Nothing left to tell.
        pass


def describe(error: app_commands.AppCommandError) -> str | None:
    """A user-facing message for expected errors, or None for real bugs."""
    if isinstance(error, UserError):
        return str(error)
    if isinstance(error, app_commands.CommandOnCooldown):
        return f"Slow down. Try again in {error.retry_after:.0f}s."
    if isinstance(error, app_commands.MissingPermissions):
        return "You need these permissions: " + ", ".join(p.replace("_", " ") for p in error.missing_permissions)
    if isinstance(error, app_commands.BotMissingPermissions):
        return "I need these permissions here: " + ", ".join(p.replace("_", " ") for p in error.missing_permissions)
    if isinstance(error, app_commands.NoPrivateMessage):
        return "That command only works in a server."
    if isinstance(error, app_commands.CheckFailure):
        return "You can't use that command."
    if isinstance(error, app_commands.TransformerError):
        return f"I couldn't understand `{error.value}`."
    return None


async def handle_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError) -> None:
    message = describe(error)
    if message is not None:
        await reply(interaction, message)
        return

    error_id = secrets.token_hex(3)
    name = interaction.command.qualified_name if interaction.command else "unknown"
    original = error.original if isinstance(error, app_commands.CommandInvokeError) else error
    log.error(
        "error %s in /%s (user %s, guild %s)",
        error_id, name, interaction.user.id, interaction.guild_id,
        exc_info=(type(original), original, original.__traceback__),
    )  # fmt: skip
    await reply(interaction, f"Something went wrong on my side. Error id: `{error_id}`")

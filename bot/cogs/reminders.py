"""/remind: a real feature that shows the patterns you will reuse.

Reminders live in SQLite, so a restart never loses one. A background task
wakes up every few seconds and delivers whatever is due.
"""

from __future__ import annotations

import logging
import time

import discord
from discord import app_commands
from discord.ext import commands, tasks

from ..client import Bot
from ..errors import UserError
from ..utils.duration import humanize, parse_duration

log = logging.getLogger(__name__)

MAX_PER_USER = 25
MAX_DAYS = 365


class Reminders(commands.Cog):
    remind = app_commands.Group(name="remind", description="Reminders that survive restarts.")

    def __init__(self, bot: Bot):
        self.bot = bot

    async def cog_load(self) -> None:
        self.deliver_due.start()

    async def cog_unload(self) -> None:
        self.deliver_due.cancel()

    @remind.command(name="me", description="Remind you about something later.")
    @app_commands.describe(when="How long from now, like 10m, 2h or 1d 6h", what="What to remind you about")
    @app_commands.checks.cooldown(3, 30)
    async def remind_me(
        self, interaction: discord.Interaction, when: str, what: app_commands.Range[str, 1, 1000]
    ) -> None:
        try:
            delta = parse_duration(when)
        except ValueError as e:
            raise UserError(str(e)) from None
        if delta.total_seconds() > MAX_DAYS * 86400:
            raise UserError(f"Pick something within {MAX_DAYS} days.")

        db = self.bot.db.conn
        cur = await db.execute("SELECT COUNT(*) FROM reminders WHERE user_id = ?", (interaction.user.id,))
        (count,) = await cur.fetchone()
        if count >= MAX_PER_USER:
            raise UserError(f"You already have {MAX_PER_USER} reminders. Cancel one with `/remind cancel`.")

        due = time.time() + delta.total_seconds()
        await db.execute(
            "INSERT INTO reminders (user_id, channel_id, guild_id, message, due_at, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (interaction.user.id, interaction.channel_id, interaction.guild_id, what, due, time.time()),
        )
        await db.commit()
        await interaction.response.send_message(
            f"Okay, I'll remind you <t:{int(due)}:R> (in {humanize(delta)}).", ephemeral=True
        )

    @remind.command(name="list", description="Show your upcoming reminders.")
    async def remind_list(self, interaction: discord.Interaction) -> None:
        cur = await self.bot.db.conn.execute(
            "SELECT id, message, due_at FROM reminders WHERE user_id = ? ORDER BY due_at", (interaction.user.id,)
        )
        rows = await cur.fetchall()
        if not rows:
            await interaction.response.send_message("You have no reminders.", ephemeral=True)
            return
        lines = [
            f"`#{r['id']}` <t:{int(r['due_at'])}:R> {discord.utils.escape_markdown(r['message'][:80])}" for r in rows
        ]
        await interaction.response.send_message("\n".join(lines), ephemeral=True)

    @remind.command(name="cancel", description="Cancel one of your reminders.")
    @app_commands.describe(reminder="The reminder to cancel")
    async def remind_cancel(self, interaction: discord.Interaction, reminder: int) -> None:
        db = self.bot.db.conn
        cur = await db.execute("DELETE FROM reminders WHERE id = ? AND user_id = ?", (reminder, interaction.user.id))
        await db.commit()
        if cur.rowcount == 0:
            raise UserError("I couldn't find that reminder. `/remind list` shows yours.")
        await interaction.response.send_message("Cancelled.", ephemeral=True)

    @remind_cancel.autocomplete("reminder")
    async def _cancel_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[int]]:
        cur = await self.bot.db.conn.execute(
            "SELECT id, message FROM reminders WHERE user_id = ? AND message LIKE ? ORDER BY due_at LIMIT 25",
            (interaction.user.id, f"%{current}%"),
        )
        return [
            app_commands.Choice(name=f"#{r['id']} {r['message'][:90]}", value=r["id"]) for r in await cur.fetchall()
        ]

    @tasks.loop(seconds=5)
    async def deliver_due(self) -> None:
        db = self.bot.db.conn
        cur = await db.execute("SELECT * FROM reminders WHERE due_at <= ? ORDER BY due_at LIMIT 50", (time.time(),))
        for row in await cur.fetchall():
            try:
                await self._deliver(row)
            except Exception:
                # One broken reminder must not block the rest of the queue.
                log.exception("could not deliver reminder %s", row["id"])
            await db.execute("DELETE FROM reminders WHERE id = ?", (row["id"],))
        await db.commit()

    @deliver_due.before_loop
    async def _wait_ready(self) -> None:
        await self.bot.wait_until_ready()

    async def _deliver(self, row) -> None:
        text = f"<@{row['user_id']}> reminder: {row['message']}"
        mentions = discord.AllowedMentions(users=[discord.Object(row["user_id"])], everyone=False, roles=False)
        channel = self.bot.get_channel(row["channel_id"]) if row["channel_id"] else None
        if isinstance(channel, discord.abc.Messageable):
            try:
                await channel.send(text, allowed_mentions=mentions)
                return
            except discord.Forbidden:
                pass
        # Channel gone or no permission there: fall back to a DM.
        user = self.bot.get_user(row["user_id"]) or await self.bot.fetch_user(row["user_id"])
        await user.send(f"Reminder: {row['message']}")


async def setup(bot: Bot) -> None:
    await bot.add_cog(Reminders(bot))

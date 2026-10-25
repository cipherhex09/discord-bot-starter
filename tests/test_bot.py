import time
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import discord
import pytest
from discord import app_commands

from bot.client import Bot, discover_cogs
from bot.config import Config
from bot.errors import UserError, describe


@pytest.fixture
async def bot(tmp_path):
    b = Bot(Config(token="x", database_path=tmp_path / "bot.db", log_dir=None, sync_commands=False))
    # Run setup_hook without logging in to Discord.
    await b._async_setup_hook()
    await b.setup_hook()
    yield b
    await b.db.close()


def test_discover_skips_templates():
    cogs = discover_cogs()
    assert "bot.cogs.general" in cogs
    assert "bot.cogs.reminders" in cogs
    assert not any(c.endswith("_template") for c in cogs)


async def test_every_cog_loads_and_registers_commands(bot):
    names = {c.qualified_name for c in bot.tree.walk_commands()}
    assert {"ping", "about", "remind", "remind me", "remind list", "remind cancel"} <= names
    assert {"sync", "reload"} <= {c.name for c in bot.commands}


async def test_template_cog_loads(bot):
    await bot.load_extension("bot.cogs._template")
    assert bot.tree.get_command("hello") is not None


def test_user_errors_are_shown_and_bugs_are_not():
    assert describe(UserError("nope")) == "nope"
    assert "permissions" in describe(app_commands.MissingPermissions(["manage_guild"]))
    assert describe(app_commands.CommandInvokeError(MagicMock(), ValueError("boom"))) is None


async def test_due_reminders_are_delivered_and_removed(bot):
    db = bot.db.conn
    now = time.time()
    await db.executemany(
        "INSERT INTO reminders (user_id, channel_id, guild_id, message, due_at, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        [(1, 10, 100, "due", now - 1, now), (1, 10, 100, "later", now + 3600, now)],
    )
    await db.commit()

    channel = MagicMock(spec=discord.TextChannel)
    channel.send = AsyncMock()
    bot.get_channel = lambda _id: channel

    cog = bot.get_cog("Reminders")
    await cog.deliver_due.coro(cog)

    channel.send.assert_awaited_once()
    assert "due" in channel.send.await_args.args[0]
    cur = await db.execute("SELECT message FROM reminders")
    assert [r["message"] for r in await cur.fetchall()] == ["later"]


async def test_failed_delivery_does_not_block_queue(bot):
    db = bot.db.conn
    now = time.time()
    await db.executemany(
        "INSERT INTO reminders (user_id, channel_id, guild_id, message, due_at, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        [(1, 10, 100, "a", now - 2, now), (2, 10, 100, "b", now - 1, now)],
    )
    await db.commit()

    sent = []

    async def send(text, **_):
        if "a" in text.split(": ")[-1]:
            raise RuntimeError("discord is down")
        sent.append(text)

    bot.get_channel = lambda _id: SimpleNamespace(send=send)
    # SimpleNamespace is not Messageable, so delivery falls back to DM.
    user = MagicMock()
    user.send = AsyncMock(side_effect=[RuntimeError("closed DMs"), None])
    bot.get_user = lambda _id: user

    cog = bot.get_cog("Reminders")
    await cog.deliver_due.coro(cog)

    assert user.send.await_count == 2
    cur = await db.execute("SELECT COUNT(*) FROM reminders")
    assert (await cur.fetchone())[0] == 0

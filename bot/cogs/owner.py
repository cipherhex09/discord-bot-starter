"""Owner-only maintenance commands.

These are message commands triggered by mentioning the bot (`@Bot sync`) so
they never show up in anyone's slash command list. Mentions reach the bot
without the privileged message content intent.
"""

from __future__ import annotations

from discord.ext import commands

from ..client import Bot, discover_cogs


class Owner(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    async def cog_check(self, ctx: commands.Context) -> bool:
        return await self.bot.is_owner(ctx.author)

    @commands.command()
    async def sync(self, ctx: commands.Context) -> None:
        """Push slash command changes to Discord."""
        synced = await self.bot.sync_commands()
        await ctx.reply(f"Synced {len(synced)} commands.")

    @commands.command()
    async def reload(self, ctx: commands.Context, name: str | None = None) -> None:
        """Reload one cog by name, or all of them, without restarting."""
        targets = [f"bot.cogs.{name}"] if name else discover_cogs()
        done = []
        for ext in targets:
            if ext in self.bot.extensions:
                await self.bot.reload_extension(ext)
            else:
                await self.bot.load_extension(ext)
            done.append(ext.rsplit(".", 1)[-1])
        await ctx.reply("Reloaded " + ", ".join(done) + ". Run `sync` if you changed command names or options.")

    @reload.error
    @sync.error
    async def _on_error(self, ctx: commands.Context, error: commands.CommandError) -> None:
        if isinstance(error, commands.CheckFailure):
            return
        original = getattr(error, "original", error)
        await ctx.reply(f"Failed: {type(original).__name__}: {original}")


async def setup(bot: Bot) -> None:
    await bot.add_cog(Owner(bot))

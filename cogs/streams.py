import asyncio

import discord
from discord.ext import commands, tasks


class Streams(commands.Cog):
    """Cog for streams-and-promotions management."""

    def __init__(self, bot):
        self.bot = bot

        self.clear_channel.start()

    def cog_unload(self):
        self.clear_channel.cancel()

    @tasks.loop(hours=168.0)
    async def clear_channel(self):
        """Clear the streams channel every week."""
        channel = self.bot.get_channel(self.bot.settings.streams_channel)

        if channel is None:
            return

        await channel.guild.chunk()

        def check(msg):
            if not isinstance(msg.author, discord.Member):
                return True
            permissions = msg.author.guild_permissions
            return not permissions.manage_roles

        await channel.purge(check=check)


def setup(bot):
    bot.add_cog(Streams(bot))

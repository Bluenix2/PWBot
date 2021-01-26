import asyncio

import discord
from discord.ext import commands, tasks


class Streams(commands.Cog):
    """Cog for streams-and-promotions management."""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.channel.id != self.bot.settings.streams_channel:
            return

        if 'twitch.tv' not in message.content:
            return

        await message.delete(delay=14400)


def setup(bot):
    bot.add_cog(Streams(bot))

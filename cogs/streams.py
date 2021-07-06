# Yes this is a mere copy of lfg.py, a rewrite of this whole bot is long overdue.
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
        pins = await channel.pins()

        def check(msg):
            return msg not in pins

        await channel.purge(limit=None, check=check)


def setup(bot):
    bot.add_cog(Streams(bot))

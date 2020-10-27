from discord.ext import commands


class Events(commands.Cog):
    """Event specific code, for improving management of events."""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.channel.id != 651109293663191061:
            return

        await message.add_reaction(':survivor:500377451592155137')


def setup(bot):
    bot.add_cog(Events(bot))

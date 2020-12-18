from discord.ext import commands


class Responses(commands.Cog):
    """Cog for common responses to issues."""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        """React with thumbs up and down to all suggestions messages."""
        if message.author.bot:
            return
        if message.channel.id != self.bot.settings.suggestions_channel:
            return

        await message.add_reaction('\N{THUMBS UP SIGN}')
        await message.add_reaction('\N{THUMBS DOWN SIGN}')


def setup(bot):
    bot.add_cog(Responses(bot))

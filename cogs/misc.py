from discord.ext import commands


class Misc(commands.Cog):
    """Miscellaneous code and features, for the fun of it."""

    def __init__(self, bot):
        self.bot = bot


def setup(bot):
    bot.add_cog(Misc(bot))

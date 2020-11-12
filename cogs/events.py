from discord.ext import commands


class Events(commands.Cog):
    """Event specific code, for improving management of events."""
    pass


def setup(bot):
    bot.add_cog(Events(bot))

import discord
from discord.ext import commands, tasks


class LFG(commands.Cog):
    """Cog for looking-for-group management."""

    def __init__(self, bot):
        self.bot = bot

        self.clear_lfg_channel.start()

    def cog_unload(self):
        self.clear_lfg_channel.cancel()

    @tasks.loop(hours=24.0)
    async def clear_lfg_channel(self):
        """Clears the looking-for-group channel every 24 hours."""
        channel = self.bot.get_channel(self.bot.settings.lfg_channel)

        if channel is None:
            return

        await channel.guild.chunk()

        def check(msg):
            permissions = msg.author.guild_permissions
            return not permissions.manage_roles

        await channel.purge(check=check)


def setup(bot):
    bot.add_cog(LFG(bot))

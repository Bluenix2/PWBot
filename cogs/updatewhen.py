from discord.ext import commands


class UpdateWhen(commands.Cog):
    """Cog for matching "update when", isolated for easy unloading."""

    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return await self.bot.is_owner(ctx.author)

    @commands.Cog.listener()
    async def on_message(self, message):
        """Detect "update when" and send a message."""
        if message.author.bot:
            return

        # Ignore the command defined below
        if message.content.startswith('?updatewhen'):
            return

        content_lower = message.content.lower()
        if 'update' in content_lower and 'when' in content_lower:
            await message.channel.send(self.bot.settings.update_when_message)

    @commands.command()
    async def updatewhen(self, ctx, *, message):
        self.bot.settings.update_when_message = message
        await ctx.send('Changed update-when message.')


def setup(bot):
    bot.add_cog(UpdateWhen(bot))

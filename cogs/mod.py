import asyncio

import discord
from discord.ext import commands


class AutoMod(commands.Cog):
    """Auto-moderation capabilities for the bot."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def fakesteam(self, ctx, *, link):
        """Add a link to the list of fake Steam links."""
        if link in self.bot.settings.fake_steam_links:
            return await ctx.send('Link already registered.')

        # Sleep so that we add the link after the on_message below is called
        await asyncio.sleep(1)

        # This way we hit __setattr__
        self.bot.settings.fake_steam_links += [link]
        await ctx.send('Registered link.')

    @commands.Cog.listener()
    async def on_message(self, message):
        """Detect whether a message contains risky Steam links."""
        for link in self.bot.settings.fake_steam_links:
            if link in message.content:
                break
        else:
            # If there was a link in the message, it would've broke
            return

        await message.delete()
        if message.webhook_id:  # This was sent by a webhook
            return

        await message.author.add_roles(
            discord.Object(self.bot.settings.timed_out_role),
            reason=f'Sent a fake steam link: "{message.content}"'
        )


def setup(bot):
    bot.add_cog(AutoMod(bot))

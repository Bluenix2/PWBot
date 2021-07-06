import asyncio
import re

import discord
from discord.ext import commands

from cogs.utils import is_mod

# Regex to match a link with '.ru'
russian_link = re.compile(
    r'(?:https?:\/\/)?' +
    r'(?:www\.)?' +
    r'[-a-zA-Z0-9@:%._\+~#=]{1,256}\.ru' +
    r'(?:[-a-zA-Z0-9()@:%_\+.~#?&\/=]*)'
)


class AutoMod(commands.Cog):
    """Auto-moderation capabilities for the bot."""

    def __init__(self, bot):
        self.bot = bot

    @is_mod()
    @commands.command()
    async def fakesteam(self, ctx, *, link):
        """Add a link to the list of fake Steam links."""
        if link in self.bot.settings.fake_steam_links:
            return await ctx.send('Link already registered.')

        # This way we hit __setattr__
        self.bot.settings.fake_steam_links += [link]
        await ctx.send('Registered link.')

    @commands.Cog.listener()
    async def on_message(self, message):
        """Detect whether a message contains risky Steam links."""
        if not isinstance(message.author, discord.Member):  # In DMs
            return

        # Ignore moderators
        if not message.author.guild_permissions.manage_roles:
            return

        if message.webhook_id:  # This was sent by a webhook
            return

        match = re.search(russian_link, message.content)
        found = None
        for link in self.bot.settings.fake_steam_links:
            if link in message.content:
                found = link

        if not (match or found):
            return

        await message.delete()
        await message.channel.send(
            'Because of a surge in fake steam links, '
            'we have employed a blankey ban on `.ru` links.',
            delete_after=5.0
        )

        # Only time out if it is a known link
        if found:
            await message.author.add_roles(
                discord.Object(self.bot.settings.timed_out_role),
                reason=f'Sent a fake steam link: "{message.content}"'
            )


def setup(bot):
    bot.add_cog(AutoMod(bot))

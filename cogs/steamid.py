import re

from discord.ext import commands
from steam.steamid import steam64_from_url


# https://www.steamcommunity.com/id/Bluenix/
steamcommunity = re.compile(
    r'(?:https?:\/\/)?' +  # https://
    r'(?:www\.)?' +  # www.
    r'steamcommunity.com\/id\/' +  # steamcommunity.com/id/
    r'(?:.*)'  # Bluenix/
)


class SteamID(commands.Cog):
    """Cog for finding permanent profiles and automatically send them."""
    def __init__(self, bot):
        self.bot = bot

    async def handle_steam(self, message, link=None):
        """Handle a found steam link."""
        matches = link or re.findall(steamcommunity, message.content)
        steamids = [str(steam64_from_url(m)) for m in matches]

        if not steamids:
            return

        await message.channel.send(
            ('Here are their permanent counterparts:\n' if not link else '') +
            '\n'.join(f'<https://www.steamcommunity.com/profiles/{id_}/>' for id_ in steamids)
        )

    @commands.command()
    async def steamid(self, ctx, *, link):
        """Get a permanent link to a steam profile."""
        await self.handle_steam(ctx.message, link)

    @commands.Cog.listener()
    async def on_message(self, message):
        await self.handle_steam(message)


def setup(bot):
    bot.add_cog(SteamID(bot))

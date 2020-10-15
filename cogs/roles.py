import discord
from discord.ext import commands

from cogs.utils import colours


class Roles(commands.Cog):
    """Manages reaction roles."""
    def __init__(self, bot):
        self.bot = bot

        # A mapping of reaction unicode characters to role ids.
        self.roles = {
            '📣': 765262869239431191,
            '🎟': 765263058515525633,
            '🏆': 765263032489738293
        }

    @commands.command(name='sendrolemessage', hidden=True)
    async def send_role_message(self, ctx):
        await ctx.message.delete()

        description = """To avoid pinging everyone we've created a few roles to ping instead.

        React to this message to assign the appropriate role.
        If you have any questions feel free to ping a Community Manager
        """
        embed = discord.Embed(
            title='Role Management',
            description=description,
            colour=colours.light_blue()
        )

        embed.add_field(
            name='\N{CHEERING MEGAPHONE} Announcements',
            value='Will get pinged in <#489825441075429378> when the game is updated or the developers have important information to share.',
            inline=False
        )
        embed.add_field(
            name='\N{ADMISSION TICKETS} Events',
            value='Pinged in <#651109293663191061> or <#489825441075429378> when a new event is created, or event details have been released/updated.',
            inline=False
        )
        embed.add_field(
            name='\N{TROPHY} Tournaments',
            value='Pinged in <#647955879844380682> when new community-run tournaments are hosted or information is released/updated.',
            inline=False
        )
        embed.add_field(
            name='\N{GLOBE WITH MERIDIANS} Community Translations',
            value='We are looking to let active community members helps us translate the game.\n**If you want to help please contact a Community Manager**.',
            inline=False
        )

        message = await ctx.send(embed=embed)
        self.bot.settings.reaction_message = message.id

        await message.add_reaction('\N{CHEERING MEGAPHONE}')
        await message.add_reaction('\N{ADMISSION TICKETS}')
        await message.add_reaction('\N{TROPHY}')

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.message_id != self.bot.settings.reaction_message:
            return

        if payload.user_id == self.bot.client_id:
            return

        role_id = self.roles.get(payload.emoji.name)
        if not role_id:
            return await self.bot.http.remove_reaction(
                payload.channel_id, payload.message_id,
                payload.emoji, payload.member.id,
            )

        await self.bot.http.add_role(payload.guild_id, payload.user_id, role_id)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        if payload.message_id != self.bot.settings.reaction_message:
            return

        role_id = self.roles.get(payload.emoji.name)
        if not role_id:
            return

        await self.bot.http.remove_role(payload.guild_id, payload.user_id, role_id)


def setup(bot):
    bot.add_cog(Roles(bot))

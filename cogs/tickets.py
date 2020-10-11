import discord
from discord.ext import commands

from cogs.utils import checks, ticket_mixin


class TicketManager(commands.Cog, ticket_mixin.TicketMixin):
    """Cog managing all normal tickets for help."""
    def __init__(self, bot):
        self.bot = bot

        self.ticket_type = ticket_mixin.TicketType.ticket
        self._category = None
        self.category_id = self.bot.settings.ticket_category

        self.message_id = self.bot.settings.ticket_message
        self.open_message = """Welcome

        Thank you for opening a ticket, what can we help you with?
        Please explain what you need help with and we will get back with you.
        """

        self.create_log = True
        self.log_channel_id = self.bot.settings.log_channel

        self.adduser_message = "Welcome {0}, you were added to this ticket."

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        await self.on_reaction(payload)

    @commands.group(
        invoke_without_command=True,
        brief='Open a help ticket',
        help='Open a help ticket, giving access to a private channel with mods.')
    async def ticket(self, ctx, *, issue=None):
        await self.on_open_command(ctx, issue)

    @ticket.command(name='adduser', breif='Add a user to the help ticket.')
    @ticket_mixin.ticket_only()
    @ticket_mixin.author_only()
    async def ticket_adduser(self, ctx, user: discord.User):
        await ctx.channel.set_permissions(user, read_messages=True)

        description = "Welcome {0}, you were added to this ticket."
        await ctx.send(user.mention, embed=discord.Embed(
            description=description.format(user.mention),
            colour=discord.Color.greyple(),
        ))

    @ticket.command(name='close', breif='Close the ticket, creating an archive')
    @ticket_mixin.ticket_only()
    @checks.mod_only()
    async def ticket_close(self, ctx, *, reason=None):
        await self.on_close_command(ctx, reason)


def setup(bot):
    bot.add_cog(TicketManager(bot))

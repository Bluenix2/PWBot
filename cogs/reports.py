import discord
from discord.ext import commands

from cogs.utils import checks, ticket_mixin


class ReportManager(commands.Cog, ticket_mixin.TicketMixin):
    """Cog managing all report tickets reporting players."""
    def __init__(self, bot):
        super().__init__()

        self.bot = bot

        self.ticket_type = ticket_mixin.TicketType.report
        self.category_id = self.bot.settings.report_category

        self.open_message = '\n'.join((
            'Thank you for reporting, please provide all the evidence.',
            'Feel free to use the following template: ```',
            'Username/Steam ID:',
            'Reason:',
            'Description of incident:',
            'Evidence (Video or screenshots):',
            '```',
        ))

        self.status_channel_id = self.bot.settings.report_status_channel

        self.create_log = False

    @property
    def message_id(self):
        # Defining the attribute directy means it doesn't get changed
        # when bot.settings.report_message gets changed
        return self.bot.settings.report_message

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        await self.on_reaction(payload)

    @commands.group(
        invoke_without_command=True,
        brief='Manage report tickets, see subcommand: ?report open',
        help='Manage report tickets')
    async def report(self, ctx, *, issue=None):
        await ctx.invoke(self.report_open, issue=issue)

    @report.command(
        name='open',
        brief='Open a report ticket',
        help='Open a report ticket, giving access to a private channel with mods.')
    async def report_open(self, ctx, *, issue=None):
        await self.on_open_command(ctx, issue)

    @report.command(
        name='openas',
        brief='Open a report ticket for a user',
        help='Open a report ticket for a user, giving access to a private channel with mods.')
    @checks.mod_only()
    async def report_openas(self, ctx, user: discord.User, *, issue=None):
        await self.on_open_command(ctx, issue, user=user)

    @report.command(name='close', brief='Close the ticket')
    @ticket_mixin.ticket_only()
    @checks.mod_only()
    async def report_close(self, ctx, *, reason=None):
        await self.on_close_command(ctx, reason)


def setup(bot):
    bot.add_cog(ReportManager(bot))

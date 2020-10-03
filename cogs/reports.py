from discord.ext import commands

from cogs.utils import checks, ticket_mixin


class ReportManager(commands.Cog, ticket_mixin.TicketMixin):
    """Cog managing all report tickets reporting players."""
    def __init__(self, bot):
        self.bot = bot

        self.ticket_type = ticket_mixin.TicketType.report
        self._category = None
        self.category_id = self.bot.settings.report_category

        self.message_id = self.bot.settings.report_message
        self.open_message = """Welcome {0}

        Thank you for reporting, please provide all evidence.
        Examples of good evidence is video proof and screenshots.
        Please also post their or your Steam link.
        """

        self.create_log = False

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        await self.on_reaction(payload)

    @commands.group(
        invoke_without_command=True,
        brief='Open a report ticket',
        help='Open a report ticket, giving access to a private channel with mods.')
    async def report(self, ctx, *, issue=None):
        await self.on_open_command(ctx, issue)

    @report.command(name='close', brief='Close the ticket')
    @ticket_mixin.ticket_only()
    @checks.mod_only()
    async def report_close(self, ctx, *, reason=None):
        await self.on_close_command(ctx, reason)


def setup(bot):
    bot.add_cog(ReportManager(bot))

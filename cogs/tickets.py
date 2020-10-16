import discord
from discord.ext import commands

from cogs.utils import checks, colours, ticket_mixin


class TicketManager(commands.Cog, ticket_mixin.TicketMixin):
    """Cog managing all normal tickets for help."""
    def __init__(self, bot):
        super().__init__()

        self.bot = bot

        self.ticket_type = ticket_mixin.TicketType.ticket
        self.category_id = self.bot.settings.ticket_category

        self.open_message = """Welcome {0}

        Thank you for opening a ticket, what can we help you with?
        Please explain what you need help with and we will get back with you.

        You may want to post a log for us, this is very helpful. See `?log`.
        """

        self.status_channel_id = self.bot.settings.ticket_status_channel

        self.create_log = True
        self.log_channel_id = self.bot.settings.log_channel

    @property
    def message_id(self):
        # Defining the attribute directy means it doesn't get changed
        # when bot.settings.ticket_message gets set
        return self.bot.settings.ticket_message

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        await self.on_reaction(payload)

    @commands.group(
        invoke_without_command=True,
        brief='Manage help tickets, see subcommand: ?ticket open',
        help='Manage help tickets')
    async def ticket(self, ctx, *, issue=None):
        if issue:  # Aid users in opening tickets
            return await ctx.invoke(self.ticket_open, issue=issue)

        await ctx.send('\n'.join((
            '> You can open a help ticket by using the following command:',
            '> ```',
            '> ?ticket open <issue>',
            '> ```',
            '> So, for example:',
            '> ```',
            '> ?ticket open My voice comms are not working.',
            '> ```',
            '> Upon opening a ticket a new private channel with the mods will be created '
            'where we can securely talk and disclose important information.',
            '> **Abuse of the ticket system could result in a temporary squelching.**',
        )))

    @ticket.command(
        name='open', brief='Open a help ticket',
        help='Open a help ticket, giving access to a private channel with the mods.')
    async def ticket_open(self, ctx, *, issue=None):
        await self.on_open_command(ctx, issue)

    @ticket.command(
        name='openas',
        brief='Open a help ticket for a user',
        help='Open a help ticket for a user, giving access to a private channel with mods.')
    @checks.mod_only()
    async def report_openas(self, ctx, user: discord.User, *, issue=None):
        await self.on_open_command(ctx, issue, user=user)

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

    @ticket.command(name='megamode')
    @commands.is_owner()
    async def ticket_megamode(self, ctx):
        await ctx.message.delete()
        help_channel = ctx.guild.get_channel(self.bot.settings.help_channel)

        if self.bot.settings.ticket_message == 0:
            await help_channel.set_permissions(ctx.guild.default_role, send_messages=False)

            description = '\n'.join((
                'We have temporarily limited the help channels at the moment. To get help '
                'please open a ticket where you will get access to a private channel.',
                'Simply react below with <:high5:{}>!'.format(self.bot.settings.high5_emoji)
            ))

            message = await help_channel.send(embed=discord.Embed(
                title='Help',
                description=description,
                colour=colours.light_blue()
            ))
            self.bot.settings.ticket_message = message.id

            await message.add_reaction(':high5:{}'.format(self.bot.settings.high5_emoji))

        else:
            await help_channel.set_permissions(ctx.guild.default_role, send_messages=None)

            await self.bot.http.delete_message(
                help_channel.id,
                self.bot.settings.ticket_message
            )

            self.bot.settings.ticket_message = 0


def setup(bot):
    bot.add_cog(TicketManager(bot))

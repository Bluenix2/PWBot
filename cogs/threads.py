import enum

import discord
from discord.ext import commands

from cogs.utils import checks


def thread_only():
    async def predicate(ctx):
        if ctx.guild is None:
            return False

        query = 'SELECT id FROM threads WHERE id=$1;'
        record = await ctx.db.fetchrow(query, ctx.channel.id)

        return bool(record)
    return commands.check(predicate)


def thread_author():
    async def predicate(ctx):
        query = 'SELECT author FROM threads WHERE id=$1;'
        record = await ctx.db.fetchval(query, ctx.channel.id)

        return record == ctx.author.id
    return commands.check(predicate)


class ThreadState(enum.Enum):
    open = 0
    closed = 1


class Threads(commands.Cog):
    """Commands for creating, opening and managing threads."""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.message_id not in (
            self.bot.settings.ticket_message, self.bot.settings.report_message
        ):
            return

        # Use raw method to avoid unnecessary API calls
        await self.bot.http.remove_reaction(
            payload.channel_id, payload.message_id,
            payload.emoji, payload.member.id,
        )

        if str(payload.emoji) != '\N{WHITE MEDIUM STAR}':  # Will be changed
            return

        if payload.message_id == self.bot.settings.ticket_message:
            await self.create_ticket(self.bot.get_user(payload.user_id))

        elif payload.message_id == self.bot.settings.report_message:
            await self.create_report(self.bot.get_user(payload.user_id))

    async def create_ticket(self, user, issue=''):
        """Create a new ticket under the ticket category."""
        category = self.bot.get_channel(self.bot.settings.ticket_category)

        description = """Welcome {0}

        Thank you for opening a ticket, what can we help you with?
        Please explain what you need help with and we will get back with you.
        """

        await self._create_thread(
            user, category, 'ticket-{0}'.format(issue), description,
        )

    async def create_report(self, user, issue=''):
        """Create a new report under the report category."""
        category = self.bot.get_channel(self.bot.settings.report_category)

        description = """Welcome {0}

        Thank you for reporting, please provide all evidence.
        Examples of good evidence is video proof and screenshots.
        Please also post their or your Steam link.
        """

        await self._create_thread(
            user, category, 'report-{0}'.format(issue), description,
        )

    @commands.group(aliases=['ticket', 'report'], invoke_without_command=True)
    async def thread(self, ctx, *, message=''):
        """Parent to all ticket commands.

        Also opens a ticket to help inexperienced users.
        """
        # Redirect to opening a ticket
        await ctx.invoke(self.thread_create, message=message)

    @thread.command(name='create', aliases=['open'])
    async def thread_create(self, ctx, *, message=''):
        """Open a thread, giving both author and mod team access."""
        # Commands are ugly and in case it contains confidential information
        await ctx.message.delete()

        if ctx.invoked_with.startswith('ticket'):
            await self.create_ticket(ctx.author, message)

        elif ctx.invoked_with.startswith('report'):
            await self.create_report(ctx.author, message)

    @thread.command(name='adduser', aliases=['add', 'user'])
    @thread_only()
    async def thread_adduser(self, ctx, user: discord.User):
        """Add a user to the thread."""
        overwrites = {
            user: discord.PermissionOverwrite(
                read_messages=True,
            ),
        }
        overwrites.update(ctx.channel.category.overwrites)

        description = 'Welcome {0}, you were added to this thread.'
        await ctx.send(user.mention, embed=discord.Embed(
            description=description.format(user.mention),
            colour=discord.Colour.greyple(),
        ))

    @thread.command(name='close')
    @thread_only()
    @checks.is_mod()
    async def thread_close(self, ctx):
        """Close a thread, deleting the channel."""
        query = 'UPDATE threads SET state=$1 WHERE id=$2;'
        await ctx.db.execute(query, ThreadState.closed.value, ctx.channel.id)

        await ctx.channel.delete()

    async def _create_thread(
        self, user, category, channel_name, description,
    ):
        """Create a new thread."""
        overwrites = {
            user: discord.PermissionOverwrite(
                read_messages=True,
            ),
        }
        overwrites.update(category.overwrites)

        channel = await category.create_text_channel(
            name=channel_name, sync_permissions=True,
            overwrites=overwrites,
        )

        query = 'INSERT INTO threads (id, author) VALUES ($1, $2);'
        await self.bot.pool.execute(query, channel.id, user.id)

        await channel.send(user.mention, embed=discord.Embed(
            description=description.format(user.mention),
            colour=discord.Colour.greyple(),
        ))


def setup(bot):
    bot.add_cog(Threads(bot))

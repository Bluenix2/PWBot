import enum
import io
import os
import zipfile

import discord
from cogs.utils import colours
from discord.ext import commands


def ticket_only():
    """Check for channel being a ticket,
    can only be used on commands inside TicketMixin subclasses
    becauses it uses the ticket_type attribute.
    """
    async def predicate(ctx):
        if ctx.guild is None:
            return False

        query = """SELECT EXISTS (
                SELECT 1 FROM tickets WHERE channel_id=$1 AND type=$2 LIMIT 1
            );
        """
        record = await ctx.db.fetchval(query, ctx.channel.id, ctx.cog.ticket_type.value)

        return bool(record)
    return commands.check(predicate)


def author_only():
    async def predicate(ctx):
        if ctx.guild is None:
            return False

        query = 'SELECT author_id FROM tickets WHERE channel_id=$1;'
        author_id = await ctx.db.fetchval(query, ctx.channel.id)

        return author_id == ctx.author.id
    return commands.check(predicate)


class TicketType(enum.Enum):
    ticket = 0
    report = 1


class TicketState(enum.Enum):
    open = 0
    closed = 1


class TicketMixin:
    """Central class for managing tickets.
    The following attributes must be defined when subclassing.
    You don't need to call init.

    Attributes
    -----------
    ticket_type: TicketType
        The type of ticket. This is used in queries.
    category_id: int
        The id of the category that the tickets will be created in
    open_message: str
        The content of the message the bot should send, will be formatted
        with a mention of the author.
    status_channel_id: int
        The id of the channel where updates and statuses on tickets are kept.
    create_log: bool
        If logs should be created when closing the ticket.
    log_channel_id: Optional[int]
        The id of the channel that the log archives will be sent to.
    message_id: Optional[int]
        The id of the message that it should create tickets
        when reacted to.
        """

    def __init__(self):
        self._category = None
        self._status_channel = None
        self._log_channel = None

    @property
    def category(self):
        if not self._category:
            self._category = self.bot.get_channel(self.category_id)
        return self._category

    @property
    def status_channel(self):
        if not self._status_channel:
            self._status_channel = self.bot.get_channel(self.status_channel_id)
        return self._status_channel

    @property
    def log_channel(self):
        if not self._log_channel:
            self._log_channel = self.bot.get_channel(self.log_channel_id)
        return self._log_channel

    async def get_open_by_author(self, author_id):
        query = 'SELECT channel_id FROM tickets WHERE author_id=$1 AND state=$2 AND type=$3;'
        channel_id = await self.bot.pool.fetchval(
            query, author_id, TicketState.open.value, self.ticket_type.value
        )

        return channel_id

    async def on_reaction(self, payload):
        if payload.message_id != self.message_id:
            return

        if payload.user_id == self.bot.client_id:
            return

        await self.bot.http.remove_reaction(
            payload.channel_id, payload.message_id,
            payload.emoji._as_reaction(), payload.member.id,
        )

        if payload.emoji.id != self.bot.settings.high5_emoji:
            return

        open_channel = await self.get_open_by_author(payload.user_id)
        if open_channel:
            return await self.bot.http.send_message(
                open_channel, '<@{0}> you already have an open ticket in here.'.format(
                    payload.user_id
                ))

        await self._create_ticket(payload.member, None)

    async def on_open_command(self, ctx, issue, *, user=None):
        author = user or ctx.author

        await ctx.message.delete()

        open_channel = await self.get_open_by_author(author.id)
        if open_channel:
            return await ctx.send('{0} you already have an open ticket: <#{1}>'.format(
                    ctx.author.mention, open_channel
                ), delete_after=10
            )

        await self._create_ticket(author, issue, conn=ctx.db)

    async def _create_ticket(self, author, issue, *, conn=None):
        conn = conn or self.bot.pool  # We expect to be in a cog

        ticket_id = await conn.fetchval("SELECT nextval('ticket_id')")

        overwrites = {
            author: discord.PermissionOverwrite(
                read_messages=True,
            ),
        }
        overwrites.update(self.category.overwrites)

        channel = await self.category.create_text_channel(
            name='{0}-{1}'.format(ticket_id, issue or self.ticket_type.name),
            sync_permissions=True,
            overwrites=overwrites,
        )

        query = """INSERT INTO tickets (
                    id, channel_id, author_id, type, issue
                ) VALUES ($1, $2, $3, $4, $5) RETURNING *;
        """
        record = await conn.fetchrow(
            query, ticket_id, channel.id, author.id,
            self.ticket_type.value, issue[:90] if issue else None
        )

        await channel.send(author.mention, embed=discord.Embed(
            description=self.open_message.format(author.mention),
            colour=colours.light_blue(),
        ))

        title = '{} #{}{}'.format(
            self.ticket_type.name[0].upper() + self.ticket_type.name[1:],
            record['id'], ' - {}'.format(issue) if issue else ''
        )

        embed = discord.Embed(
            title=title,
            colour=colours.cyan()
        )

        embed.set_author(name=author, icon_url=author.avatar_url)

        message = await self.status_channel.send(embed=embed)

        await conn.execute(
            'UPDATE tickets SET status_message_id=$1 WHERE id=$2',
            message.id, record['id']
        )

        return channel, record

    async def on_close_command(self, ctx, reason):
        query = 'SELECT * from tickets WHERE channel_id=$1;'
        record = await ctx.db.fetchrow(query, ctx.channel.id)

        if not record:
            return

        log_message = None
        if self.create_log:
            await ctx.send('Locked the channel. Creating logs, this may take a while.')

            overwrites = {
                ctx.guild.default_role: discord.PermissionOverwrite(
                    read_messages=False,
                ),
                self.bot.user: discord.PermissionOverwrite(
                    read_messages=True,
                ),
            }
            await ctx.channel.edit(overwrites=overwrites)

            archive = await self._generate_log(ctx.channel, record)

            issue = '-' + record['issue'] if record['issue'] else ''
            filename = f"log-{record['id']}{issue}.zip"
            log = discord.File(archive, filename=filename)

            # We send the file name so that it's easily searched in discord
            log_message = await self.log_channel.send(filename, file=log)

        query = 'UPDATE tickets SET state=$1 WHERE channel_id=$2'
        await ctx.db.execute(query, TicketState.closed.value, record['channel_id'])

        message = await self.status_channel.fetch_message(record['status_message_id'])
        embed = message.embeds[0]

        embed.description = reason
        embed.colour = colours.apricot()

        embed.set_footer(
            text=f'{ctx.author} ({ctx.author.id})',
            icon_url=ctx.author.avatar_url
        )
        if log_message:
            embed.add_field(name='Log', value=f'[Jump!]({log_message.jump_url})')

        await message.edit(embed=embed)

        await ctx.channel.delete(reason=reason)

    async def _generate_log(self, channel, record):
        """Create a log archive with transcript and attachments."""
        messages = ["""Transcript of ticket {0} "{1}" opened by user {2}:\n""".format(
            record['id'], record['issue'], record['author_id'],
        )]

        attachments = []
        async for message in channel.history(oldest_first=True):
            messages.append(
                "[{2}] {0.author} ({0.author.id}){1}: {0.content}".format(
                    message, ' (attachment)' if message.attachments else '',
                    message.created_at.strftime('%Y %b %d %H:%M:%S')
                )
            )
            attachments.extend(message.attachments)

        memory = io.BytesIO()
        archive = zipfile.ZipFile(memory, 'a', zipfile.ZIP_DEFLATED, False)

        for index in range(len(attachments)):

            archive.writestr(
                'attachment-' + str(index) + os.path.splitext(attachments[index].filename)[1],
                await attachments[index].read()
            )

        archive.writestr('transcript.txt', '\n'.join(messages))
        archive.close()

        memory.seek(0)
        return memory

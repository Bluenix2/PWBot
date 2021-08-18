import asyncio
import enum
import os

import discord
from discord.ext import commands

from cogs.utils import Colour, is_mod, ignore_report_webhooks


def ticket_only():
    """Check for channel being a ticket,
    can only be used on commands inside TicketMixin subclasses
    because it uses the ticket_type attribute.
    """
    async def predicate(ctx):
        if ctx.guild is None:
            return False

        query = """SELECT EXISTS (
                SELECT 1 FROM tickets WHERE channel_id=$1 LIMIT 1
            );
        """
        record = await ctx.db.fetchval(query, ctx.channel.id)

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


class TicketState(enum.Enum):
    open = 0
    closed = 1


class TicketManager(commands.Cog):
    """Cog managing all normal tickets for help."""
    def __init__(self, bot):
        self.bot = bot

        self.open_message = '\n'.join((
            'Thank you for opening a ticket, what can we help you with?',
            'Please explain what you need help with and we will get back with you.\n',

            'If you are having technical issues, please post a log. See `?log`.',
            'Otherwise, if your issue is related to in-game bans or crate purchasing please ' +
            'copy your ID seen under Settings, or send your in-game name / Steam profile.'
        ))

        self._category = None
        self._status_channel = None
        self._log_channel = None

    @property
    def category(self):
        if not self._category:
            self._category = self.bot.get_channel(self.bot.settings.ticket_category)
        return self._category

    @property
    def status_channel(self):
        if not self._status_channel:
            self._status_channel = self.bot.get_channel(
                self.bot.settings.ticket_status_channel
            )
        return self._status_channel

    @property
    def log_channel(self):
        if not self._log_channel:
            self._log_channel = self.bot.get_channel(self.bot.settings.ticket_log_channel)
        return self._log_channel

    async def get_open_by_author(self, author_id):
        query = 'SELECT channel_id FROM tickets WHERE author_id=$1 AND state=$2;'
        channel_id = await self.bot.pool.fetchval(
            query, author_id, TicketState.open.value
        )

        return channel_id

    async def _create_ticket(self, author, issue, *, prefix=None, conn=None):
        conn = conn or self.bot.pool

        # If issue is None
        issue = issue.strip('<>') if isinstance(issue, str) else issue
        ticket_id = await conn.fetchval("SELECT nextval('ticket_id');")

        overwrites = {
            author: discord.PermissionOverwrite(
                read_messages=True
            )
        }
        overwrites.update(self.category.overwrites)

        channel = await self.category.create_text_channel(
            name='{0}-{1}-{2}'.format(
                prefix or '', ticket_id, issue[:90] if issue else author.display_name
            ),
            sync_permissions=True, overwrites=overwrites,
            reason='Creating ticket #{0}: {1}'.format(ticket_id, issue)
        )

        query = """INSERT INTO tickets (
                    id, channel_id, author_id, issue
                ) VALUES ($1, $2, $3, $4) RETURNING *;
        """
        record = await conn.fetchrow(
            query, ticket_id, channel.id, author.id,
            issue[:90] if issue else None
        )

        await channel.send(
            'Welcome {0}'.format(author.mention),
            embed=discord.Embed(
                description=await self.bot.fetch_tag(
                    prefix + '-ticket'
                ) if prefix else self.open_message,
                colour=Colour.light_blue(),
            )
        )

        title = '{} #{}{}'.format(
            (prefix[0].upper() + prefix[1:]) if prefix else 'Ticket',
            record['id'], ' - {}'.format(issue[:235]) if issue else ''
        )

        embed = discord.Embed(
            title=title,
            colour=Colour.cyan()
        )

        embed.set_author(name=author, icon_url=author.avatar_url)

        message = await self.status_channel.send(embed=embed)

        await conn.execute(
            'UPDATE tickets SET status_message_id=$1 WHERE id=$2',
            message.id, record['id']
        )

        return channel, record

    async def on_open_command(self, ctx, issue, *, prefix=None, user=None):
        author = user or ctx.author

        await ctx.message.delete()

        open_channel = await self.get_open_by_author(author.id)
        if open_channel:
            return await ctx.send('{0} already has an open ticket: <#{1}>'.format(
                    author.mention, open_channel
                ), delete_after=10
            )

        channel, record = await self._create_ticket(author, issue, prefix=prefix, conn=ctx.db)

        # Only for tickets, reports should stay anonymous
        await ctx.send('Opened ticket #{} in {} for {}.'.format(
            record['id'], channel.mention, author.mention
        ), allowed_mentions=discord.AllowedMentions(users=False))

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.message_id != self.bot.settings.ticket_message:
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
            msg = await self.bot.http.send_message(
                open_channel, f'<@{payload.user_id}> you already have an open ticket in here.'
            )
            await asyncio.sleep(10)
            return await self.bot.http.delete_message(open_channel, msg['id'])

        await self._create_ticket(payload.member, None)

    @commands.command()
    @is_mod()
    async def tickets(self, ctx, user: discord.Member):
        """Get all tickets opened by a specific user."""

        embed = discord.Embed(title=f"Tickets opened by {user}", colour=Colour.light_blue())

        tickets = await self.bot.pool.fetch(
            'SELECT * FROM tickets WHERE author_id=$1;',
            user.id
        )

        to_display = tickets
        if len(tickets) > 25:
            to_display = tickets[:25]

        for ticket in to_display:
            # Craft the message link
            link = 'https://discord.com/channels/431073730828173312/'
            link += f'{self.status_channel.id}/'
            link += str(ticket['status_message_id'])

            # Craft the field name
            name = f"Ticket #{ticket['id']}"
            if ticket['issue']:
                name += f" - {ticket['issue'][:235]}"

            embed.add_field(
                name=name,
                value=f"[Message link!]({link})",
                inline=False
            )

        footer = f'{user} has opened {len(tickets)} tickets.'
        if to_display is not tickets:
            footer += 'Displaying only 25 in no particular order.'

        embed.set_footer(text=footer)

        await ctx.send(embed=embed)

    @ignore_report_webhooks()
    @commands.group(invoke_without_command=True)
    async def ticket(self, ctx, *, issue=None):
        """Open a ticket or send a help message. Parent command for ticket management."""
        if issue:  # Aid users in opening tickets
            # Ignore moderators, so it isn't accidentally used
            if isinstance(ctx.author, discord.Member) and \
                    ctx.author.guild_permissions.manage_roles:
                return

            return await ctx.invoke(self.ticket_open, issue=issue)

        await ctx.send_tag('ticket')

    @ignore_report_webhooks()
    @ticket.command(name='open')
    async def ticket_open(self, ctx, *, issue=None):
        """Open a help ticket."""
        if self.bot.settings.pc_channel == ctx.channel.id:
            prefix = 'pc'
        elif self.bot.settings.xbox_channel == ctx.channel.id:
            prefix = 'xbox'
        else:
            prefix = ''
        await self.on_open_command(ctx, issue, prefix=prefix)

    @ticket.command(name='pc')
    @is_mod()
    async def ticket_pc(self, ctx, user: discord.Member, *, issue=None):
        """Open a Pc ticket for a member. This can only be used by mods."""
        await self.on_open_command(ctx, issue, prefix='pc', user=user)

    @ticket.command(name='xbox')
    @is_mod()
    async def ticket_xbox(self, ctx, user: discord.Member, *, issue=None):
        """Open a Xbox ticket for a member. This can only be used by mods."""
        await self.on_open_command(ctx, issue, prefix='xbox', user=user)

    @ticket.command(name='openas')
    @is_mod()
    async def ticket_openas(self, ctx, user: discord.Member, *, issue=None):
        """Open a ticket for a member. This can only be used by mods."""
        if self.bot.settings.pc_channel == ctx.channel.id:
            prefix = 'pc'
        elif self.bot.settings.xbox_channel == ctx.channel.id:
            prefix = 'xbox'
        else:
            prefix = ''
        await self.on_open_command(ctx, issue, prefix=prefix, user=user)

    @ticket.command(name='adduser')
    @ticket_only()
    @commands.check_any(author_only(), is_mod())
    async def ticket_adduser(self, ctx, user: discord.User):
        """Add a member to the help ticket."""
        await ctx.channel.set_permissions(user, read_messages=True)

        await ctx.send(
            "Welcome {0}, you were added to this ticket.".format(user.mention)
        )

    async def _generate_log(self, channel, record):
        """Create a log archive with transcript and attachments."""
        transcript = f"transcript-{record['id']}.txt"
        with open(transcript, 'a+') as f:
            f.write("""Transcript of ticket {0}{1} opened by user {2}:\n""".format(
                record['id'], (' "' + record['issue'] + '"') if record['issue'] else '',
                record['author_id']
            ))

            attachments = []
            async for message in channel.history(limit=None, oldest_first=True):
                f.write(
                    "[{0}] {1.author} ({1.author.id}){2}: {1.content}\n".format(
                        message.created_at.strftime('%Y %b %d %H:%M:%S'),
                        message, ' (attachment)' if message.attachments else '',
                    )
                )
                attachments.extend(message.attachments)

        files = [transcript]

        for i, attach in enumerate(attachments):
            name = f"attachment{str(i)}-{record['id']}" + os.path.splitext(attach.filename)[1]
            await attach.save(name)
            files.append(name)

        return files

    @ticket.command(name='close')
    @ticket_only()
    @is_mod()
    @commands.max_concurrency(1, per=commands.cooldowns.BucketType.guild, wait=True)
    async def ticket_close(self, ctx, *, reason=None):
        """Close the ticket and create an archive. The reason should be a summary."""

        query = 'SELECT * from tickets WHERE channel_id=$1;'
        record = await ctx.db.fetchrow(query, ctx.channel.id)

        if not record:
            return

        query = 'UPDATE tickets SET state=$1 WHERE channel_id=$2'
        await ctx.db.execute(query, TicketState.closed.value, record['channel_id'])

        await ctx.send('Creating logs please do not send any messages, this may take a while.')

        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(
                read_messages=True,
                send_messages=False
            )
        }
        await ctx.channel.edit(
            overwrites=overwrites,
            reason='Locking ticket while creating logs as to not disrupt.'
        )

        message = await self.status_channel.fetch_message(record['status_message_id'])
        embed = message.embeds[0]

        embed.description = reason
        embed.colour = Colour.apricot()

        ticket = 'Ticket #{}{}'.format(
            record['id'], ' - {}'.format(record['issue']) if record['issue'] else ''
        )
        files = await self._generate_log(ctx.channel, record)
        jumps = ''
        for attachment in files[1:]:  # The log comes afterwards
            # Embed fields cannot exceed 1024 characters, so we need to split
            # the jump URLs before this happens.
            if len(jumps) > 800:
                embed.add_field(
                    name='Attachments',
                    value=jumps,
                    inline=False
                )
                jumps = ''

            msg = await self.log_channel.send(
                f'Attachment from **{ticket}**',
                file=discord.File(attachment, filename=attachment)
            )
            jumps += f'[Jump: {attachment}]({msg.jump_url})\n'

            os.remove(attachment)

        if jumps:  # There's some jump URLs to send
            embed.add_field(
                name='Attachments',
                value=jumps,
                inline=False
            )

        transcript = await self.log_channel.send(
            f"Transcription from **{ticket}**",
            file=discord.File(files[0], filename=files[0])
        )
        embed.add_field(name='Log', value=f'[Jump!]({transcript.jump_url})')

        embed.set_footer(
            text=f'{ctx.author} ({ctx.author.id})',
            icon_url=ctx.author.avatar_url
        )

        await message.edit(embed=embed)

        await ctx.channel.delete(
            reason='Closing ticket #{0} because: {1}'.format(record['id'], reason)
        )


def setup(bot):
    bot.add_cog(TicketManager(bot))

import asyncio
import enum
import re

import discord
from discord.ext import commands
from steam.steamid import steam64_from_url

from cogs.utils import Colour, is_mod

# Regex to match a link, see comments for example
re_link = re.compile(
    r'(?:https?:\/\/)?' +  # https://
    r'(?:www\.)?' +  # www.
    r'[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}' +  # youtube.com
    r'(?:[-a-zA-Z0-9()@:%_\+.~#?&\/=]*)'  # /watch?v=123
)


def report_only():
    async def predicate(ctx):
        if ctx.guild is None:
            return False

        query = """SELECT EXISTS (
                SELECT 1 FROM reports WHERE channel_id=$1 LIMIT 1
            );
        """
        return bool(await ctx.db.fetchval(query, ctx.channel.id))
    return commands.check(predicate)


class ReportState(enum.Enum):
    open = 0
    closed = 1


class ReportManager(commands.Cog):
    """Cog managing all report tickets for reporting players."""
    def __init__(self, bot):
        self.bot = bot

        self._category = None
        self._evidence_channel = None
        self._status_channel = None

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

    @property
    def category(self) -> discord.CategoryChannel:
        if not self._category:
            self._category = self.bot.get_channel(self.bot.settings.report_category)
        return self._category

    @property
    def evidence_channel(self) -> discord.TextChannel:
        if not self._evidence_channel:
            self._evidence_channel = self.bot.get_channel(
                self.bot.settings.report_evidence_channel
            )
        return self._evidence_channel

    @property
    def status_channel(self):
        if not self._status_channel:
            self._status_channel = self.bot.get_channel(
                self.bot.settings.report_status_channel
            )
        return self._status_channel

    async def get_open_by_author(self, author_id):
        return await self.bot.pool.fetchval(
            'SELECT channel_id FROM reports WHERE author_id=$1 AND state=$2',
            author_id, ReportState.open.value
        )

    async def create_report(self, author: discord.Member, *, conn=None):
        conn = conn or self.bot.pool

        report_id: int = await conn.fetchval("SELECT nextval('report_id');")

        overwrites = {
            author: discord.PermissionOverwrite(
                read_messages=True
            )
        }
        overwrites.update(self.category.overwrites)

        channel = await self.category.create_text_channel(
            name='{0}-{1}'.format(
                report_id, author.display_name
            ),
            sync_permissions=True, overwrites=overwrites,
            reason='Creating report #{0} ({1}) for {2}'.format(
                report_id, report_id, author.display_name
            )
        )

        query = """INSERT INTO reports (
                    id, channel_id, author_id
                ) VALUES ($1, $2, $3) RETURNING *;
        """
        record = await conn.fetchrow(query, report_id, channel.id, author.id)

        await channel.send(
            'Welcome {0}'.format(author.mention),
            embed=discord.Embed(
                description=self.open_message,
                colour=Colour.light_blue(),
            )
        )

        embed = discord.Embed(
            title=f"Report #{record['id']}",
            colour=Colour.cyan()
        )

        embed.set_author(name=author, icon_url=author.avatar_url)

        message = await self.status_channel.send(embed=embed)

        await conn.execute(
            'UPDATE reports SET status_message_id=$1 WHERE id=$2',
            message.id, record['id']
        )

        return channel, record

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.message_id != self.bot.settings.report_message:
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
                open_channel, f'<@{payload.user_id}> you already have an open report in here.'
            )
            await asyncio.sleep(10)
            return await self.bot.http.delete_message(open_channel, msg['id'])

        await self.create_report(payload.member)

    @commands.Cog.listener()
    async def on_message(self, message):
        """Automatically move messages into their reports"""

        if message.channel.id != self.bot.settings.report_player_channel:
            return
        # Ignore the bot itself
        if message.author.bot:
            return

        open_channel = await self.get_open_by_author(message.author.id)
        if open_channel:
            destination = self.bot.get_channel(open_channel)
        else:
            # create_report returns the channel and the ticket record, we want the channel
            destination = (await self.create_report(message.author))[0]

        webhook = None
        for wh in await destination.webhooks():
            if wh.user.id == self.bot.user.id:  # Look for the webhook we created
                webhook = wh

        # Create a new webhook if none exists
        webhook = webhook or await destination.create_webhook(
            name=f'Mimic {message.author.display_name} in report'
        )

        # Create a list of files, or None if the list is empty
        files = [await attachment.to_file() for attachment in message.attachments] or None

        await webhook.send(
            message.content,
            username=message.author.display_name,
            avatar_url=message.author.avatar_url,
            files=files
        )

        await message.delete()  # Delete the original message

        # Ping the user in the report to remind them of it
        msg = await self.bot.http.send_message(destination.id, message.author.mention)
        await asyncio.sleep(10)
        await self.bot.http.delete_message(destination.id, msg['id'])

    @commands.group(invoke_without_command=True)
    async def report(self, ctx, *, issue=None):
        """Open a report. Parent command for report ticket management."""
        # Ignore moderators, so it isn't accidentally used
        if isinstance(ctx.author, discord.Member) and \
                ctx.author.guild_permissions.manage_roles:
            return

        await ctx.invoke(self.report_open, issue=issue)

    @report.command(name='open', aliases=['openas'])
    async def report_open(self, ctx, user: discord.Member = None):
        """Open a report ticket."""
        author = ctx.author
        if user:
            if isinstance(ctx.author, discord.Member) and \
                    ctx.author.guild_permissions.manage_roles:
                author = user
            else:
                return  # Doesn't have permission to open a report as someone

        await ctx.message.delete()

        open_channel = await self.get_open_by_author(author.id)
        if open_channel:
            return await ctx.send('{0} already has an open report: <#{1}>'.format(
                    author.mention, open_channel
                ), delete_after=10
            )

        channel, _ = await self.create_report(author, conn=ctx.db)

        await ctx.send(f'Opened report in {channel.mention}.')

    async def _lock_channel(self, channel):
        await channel.send('Locked the channel. Saving evidence, this may take a while.')

        overwrites = {
            channel.guild.default_role: discord.PermissionOverwrite(
                read_messages=False
            ),
            self.bot.user: discord.PermissionOverwrite(
                read_messages=True
            )
        }
        await channel.edit(
            overwrites=overwrites,
            reason='Locking report while downloading evidence.'
        )

    async def _gather_evidence(self, channel):
        """Find all attachments and links in a channel"""

        attachments, found_links = [], []  # Short for declaring two lists
        async for message in channel.history(limit=None, oldest_first=True):
            # Make sure the regex doesn't end with a )
            found_links.extend(
                m[:-1] if m.endswith(')') else m for m in re.findall(re_link, message.content)
            )
            attachments.extend(message.attachments)

        steamids, links = set(), []
        for link in found_links:
            if 'steamcommunity' not in link:
                links.append(link)
            else:
                # We're gonna handle these later
                steamids.add(steam64_from_url(link))

        for steamid in steamids:
            if steamid is None:
                continue

            links.append(f'https://www.steamcommunity.com/profiles/{steamid}/')

        return attachments, links

    @report.command(name='close')
    @report_only()
    @is_mod()
    async def report_close(self, ctx, *, reason=''):
        """Close the report. The reason should be a summary."""

        query = 'SELECT * from reports WHERE channel_id=$1;'
        record = await ctx.db.fetchrow(query, ctx.channel.id)

        if not record:
            return

        query = 'UPDATE reports SET state=$1 WHERE channel_id=$2;'
        await ctx.db.execute(query, ReportState.closed.value, record['channel_id'])

        # For older reports before this change that don't have a status message
        if record['status_message_id'] is None:
            return await ctx.channel.delete(
                reason='Closing report #{0}'.format(record['id'])
            )

        await self._lock_channel(ctx.channel)

        message = await self.status_channel.fetch_message(record['status_message_id'])
        embed = message.embeds[0]

        embed.description = reason
        embed.colour = Colour.apricot()

        evidence, links = await self._gather_evidence(ctx.channel)

        if links:
            embed.add_field(
                name='Links',
                value='\n'.join(links),
            )

        if evidence:
            jumps = ''
            for attachment in evidence:
                msg = await self.evidence_channel.send(
                    f"Evidence for **Report #{record['id']}**",
                    file=await attachment.to_file()
                )
                jumps += f'[Jump: {attachment.filename}]({msg.jump_url})\n'

            embed.add_field(
                name='Attachments',
                value=jumps,
            )

        embed.set_footer(
            text=f'{ctx.author} ({ctx.author.id})',
            icon_url=ctx.author.avatar_url
        )

        await message.edit(embed=embed)

        await ctx.channel.delete(
            reason='Closing report #{0}'.format(record['id'])
        )


def setup(bot):
    bot.add_cog(ReportManager(bot))

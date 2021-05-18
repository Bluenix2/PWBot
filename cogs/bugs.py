import re
from io import StringIO, BytesIO
import csv

import discord
from discord.ext import commands

from cogs.utils import is_mod


class BugReporter(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True, aliases=['bug'])
    @is_mod()
    async def bugs(self, ctx, name, *, info=None):
        """Parent command for bug reporting, shortcut for `?bugs report`"""
        return await ctx.invoke(self.report, name, info=info)

    @bugs.command()
    @is_mod()
    async def report(self, ctx, name, *, info=None):
        """Make a new report for a bug"""

        msg = None

        if info:
            # Try to identify a message link
            re_match = re.search(
                r'https:\/\/discord\.com\/channels\/[0-9]+\/[0-9]+\/[0-9]+', info
            )
            if re_match:
                msg = info[re_match.start():re_match.end()]
                info = info.replace(msg, '')

        # Use the message link above or use the invoked message's one
        msg = msg or ctx.message.jump_url

        if await ctx.db.fetchval(
                'SELECT name FROM bugs WHERE name=$1 AND archived=TRUE;', name):
            return await ctx.send(f'{name} is archived, pick another name for a new bug.')

        # This is done to combat accidental typos
        elif not await ctx.db.fetchval('SELECT name FROM bugs WHERE name=$1 LIMIT 1;', name):
            # Make sure they want to continue
            question = ('There are no other reports of the same bug, ' +
                        'are you sure you want to continue?')
            if not await ctx.prompt(question):
                return await ctx.send('Cancelled.')

        # If we've reached this far we definitly want to insert the bug report
        count = await ctx.db.fetchval("""
            INSERT INTO bugs (name, message_link, info) VALUES ($1, $2, $3)
            RETURNING (
                SELECT COUNT(*) FROM bugs WHERE name = $1
            );
        """, name, msg, info or None)

        await ctx.send(f'Recorded report, there has now been {count + 1} reports so far.')

    @bugs.command()
    @is_mod()
    async def dump(self, ctx, all_records: bool = False):
        """Dump all reported bugs, by default only reports the counts"""
        if all_records:
            query = 'SELECT * FROM bugs WHERE archived = FALSE;'
        else:
            query = 'SELECT name, COUNT(name) FROM bugs WHERE archived = FALSE GROUP BY name;'

        dump = StringIO()
        writer = csv.writer(dump)

        conn = await ctx.acquire()
        async with conn.transaction():
            async for record in conn.cursor(query):
                writer.writerow(list(record.values()))

        await ctx.release()

        dump.seek(0)

        buffer = BytesIO()
        buffer.write(dump.getvalue().encode())
        buffer.seek(0)

        await ctx.send(
            'Dumped all non-archived bugs',
            file=discord.File(buffer, filename='bugs.csv')
        )

    @bugs.command()
    @commands.is_owner()
    async def archive(self, ctx, name):
        """Archive a specific bug"""

        if not await ctx.prompt(f'Are you sure you want to archive all {name} bugs?'):
            return await ctx.send('Cancelled.')

        await ctx.db.execute('UPDATE bugs SET archived = TRUE WHERE name = $1;', name)

        return await ctx.send(f'Archived bug {name}')


def setup(bot):
    bot.add_cog(BugReporter(bot))

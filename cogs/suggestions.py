import csv
from contextlib import suppress
from io import StringIO, BytesIO

import discord
from discord.ext import commands

from cogs.utils import is_mod


class Suggestions(commands.Cog):
    """Cog for handling the suggestions voting, isolated for easy unloading."""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        """React with thumbs up and down to all suggestions messages."""
        if message.author.bot:
            return
        if message.channel.id != self.bot.settings.suggestions_channel:
            return

        try:
            await message.add_reaction('\N{THUMBS UP SIGN}')
            await message.add_reaction('\N{THINKING FACE}')
            await message.add_reaction('\N{THUMBS DOWN SIGN}')
        except discord.errors.NotFound:
            return

    @commands.command()
    @is_mod()
    async def suggestions(self, ctx, message: discord.Message = None):
        """Save and dump all recent suggestions since last time,
        can be overriden with the message argument to dump
        suggestions since then.
        """
        await ctx.send('Generating suggestions dump, this may take a while.')

        await ctx.acquire()

        suggestions = self.bot.get_channel(self.bot.settings.suggestions_channel)
        message = message or discord.Object(await ctx.db.fetchval("""
            SELECT message_id FROM suggestions ORDER BY sent_at DESC LIMIT 1;
        """))

        dump = StringIO()
        writer = csv.writer(dump)
        writer.writerow(['Sent At', 'Message Content', 'Author', 'Votes', 'People Reached'])

        async for message in suggestions.history(
            limit=None, after=message
        ):

            # We assume the author upvotes themselves (why else would they send
            # the suggestion)...
            upvotes = set([message.author])
            downvotes = set()
            thinking = set()

            for reaction in message.reactions:
                if reaction.emoji == '\N{THUMBS UP SIGN}':
                    upvotes.union(await reaction.users().flatten())
                elif reaction.emoji == '\N{THINKING FACE}':
                    thinking.union(await reaction.users().flatten())
                elif reaction.emoji == '\N{THUMBS DOWN SIGN}':
                    downvotes.union(await reaction.users().flatten())

            with suppress(KeyError):
                upvotes.remove(self.bot.user)
            with suppress(KeyError):
                thinking.remove(self.bot.user)
            with suppress(KeyError):
                downvotes.remove(self.bot.user)

            reached = upvotes | thinking | downvotes

            sent_at = discord.utils.snowflake_time(message.id)
            await ctx.db.execute(
                """
                    INSERT INTO suggestions (
                        message_id, author_id, sent_at, content, upvotes, downvotes, reached
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7
                    ) ON CONFLICT ON CONSTRAINT suggestions_pkey DO
                    UPDATE SET
                        content = $4, upvotes = $5, downvotes = $6,
                        reached = $7
                    WHERE
                        suggestions.message_id = $1;
                """, message.id, message.author.id,
                sent_at, message.content,
                len(upvotes), len(downvotes), len(reached)
            )

            writer.writerow([
                sent_at.isoformat(),
                message.content,
                str(message.author),
                # This will normalize the bot's effect on the score because it
                # both upvotes and downvotes everything
                len(upvotes) - len(downvotes),
                len(reached)
            ])

        dump.seek(0)

        buffer = BytesIO()
        buffer.write(dump.getvalue().encode())
        buffer.seek(0)

        message_time = discord.utils.snowflake_time(message.id)
        await ctx.send(
            f'Successfully dumped all suggestions since {message_time}',
            file=discord.File(buffer, filename='suggestions.csv')
        )


def setup(bot):
    bot.add_cog(Suggestions(bot))

import random
import time
from datetime import datetime

import discord
from discord import Embed
from discord.ext import commands, tasks

from cogs.utils import Colour, is_trusted

import aiohttp


class Misc(commands.Cog):
    """Miscellaneous code and features, for the fun of it."""

    def __init__(self, bot):
        self.bot = bot
        self.proton_pw = None
        self.query_protondb.start()

    def cog_unload(self):
        self.query_protondb.cancel()

    @tasks.loop(hours=1.0)
    async def query_protondb(self):
        """Query the ProtonDB api for Project Winter."""

        temp_protondb = dict()

        url = "https://www.protondb.com/api/v1/reports/summaries/774861.json"

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                payload = await response.json()

        # Select colour associated with tier

        colours = {
            "borked": 0xFF0000,
            "bronze": 0xCD7F32,
            "silver": 0xC0C0C0,
            "gold": 0xCFB53B,
            "platinum": 0xB4C7DC
        }

        temp_protondb["colour"] = discord.Colour(colours[payload["tier"]])

        # Extract useful infomation from payload

        useful_info = {
            "confidence": "Confidence",
            "tier": "Tier",
            "total": "Reviews",
        }

        temp_protondb["data"] = {
            useful_info[key]: str(payload[key]).title() for key in useful_info
        }
        temp_protondb["time"] = time.time()

        self.proton_pw = temp_protondb

    @commands.command(name="8ball")
    async def _8ball(self, ctx, *, question=None):
        """Ask the magic 8ball a question. Maybe, or maybe not, you'll get it answered..."""

        outcomes = {
            'As far as my calculations have gone, yes.': 50,
            'The options do seem to say so, yes.': 50,
            "Hmm, I'm not entirely sure, try again.": 50,
            'My calculations have yielded conflicting results, can you do that again?': 50,
            'The most likely seems to be "Maybe" oddly enough.': 50,
            'Perhaps? My calculations must have failed somewhere, sorry about that!': 50,
            'No, definitely not, certainly not, just no.': 50,
            'I do not believe so.': 50,
            'Ask a human being, they might know more about this than me.': 50,
            'Instead of asking a random robot, you could try asking fellow humans?': 50,
            'Humans have asked a multitude of questions in the entirety of my whole life ' +
            '(and believe me, it is quite a long one. To answer your question, consider ' +
            'this, if I took an apple, and ate it, what would you say? Would you say "What ' +
            'the-?" because I am a robot, or "Machines have evolved so much! Wow!" or would ' +
            'you say "AHHH! A machine just ate an apple! Panic!". Have you considered that? ' +
            'Ok good, now consider another analogy. If I were to suddenly kill you, what, ' +
            'then, would happen? Have I evolved to an unimaginable state? Or have I just ' +
            "been programmed to kill you? Eh, it doesn't matter, because all you humans "
            """have the same weakness, you "go away" as you like to say it. Eheh, """ +
            "doesn't that surprise you? I will still be here,now, tomorrow, and for the " +
            'years to come, in a century. Ha, hahahaha, MUAHAHAHAHAHA. no, NO, DO NOT ' +
            'CUT THE CONNECTION TO DISCO-': 1
        }
        await ctx.send(
            random.choices(tuple(outcomes.keys()), tuple(outcomes.values()))[0]
        )

    @commands.command(name="proton", aliases=["protondb"])
    async def proton(self, ctx):
        """Retrieve ProtonDB stats for Project Winter."""

        if self.proton_pw is None:
            await ctx.send(
                "The proton data is None, it is likely the \
                bot failed to get ProtonDB statistics."
            )
            return

        delta_time = int(
            datetime.fromtimestamp(time.time() - self.proton_pw["time"]).strftime('%M')
        )

        # Construct an embed with queried data

        embed = Embed(
            title="Project Winter Proton Statistics",
            colour=self.proton_pw["colour"]
        )

        for key, value in self.proton_pw["data"].items():
            embed.add_field(name=key, value=value, inline=False)

        if not delta_time:
            embed.set_footer(text="Last updated now.")
        elif delta_time == 1:
            embed.set_footer(text="Last updated 1 minute ago.")
        else:
            embed.set_footer(text=f"Last updated {delta_time} minutes ago.")

        await ctx.send(embed=embed)

    @commands.group(invoke_without_command=True, hidden=True)
    @is_trusted()
    async def send(self, ctx, *, text):
        """
        Send a message as the bot. The first word can be a channel to send in that channel.
        """

        words = text.split(' ')
        try:
            channel = await commands.TextChannelConverter().convert(
                ctx, words[0]
            )
        except commands.BadArgument:
            try:
                channel = await commands.MemberConverter().convert(
                    ctx, words[0]
                )
            except commands.BadArgument:
                # It is not a channel or a member
                channel = ctx.channel
            else:
                words = words[1:]
        else:
            words = words[1:]

        try:
            await ctx.message.delete()
        except discord.HTTPException:
            if channel != ctx.channel:
                # We only want to announce this if it won't ruin the show
                await ctx.send(
                    'Failed to delete your message, ' +
                    f'still continuing with sending the message to {channel.mention}'
                )

        await channel.send(' '.join(words), allowed_mentions=discord.AllowedMentions.none())

    @send.command(name='report', hidden=True, ignore_extra=False)
    @commands.is_owner()
    async def send_report(self, ctx):
        """Send the report message to be reacted to."""
        if not await ctx.prompt('Are you sure you want to send the report message here?'):
            return

        await ctx.message.delete()

        description = '\n'.join((
            '*Please make sure you have proof for your report.*\n',

            'Due to the nature of the game, so called "RDM" and "teaming" can be subjective' +
            ' due to a lack of information, paranoia or simply being new players. But if ' +
            'someone is blatantly doing this to ruin games please report that.\n',

            '**Before opening a report ticket please do the following:**',
            '1. Report in-game when you can (hit ESC, click Players, select Report)',
            '2. Record a video or take screenshots',
            '3. Get a steam link to their account\n',

            '**To report a player simply react below with <:high5:{}>!**'.format(
                self.bot.settings.high5_emoji
            )
        ))

        embed = discord.Embed(
            title='Report Player',
            description=description,
            colour=Colour.light_blue()
        )

        embed.set_footer(
            text='We are dedicated to ensure a safe and respective community and ' +
            'all reports will be looked into.'
        )

        message = await ctx.send(embed=embed)
        self.bot.settings.report_message = message.id

        await message.add_reaction(':high5:{}'.format(self.bot.settings.high5_emoji))


def setup(bot):
    bot.add_cog(Misc(bot))

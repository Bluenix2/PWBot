import discord
from discord.ext import commands

from cogs.utils import checks, colours


class Responses(commands.Cog):
    """Cog for common responses to issues."""

    def __init__(self, bot):
        self.bot = bot

    @commands.group(
        invoke_without_command=True,
        hidden=True)
    @checks.trusted()
    async def send(self, ctx, *, text):
        """Send a message as the bot.
        The first word can be a channel to send in that channel.
        """
        await ctx.message.delete()
        words = text.split(' ')

        try:
            channel = await commands.TextChannelConverter().convert(
                ctx, words[0]
            )
        except commands.BadArgument:
            channel = ctx.channel
        else:
            words = words[1:]

        await channel.send(' '.join(words), allowed_mentions=discord.AllowedMentions.none())

    @send.command(
        name='report',
        hidden=True,
        ignore_extra=False)
    @commands.is_owner()
    async def send_report(self, ctx):
        await ctx.message.delete()

        description = '\n'.join((
            '*Please make sure you have proof for your report.*\n',

            'Due to the nature of the game, so called "RDM" and "teaming" can be subjective due to a lack of information, paranoia '
            'or simply being new players. But if someone is blatantly doing this to ruin games please report that.\n',

            '**Before opening a report ticket please do the following:**',
            '1. Report in-game when you can (hit ESC, click Players, select Report)',
            '2. Record a video or take screenshots',
            '3. Get a steam link to their account\n',

            '**To report a player simply react below with <:high5:{}>!**'.format(self.bot.settings.high5_emoji)
        ))

        embed = discord.Embed(
            title='Report Player',
            description=description,
            colour=colours.light_blue()
        )

        embed.set_footer(text='We are dedicated to ensure a safe and respective community and all reports will be looked into.')

        message = await ctx.send(embed=embed)
        self.bot.settings.report_message = message.id

        await message.add_reaction(':high5:{}'.format(self.bot.settings.high5_emoji))

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        if message.channel.id != self.bot.settings.suggestions_channel:
            return

        await message.add_reaction('\N{THUMBS DOWN SIGN}')
        await message.add_reaction('\N{THUMBS UP SIGN}')


def setup(bot):
    bot.add_cog(Responses(bot))

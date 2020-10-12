from datetime import datetime

import discord
from dateutil.relativedelta import relativedelta
from discord.ext import commands


class PWBotHelp(commands.HelpCommand):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def send_bot_help(self, mapping):
        bot = self.context.bot
        all_commands = await self.filter_commands(bot.commands, sort=True)

        embed = discord.Embed(
            title='All commands',
            colour=discord.Colour.blue(),
        )
        for command in all_commands:
            embed.add_field(
                name=self.get_command_signature(command), value=command.brief,
                inline=False
            )

        await self.get_destination().send(embed=embed)

    async def send_command_help(self, command):
        await self.get_destination().send(embed=discord.Embed(
            title=command.name,
            description='`{0}` {1}'.format(
                self.get_command_signature(command),
                command.help,
            ),
            colour=discord.Colour.blue(),
            )
        )

    async def send_group_help(self, group):
        all_commands = await self.filter_commands(group.commands, sort=True)

        embed = discord.Embed(
            title=group.name,
            description='`{0}` {1}'.format(
                self.get_command_signature(group),
                group.help,
            ),
            colour=discord.Colour.blue(),
            )

        for command in all_commands:
            embed.add_field(
                name=self.get_command_signature(command), value=command.brief,
                inline=False
            )

        await self.get_destination().send(embed=embed)

    async def send_error_message(self, error):
        return  # Do nothing


class Meta(commands.Cog):
    """Utilities for the bot itself."""
    def __init__(self, bot):
        self.bot = bot

    @commands.command(brief='Say how long the bot has been up for.')
    async def uptime(self, ctx):
        delta = relativedelta(
            datetime.utcnow().replace(microsecond=0),
            self.bot.uptime.replace(microsecond=0),
        )
        await ctx.send(
            'I have been working for **{} weeks, {} days, {} hours, {} minutes.**'.format(
                delta.weeks, (delta.days - delta.weeks * 7), delta.hours, delta.minutes
            )
        )


def setup(bot):
    bot.add_cog(Meta(bot))

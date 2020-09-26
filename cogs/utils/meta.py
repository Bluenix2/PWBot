import discord
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
                name=self.get_command_signature(command), value=command.brief, inline=False
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

    async def send_error_message(self, error):
        return  # Do nothing

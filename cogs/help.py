import discord
from discord.ext import commands


class Help(commands.Cog):
    """Cog solely for the help command."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def help(self, ctx):
        embed = discord.Embed(
            title="Commands",
            colour=discord.Colour.blue(),
        )

        embed.add_field(
            name="ticket <issue>",
            value="Create a private ticket with the Mod team.",
            inline=False
        )
        embed.add_field(
            name="report",
            value="Open a private channel with the Mod team to report",
            inline=False
        )

        embed.add_field(
            name="lobby <players>",
            value="Send a message, that can be reacted to, to find players",
            inline=False
        )
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Help(bot))

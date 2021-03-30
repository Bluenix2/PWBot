import pygsheets
import discord
from discord.ext import commands

from cogs import utils


class Events(commands.Cog):
    """Event specific code, for improving management of events."""
    def __init__(self, bot):
        self.bot = bot

        self.client = pygsheets.authorize(service_file="cogs/gsheets.json")
        self.sheet = self.client.open_by_key("1UBH9Gwi9a-0miAChmb-Ecet9BhDZ0egIvymteONxYBQ").worksheet_by_title("Submissions")

        self.answered = dict()

    @utils.is_mod()
    @commands.command(hidden=True)
    async def event_reset(self, ctx, user: discord.Member):
        self.answered[user.id] = 0
        await ctx.send('\N{OK HAND SIGN}')

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild:
            return

        if message.content.startswith('?') or message.author.bot:
          return

        if self.answered.get(message.author.id, 0) > 10:
            self.answered[message.author.id] += 1
            return

        elif self.answered.get(message.author.id, 0) == 10:
            self.answered[message.author.id] += 1
            return await message.channel.send('You have been blocked from making more submissions for spam, if you think this was a mistake please contact a Community Manager.')

        content = message.content + " " + " ".join([attach.url for attach in message.attachments])
        id_ = "ID:" + str(message.author.id)

        self.sheet.insert_rows(2, 1, [str(message.author), id_, content], True)

        if message.author.id in self.answered:
            self.answered[message.author.id] += 1
            return await message.add_reaction('\N{THUMBS UP SIGN}')

        embed = discord.Embed(
            title='Thank you for your submission!',
            description='Please **do not** delete your message, it deletes *the image too*. While you may only make one submission, if you change your mind you can send more images. Only the most recent image as of closing submissions will be counted for though.',
            colour=utils.Colour.light_blue())
        await message.channel.send(embed=embed)

        self.answered[message.author.id] = 1


def setup(bot):
    bot.add_cog(Events(bot))

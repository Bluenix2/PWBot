from discord.ext import commands


class Submission:
    """Represents a submission to the October Costume Contest"""

    def __init__(self, message, voters):
        self.message = message
        self.voters = voters


class Events(commands.Cog):
    """Event specific code, for improving management of events."""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.channel.id != 651109293663191061:
            return

        await message.add_reaction(':survivor:500377451592155137')

    @commands.command(name='countevent', brief='Count votes on current ongoing event.')
    @commands.is_owner()
    async def count_event(self, ctx):
        event_channel = self.bot.get_channel(651109293663191061)
        event_message = await event_channel.fetch_message(770775667817185312)

        submissions = []
        async for submission in event_channel.history(after=event_message):
            vote = None
            for reaction in submission.reactions:
                if str(reaction) == '<:survivor:500377451592155137>':
                    vote = reaction
            if not vote:
                continue

            voters = []
            async for voter in vote.users():
                if voter.id == submission.author.id or voter.id == self.bot.client_id:
                    continue

                voters.append(voter)

            submissions.append(Submission(submission, voters))

        def key(elem):
            return len(elem.voters)
        submissions.sort(key=key, reverse=True)

        lines = ['```']
        for submission in submissions[:14]:  # Only top 15 submissions
            lines.append('{}   {}: {}'.format(
                submission.message.author, len(submission.voters),
                submission.message.jump_url
            ))
        lines.append('```')

        await ctx.send('\n'.join(lines))


def setup(bot):
    bot.add_cog(Events(bot))

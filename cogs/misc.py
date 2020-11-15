import random

from discord.ext import commands


class Misc(commands.Cog):
    """Miscellaneous code and features, for the fun of it."""

    def __init__(self, bot):
        self.bot = bot

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


def setup(bot):
    bot.add_cog(Misc(bot))

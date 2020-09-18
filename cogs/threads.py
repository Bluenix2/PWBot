import discord
from discord.ext import commands


class Threads(commands.Cog):
    """Commands for creating, opening and managing threads."""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.message_id not in (756608926157504633, 756608932641898517):
            return

        # Use raw method to avoid unnecessary API calls
        await self.bot.http.remove_reaction(
            payload.channel_id, payload.message_id,
            payload.emoji, payload.member.id
        )

        if str(payload.emoji) != '\N{WHITE MEDIUM STAR}':  # Will be changed
            return

        if payload.message_id == 756608926157504633:
            await self.create_ticket(self.bot.get_user(payload.user_id))
        elif payload.message_id == 756608932641898517:
            await self.create_report(self.bot.get_user(payload.user_id))

    async def create_ticket(self, user, issue=""):
        category = self.bot.get_channel(755833939997884568)

        description = """Welcome {0}

        Thank you for opening a ticket, what can we help you with?
        Please explain what you need help with and we will get back with you.

        Please use the following command to close the ticket:
        `-ticket close <reason for closing here>`

        And use the following command to add a user to the ticket:
        `-ticket add <@user>`
        """

        await self._create_thread(
            user, category, "ticket-{0}", description, issue
        )

    async def create_report(self, user, issue=""):
        category = self.bot.get_channel(756603865805357217)

        description = """Welcome {0}

        Thank you for reporting, please provide all evidence.
        Examples of good evidence is video proof and screenshots.
        Please also post their or your Steam link.

        Please use the following command to close the report:
        `-report close <reason for closing here>`

        And use the following command to add a user to the report:
        `-report add <@user>`
        """

        await self._create_thread(
            user, category, "report-{0}", description, issue
        )

    async def _create_thread(
        self, user, category, channel_format, description, issue
    ):
        """Create a new thread."""

        overwrites = {
            user: discord.PermissionOverwrite(
                read_messages=True
            )
        }
        overwrites.update(category.overwrites)

        channel = await category.create_text_channel(
            name=channel_format.format(issue), sync_permissions=True,
            overwrites=overwrites,
        )

        await channel.send(user.mention, embed=discord.Embed(
            description=description.format(user.mention),
            colour=discord.Colour.greyple()
        ))

    @commands.group(aliases=["ticket", "report"], invoke_without_command=True)
    async def thread(self, ctx, *, message=None):
        """Parent to all ticket commands.

        Also opens a ticket to help inexperienced users.
        """
        # Redirect to opening a ticket
        await ctx.invoke(self.thread_create, message=message)

    @thread.command(name="create", aliases=["open"])
    async def thread_create(self, ctx, *, message=None):
        """Opens a thread, giving both author and mod team access."""
        if ctx.invoked_with.startswith('ticket'):
            await self.create_ticket(ctx.author, message)
        elif ctx.invoked_with.startswith('report'):
            await self.create_report(ctx.author, message)

    @thread.command(name="close")
    async def thread_close(self, ctx):
        """Closes a thread, deleting the channel."""
        await ctx.channel.delete()


def setup(bot):
    bot.add_cog(Threads(bot))

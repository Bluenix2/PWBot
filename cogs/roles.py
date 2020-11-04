import enum

import discord
from discord.ext import commands


class RoleType(enum.Enum):
    ping = 0
    language = 1


class Roles(commands.Cog):
    """Manages reaction roles for both language and ping roles."""
    def __init__(self, bot):
        self.bot = bot

        self._role_channel = None

    @property
    def messages(self):
        # Defining it directly means it doesn't get changed
        # when the setting gets set, this is a work-around
        return {
            self.bot.settings.pings_message: RoleType.ping,
            self.bot.settings.language_message: RoleType.language,
        }

    @property
    def role_channel(self):
        if not self._role_channel:
            self._role_channel = self.bot.get_channel(self.bot.settings.role_channel)
        return self._role_channel

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        role_type = self.messages.get(payload.message_id)
        # The message is not pings_message or language_message
        if not role_type:
            return

        if payload.user_id == self.bot.client_id:
            return

        query = 'SELECT role_id FROM roles WHERE reaction=$1 AND type=$2;'
        role_id = await self.bot.pool.fetchval(query, str(payload.emoji), role_type.value)
        if not role_id:
            # Someone reacted with an emoji that wasn't set up for *this message*.
            # We remove it as to clarify what emojis actually work.
            return await self.bot.http.remove_reaction(
                payload.channel_id, payload.message_id,
                payload.emoji._as_reaction(), payload.user_id
            )

        await self.bot.http.add_role(payload.guild_id, payload.user_id, role_id)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        role_type = self.messages.get(payload.message_id)
        # The message is not pings_message or language_message
        if not role_type:
            return

        query = 'SELECT role_id FROM roles WHERE reaction=$1 AND type=$2;'
        role_id = await self.bot.pool.fetchval(query, str(payload.emoji), role_type.value)
        if not role_id:
            # At this point it was the bot that removed the reaction ( see above ),
            # so we just ignore because there is no role to remove.
            return

        await self.bot.http.remove_role(payload.guild_id, payload.user_id, role_id)

    async def _add_role(self, emoji, role, role_type, field, message_id, *, conn=None):
        if not conn:
            conn = self.bot.pool
        name, description = field.split('|')

        query = """INSERT INTO roles (
                    reaction, name, role_id, type, description
                ) VALUES ($1, $2, $3, $4, $5) RETURNING *;
        """
        record = await conn.fetchrow(query, emoji, name, role.id, role_type.value, description)

        message = await self.role_channel.fetch_message(message_id)

        message.embeds[0].add_field(
            name=record['name'],
            value=record['description'],
            inline=True
        )
        await message.edit(embed=message.embeds[0])

        await message.add_reaction(record['reaction'].strip('<>'))

    async def _remove_role(self, emoji, message_id, role_type, *, conn=None):
        if not conn:
            conn = self.bot.pool

        query = 'DELETE FROM roles WHERE reaction=$1 AND type=$2 RETURNING *;'
        record = await conn.fetchrow(query, emoji, role_type.value)
        message = await self.role_channel.fetch_message(message_id)

        index = [em.name for em in message.embeds[0].fields].index(record['name'])
        message.embeds[0].remove_field(index)

        await message.edit(embed=message.embeds[0])

        await message.clear_reaction(emoji.strip('<>'))

    @commands.group(invoke_without_command=True, brief='Manage language roles')
    @commands.is_owner()
    async def language(self, ctx):
        # This is only meant as a container for the language roles management
        await ctx.send_help('language')  # We send help for this group

    @language.command(
        name='add',
        brief='Add a new language role to the embed',
        help='Add a new language role to the embed, field splits by `name|description`.')
    # We already check for owner in our parent
    async def language_add(self, ctx, emoji, role: discord.Role, *, field):
        await self._add_role(
            emoji, role, RoleType.language,
            field, self.bot.settings.language_message,
            conn=ctx.db
        )

    @language.command(name='remove', brief='Remove a language role from the embed')
    # We already check for owner in our parent
    async def language_remove(self, ctx, emoji):
        await self._remove_role(
            emoji, self.bot.settings.language_message,
            conn=ctx.db
        )

    @commands.group(invoke_without_command=True, brief='Manage ping roles')
    @commands.is_owner()
    async def pings(self, ctx):
        # This is only meant as a container for the ping roles management
        await ctx.send_help('pings')  # We send help for this group

    @pings.command(
        name='add',
        brief='Add a new ping role to the embed',
        help='Add a new ping role to the embed, field will be split by `name|description`.')
    # We already check for owner in the parent command
    async def pings_add(self, ctx, emoji, role: discord.Role, *, field):
        await self._add_role(
            emoji, role, RoleType.ping,
            field, self.bot.settings.pings_message,
            conn=ctx.db
        )

    @pings.command(name='remove', brief='Remove a language role from the embed')
    # We already do a check for bot owner
    async def pings_remove(self, ctx, emoji):
        await self._remove_role(
            emoji, self.bot.settings.pings_message,
            conn=ctx.db
        )


def setup(bot):
    bot.add_cog(Roles(bot))

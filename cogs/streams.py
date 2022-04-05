import asyncio
from datetime import datetime, timedelta, timezone

import discord
from discord.ext import commands, tasks


class Streams(commands.Cog):
    """Cog for streams-and-promotions management."""

    def __init__(self, bot):
        self._streams_channel = None

        self.streamers = {}
        self.announcement_lock = asyncio.Lock()
        self.guilds = {}

        self.bot = bot

        # TODO: Uncomment this and reload the bot to start cleaning. Because of
        # deployment issues I don't want to clear the channel again
        #     self.clear_channel.start()

    @property
    def streams_channel(self) -> discord.TextChannel:
        if not self._streams_channel:
            self._streams_channel = self.bot.get_channel(
                self.bot.settings.stream_announcement_channel
            )
        return self._streams_channel

    def cog_unload(self):
        self.clear_channel.cancel()

    async def grab_guild(self, guild_id: int) -> discord.Guild:
        """Get or fetch the guild by its ID.

        This method houses a custom cache for guilds if possible because during
        testing the discord.py cache was not always complete.
        """
        guild = self.guilds.get(guild_id)
        if guild:
            return guild

        guild = self.bot.get_guild(guild_id)
        if not guild:
            guild = await self.bot.fetch_guild(guild_id)

        self.guilds[guild_id] = guild
        return guild

    @tasks.loop(hours=168.0)
    async def clear_channel(self):
        """Clear the streams channel every week."""
        channel = self.bot.get_channel(self.bot.settings.streams_channel)

        if channel is None:
            return

        await channel.guild.chunk()
        pins = await channel.pins()

        def check(msg):
            return msg not in pins

        await channel.purge(limit=None, check=check)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.channel != self.streams_channel:
            return

        if message.channel.is_news():
            await message.publish()

    # Thanks to how discord.py works, we want need to dig deep to get the
    # actual information we're looking for. We could get this information using
    # on_member_update() event but we won't know whether the status changed or
    # another change was made.

    @commands.Cog.listener()
    async def on_socket_response(self, data):
        if not data.get('t') == 'PRESENCE_UPDATE':
            return

        d = data['d']

        stream_url = None
        for activity in d['activities']:
            if activity.get('type') == 1 and activity.get('state') == 'Project Winter':
                stream_url = activity.get('url')
                break

        if stream_url is None:
            return

        user = d['user']
        user_id = user['id']

        async with self.announcement_lock:
            if (
                user_id in self.streamers and (
                    datetime.now(timezone.utc) - self.streamers[user_id]
                ) < timedelta(hours=12)
            ):
                return  # Already announced this stream

            guild = await self.grab_guild(d['guild_id'])

            member = guild.get_member(user_id)
            if not member:
                await guild.chunk()
                member = guild.get_member(user_id)
                if not member:
                    member = await guild.fetch_member(user_id)

            for role_id in [role.id for role in member.roles]:
                if role_id in self.bot.settings.streamer_roles:
                    break
            else:
                return  # Not a streamer we want to announce

            self.streamers[user_id] = datetime.now(timezone.utc)

        await self.streams_channel.send(
            self.bot.settings.stream_announcement.format(
                user=user, url=stream_url
            ),
            allowed_mentions=discord.AllowedMentions(roles=True)
        )


def setup(bot):
    bot.add_cog(Streams(bot))

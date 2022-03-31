import json

import discord
from discord.ext import commands, tasks


class Streams(commands.Cog):
    """Cog for streams-and-promotions management."""

    def __init__(self, bot):
        self._streams_channel = None

        self.bot = bot

        self.clear_channel.start()

    @property
    def streams_channel(self) -> discord.TextChannel:
        if not self._streams_channel:
            self._streams_channel = self.bot.get_channel(self.bot.settings.streams_channel)
        return self._streams_channel

    def cog_unload(self):
        self.clear_channel.cancel()

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

    # Thanks to how discord.py works, we want need to dig deep to get the
    # actual information we're looking for. We could get this information using
    # on_member_update() event but we won't know whether the status changed or
    # another change was made.

    @commands.Cog.listener()
    async def on_socket_response(self, data):
        if not data.get('t') == 'PRESENCE_UPDATE':
            return

        print('status changed', data['d']['activities'])

        d = data['d']

        guild = self.bot.get_guild(d['guild_id'])
        if guild:
            member = guild.get_member(d['user']['id'])
            if member:
                # on_socket_raw_receive is dispatched before any other event is,
                # which means that this member object hasn't been affected by this
                # event. We can take advantage of discord.py's cache while
                # narrowing it down to knowing that the presence changed.
                for activity in member.activities:
                    if isinstance(activity, discord.Streaming):
                        return  # Already streaming before this event

        stream_url = None
        for activity in d['activities']:
            if activity.get('type') == 1 and activity.get('state') == 'Project Winter':
                stream_url = activity.get('url')
                break

        if stream_url is None:
            return

        await self.streams_channel.send(
            self.bot.settings.stream_announcement.format(user=d['user']['id'], url=stream_url)
        )


def setup(bot):
    bot.add_cog(Streams(bot))

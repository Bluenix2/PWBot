import asyncio
import datetime
import time

import discord
from discord.ext import commands

from cogs.utils import Colour


class ModLogging(commands.Cog):
    """Logging listeners for moderation actions."""
    def __init__(self, bot):
        self.bot = bot
        self._automod_channel = None

    @property
    def automod_channel(self):
        if not self._automod_channel:
            self._automod_channel = self.bot.get_channel(self.bot.settings.automod_channel)
        return self._automod_channel

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        timestamp = datetime.datetime.utcnow()

        if member.joined_at is None:
            return

        await asyncio.sleep(1)

        log = None
        limit_timestamp = datetime.datetime.utcfromtimestamp(time.time() - 60)

        # This has a little bit higher treshold because there is no garuantee to find the log.
        guild = member.guild
        async for entry in guild.audit_logs(action=discord.AuditLogAction.kick, limit=25):
            if member.joined_at > entry.created_at or entry.created_at < limit_timestamp:
                # We've missed it, or it's not there
                break

            if entry.target == member:
                log = entry
                break

        if not log:
            return

        embed = discord.Embed(
            title='Member Kicked',
            description=f'{member} (ID: {member.id})',
            colour=Colour.apricot(),
            timestamp=timestamp,
        )
        embed.set_thumbnail(url=member.avatar_url)

        embed.set_author(
            name=f'{log.user.display_name} (ID: {log.user.id})',
            icon_url=log.user.avatar_url
        )

        if log.reason:
            embed.add_field(name='Reason', value=log.reason)

        await self.automod_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):

        timestamp = datetime.datetime.utcnow()

        await asyncio.sleep(1)

        log = None
        limit_timestamp = datetime.datetime.utcfromtimestamp(time.time() - 60)

        async for entry in guild.audit_logs(action=discord.AuditLogAction.ban, limit=10):
            if entry.target == user and entry.created_at > limit_timestamp:
                log = entry
                break

        embed = discord.Embed(
            title='Member Banned',
            description=f'{user} (ID: {user.id})',
            colour=Colour.unvaulted_red(),
            timestamp=timestamp,
        )
        embed.set_thumbnail(url=user.avatar_url)

        if log:
            embed.set_author(
                name=f'{log.user.display_name} (ID: {log.user.id})',
                icon_url=log.user.avatar_url
            )

            if log.reason:
                embed.add_field(name='Reason', value=log.reason)

        await self.automod_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        timestamp = datetime.datetime.utcnow()

        await asyncio.sleep(1)

        log = None
        limit_timestamp = datetime.datetime.utcfromtimestamp(time.time() - 60)

        async for entry in guild.audit_logs(action=discord.AuditLogAction.ban, limit=10):
            if entry.target == user and entry.created_at > limit_timestamp:
                log = entry
                break

        embed = discord.Embed(
            title='Member Unbanned',
            description=f'{user} (ID: {user.id})',
            colour=Colour.light_blue(),
            timestamp=timestamp,
        )
        embed.set_thumbnail(url=user.avatar_url)

        if log:
            embed.set_author(
                name=f'{log.user.display_name} (ID: {log.user.id})',
                icon_url=log.user.avatar_url
            )

            if log.reason:
                embed.add_field(name='Reason', value=log.reason)

        await self.automod_channel.send(embed=embed)


def setup(bot):
    bot.add_cog(ModLogging(bot))

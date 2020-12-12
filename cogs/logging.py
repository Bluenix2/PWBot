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
        if member.joined_at is None:
            return

        # Like above we want to try to find the audit log for the action.
        # Difference here is that there is no garuantee to find any entry at all,
        # whereas above you *should* always find a log.

        # Before the wait and audit log stuff
        timestamp = datetime.datetime.utcnow()

        # Give Discord some time to update, like a grace perioud.
        await asyncio.sleep(1)

        log = None
        limit_timestamp = datetime.datetime.utcfromtimestamp(time.time() - 60)

        # This has a little bit higher treshold than the ban.
        guild = member.guild
        async for entry in guild.audit_logs(action=discord.AuditLogAction.kick, limit=25):
            if member.joined_at > entry.created_at or entry.created_at < limit_timestamp:
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
        # We want to find the audit log for the action, to get all info.

        # Before the wait and audit log stuff
        timestamp = datetime.datetime.utcnow()

        # We give Discord some time to update its audit logs, to ensure it's there
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

        # Let's give Discord some grace perioud to update its audit logs.
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

import discord
from discord.ext import commands


def is_mod():
    async def predicate(ctx):
        return isinstance(ctx.author, discord.Member) and \
            ctx.author.guild_permissions.manage_roles

    return commands.check(predicate)


def is_trusted():
    async def predicate(ctx):
        return isinstance(ctx.author, discord.Member) and \
            ctx.author.guild_permissions.manage_messages

    return commands.check(predicate)


def ignore_report_webhooks():
    async def predicate(ctx):
        if ctx.message.webhook_id:
            return False

        if ctx.channel.id == ctx.bot.settings.report_player_channel:
            return False

        return True
    return commands.check(predicate)

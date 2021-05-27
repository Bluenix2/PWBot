import discord
from discord.ext import commands


def is_mod():
    async def predicate(ctx):
        return isinstance(ctx.author, discord.Member) and \
            ctx.author.guild_permissions.manage_role

    return commands.check(predicate)


def is_trusted():
    async def predicate(ctx):
        return isinstance(ctx.author, discord.Member) and \
            ctx.author.guild_permissions.manage_messages

    return commands.check(predicate)

from discord.ext import commands


def is_mod():
    async def predicate(ctx):
        permissions = ctx.author.guild_permissions
        return permissions.manage_messages
    return commands.check(predicate)

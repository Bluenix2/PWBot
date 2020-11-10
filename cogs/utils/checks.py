from discord.ext import commands


def mod_only():
    async def predicate(ctx):
        permissions = ctx.author.guild_permissions
        return permissions.manage_roles
    return commands.check(predicate)


def trusted():
    async def predicate(ctx):
        permissions = ctx.author.guild_permissions
        return permissions.manage_messages
    return commands.check(predicate)


def confirm(message):
    async def predicate(ctx):
        result = await ctx.prompt(message)
        # result may also be None, and we need to return a bool
        return True if result else False
    return commands.check(predicate)

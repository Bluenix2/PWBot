import asyncpg
from discord.ext import commands

from cogs.utils import checks


class TagName(commands.clean_content):
    """A converter to convert the argument to an acceptable tag name."""
    async def convert(self, ctx, argument):
        # Convert it like clean_content, then make lowercase,
        # and also strip leading and trailing spaces.
        converted = (await super().convert(ctx, argument)).lower().strip()

        if not converted:  # Nothing left
            raise commands.BadArgument('Missing tag name.')

        if len(converted) > 50:
            raise commands.BadArgument('Tag name too long, max is 50 charaters.')

        # We want to get the first word, to see if it's already a command.
        first_word, _, _ = converted.partition(' ')

        return converted


class Tags(commands.Cog):
    """Tag related management commands."""

    def __init__(self, bot):
        self.bot = bot

    @commands.group(
        invoke_without_command=True,
        brief='Manage tags, forcefully send a tag.',
        help='Parent command to tag management, forcefully send a tag.')
    @checks.mod_only()
    async def tag(self, ctx, *, name: TagName):
        try:
            await ctx.send_tag(name)
        except commands.CommandNotFound:
            return  # Do nothing, we don't care

    @tag.command(name='create', brief='Create a new tag and content.')
    async def tag_create(self, ctx, name: TagName, *, content):
        try:
            async with (await ctx.db.acquire()).transaction():
                content_id = await self.bot.create_content(content, conn=ctx.db)
                await self.bot.create_tag(name, content_id, conn=ctx.db)
        except asyncpg.UniqueViolationError:
            await ctx.send('This tag already exists!')
        except Exception:
            await ctx.send('Something went wrong!')
        else:
            await ctx.send('Tag and content successfully created.')

    @tag.command(name='add', brief='Add a new tag/alias', aliases=['alias'])
    async def tag_add(self, ctx, name: TagName, alias: TagName):
        await ctx.db.acquire()

        content_id = await ctx.db.fetchval('SELECT content_id FROM tags WHERE name=$1', name)

        try:
            await self.bot.create_tag(alias, content_id, conn=ctx.db)
        except asyncpg.UniqueViolationError:
            await ctx.send('This tag/alias already exists!')
        except Exception:
            await ctx.send('Something went wrong!')
        else:
            await ctx.send('Tag successfully created.')

    @tag.command(name='remove', brief='Safely remove a tag, but keep the content.')
    async def tag_remove(self, ctx, name: TagName):
        prompt = ('Are you sure you want to safely remove this tag? This will keep ' +
                  'the content and other aliases.')
        if not await ctx.prompt(prompt):
            return

        await ctx.acquire()

        # We really don't want to remove the last tag
        content_id = await ctx.db.fetchval('SELECT content_id FROM tags WHERE name=$1', name)

        query = 'SELECT id, name FROM tags WHERE content_id=$2 AND name<>$1 LIMIT 1;'
        other_tag = await ctx.db.fetchrow(query, name, content_id)
        if other_tag:
            # We found another tag, so let's do like told and remove the one specified
            await ctx.db.execute('DELETE FROM tags WHERE name=$1', name)
            await ctx.send(f"Tag removed, but you can still use `{other_tag['name']}`. ")
        else:
            await ctx.send(
                f'This is the last alias to content `#{content_id}`, use `?ticket delete`.'
            )

    @tag.command(
        name='delete', brief='Delete a tag and its content.',
        help='Delete a tag and its content, this will also remove all other aliases.')
    async def tag_delete(self, ctx, name: TagName):
        prompt = ("Are you sure you want to completely remove this tags' " +
                  "content and all other aliases?")
        if not await ctx.prompt(prompt):
            return

        await ctx.acquire()

        content_id = await ctx.db.fetchval('SELECT content_id FROM tags WHERE name=$1', name)

        await ctx.db.execute('DELETE FROM tag_content WHERE id=$1;', content_id)

        await ctx.send('This content and all its tags are now fully removed!')


def setup(bot):
    bot.add_cog(Tags(bot))

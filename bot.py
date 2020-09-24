import datetime
import sys
import traceback

from discord.ext import commands

import config
from cogs.utils import context, settings

initial_extensions = (
    'cogs.admin',
    'cogs.threads',
    'cogs.lobby',
)


class PWBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='?', fetch_offline_members=False)

        self.client_id = config.client_id
        self.uptime = None

        self.settings = settings.Settings()

        for extension in initial_extensions:
            try:
                self.load_extension(extension)
            except commands.ExtensionError:
                print(f'Failed to load extension {extension}', file=sys.stderr)
                traceback.print_exc()

    async def on_ready(self):
        if not hasattr(self, 'uptime'):
            self.uptime = datetime.datetime.utcnow()

        print(f'Ready: {self.user} (ID: {self.user.id})')

    async def process_commands(self, message):
        ctx = await self.get_context(message, cls=context.Context)

        try:
            await self.invoke(ctx)
        finally:
            # In case we have any outstanding database connections
            await ctx.release()

    def run(self):
        super().run(config.token, reconnect=True)

import datetime
import sys
import traceback

from discord.ext import commands

import config

initial_extensions = (
    'cogs.admin',
    'cogs.threads',
)


class PWBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="?", fetch_offline_members=False)

        for extension in initial_extensions:
            try:
                self.load_extension(extension)
            except Exception:
                print(f'Failed to load extension {extension}', file=sys.stderr)
                traceback.print_exc()

    async def on_ready(self):
        if not hasattr(self, 'uptime'):
            self.uptime = datetime.datetime.utcnow()

        print(f'Ready: {self.user} (ID: {self.user.id})')

    def run(self):
        super().run(config.token, reconnect=True)

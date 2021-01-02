import asyncio
import traceback

import asyncpg
import click

import config
from bot import PWBot


def run_bot():
    bot = PWBot()
    bot.run()


@click.group(invoke_without_command=True, options_metavar='[options]')
@click.pass_context
def main(ctx):
    """Launch the bot."""
    if ctx.invoked_subcommand is None:
        run_bot()


if __name__ == '__main__':
    main()

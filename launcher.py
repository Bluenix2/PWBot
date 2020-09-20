import asyncio
import sys
import traceback

import asyncpg
import click

import config
from bot import PWBot


def run_bot():
    loop = asyncio.get_event_loop()
    try:
        pool = loop.run_until_complete(asyncpg.create_pool(config.postgresql))
    except Exception:
        click.echo('Failed set up PostgreSQL pool, exiting', file=sys.stderr)
        return
    bot = PWBot()
    bot.pool = pool
    bot.run()


@click.group(invoke_without_command=True, options_metavar='[options]')
@click.pass_context
def main(ctx):
    """Launches the bot."""
    if ctx.invoked_subcommand is None:
        run_bot()


@main.group(options_metavar='[options]')
def database():
    """Parent to all database related command line functions."""
    pass


@database.command(options_metavar='[options]')
def init():
    click.echo('Creating tables')
    run = asyncio.get_event_loop().run_until_complete

    conn = run(asyncpg.connect(config.postgresql))

    tables = [
        """CREATE TABLE IF NOT EXISTS threads (
            id BIGINT PRIMARY KEY,
            author BIGINT NOT NULL,
            state SMALLINT NOT NULL
        );
        """,
    ]

    for table in tables:
        try:
            run(conn.execute(table))
        except Exception:
            click.echo(
                'Failed to create table\n' + traceback.format_exc(), err=True
            )


if __name__ == '__main__':
    main()

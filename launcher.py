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
    """Launch the bot."""
    if ctx.invoked_subcommand is None:
        run_bot()


@main.group(options_metavar='[options]')
def database():
    """Parent to all database related command line functions."""
    pass


@database.command(options_metavar='[options]')
def init():
    click.echo('Setting up database')
    run = asyncio.get_event_loop().run_until_complete

    conn = run(asyncpg.connect(config.postgresql))

    queries = [
        """CREATE TABLE IF NOT EXISTS tickets (
            id SMALLINT PRIMARY KEY,
            channel_id BIGINT UNIQUE NOT NULL,
            author_id BIGINT NOT NULL,
            type SMALLINT,
            state SMALLINT DEFAULT 0,
            status_message_id BIGINT,
            issue VARCHAR(90)
        );
        """,
        """CREATE SEQUENCE IF NOT EXISTS ticket_id OWNED BY tickets.id;""",
        """CREATE INDEX IF NOT EXISTS tickets_duplicate_idx ON tickets (
            author_id, state, type
        );
        """,

        """CREATE TABLE IF NOT EXISTS roles (
            reaction VARCHAR PRIMARY KEY,
            name VARCHAR(256),
            role_id BIGINT UNIQUE NOT NULL,
            type SMALLINT,
            description VARCHAR(1024)
        );
        """,
        """CREATE INDEX IF NOT EXISTS roles_idx ON roles (reaction, type);"""
    ]

    for query in queries:
        try:
            run(conn.execute(query))
        except Exception:
            click.echo(
                'Failed to execute query\n' + traceback.format_exc(), err=True,
            )


if __name__ == '__main__':
    main()

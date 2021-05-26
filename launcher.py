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
            state SMALLINT DEFAULT 0,
            status_message_id BIGINT,
            issue VARCHAR
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
        """CREATE INDEX IF NOT EXISTS roles_idx ON roles (reaction, type);""",

        """CREATE SEQUENCE IF NOT EXISTS content_ids;""",
        # All content for the tags
        """CREATE TABLE IF NOT EXISTS tag_content (
            id SMALLINT PRIMARY KEY DEFAULT NEXTVAL('content_ids'),
            value VARCHAR(2000) NOT NULL,
            created_at TIMESTAMP DEFAULT (NOW() AT TIME ZONE 'UTC'),
            uses INT DEFAULT 0
        );
        """,
        """ALTER SEQUENCE content_ids OWNED BY tag_content.id;""",
        """CREATE UNIQUE INDEX IF NOT EXISTS content_id_idx ON tag_content (id);""",
        """CREATE SEQUENCE IF NOT EXISTS tag_ids;""",
        # The pointers to the content, this means there is no distinction
        # between "aliases", and the "original" tag.
        """CREATE TABLE IF NOT EXISTS tags (
            id SMALLINT PRIMARY KEY DEFAULT NEXTVAL('tag_ids'),
            content_id SMALLINT REFERENCES tag_content (id)
                ON DELETE CASCADE ON UPDATE NO ACTION,
            name VARCHAR(50) UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT (NOW() AT TIME ZONE 'UTC')
        );
        """,
        """ALTER SEQUENCE tag_ids OWNED BY tags.id;""",
        """CREATE UNIQUE INDEX IF NOT EXISTS tags_name_idx ON tags (name);""",
        """CREATE INDEX IF NOT EXISTS tag_content_id_idx ON tags (content_id);""",
        """CREATE TABLE IF NOT EXISTS bugs (
            id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,  -- Just to have a primary key
            name TEXT NOT NULL,
            message_link TEXT,
            info TEXT,
            created_at TIMESTAMP DEFAULT (NOW() AT TIME ZONE 'UTC'),
            archived BOOLEAN DEFAULT FALSE
        );
        """,
        """CREATE INDEX IF NOT EXISTS bugs_archived_idx ON bugs (archived);""",
        """CREATE TABLE IF NOT EXISTS reports (
            id SMALLINT PRIMARY KEY,
            channel_id BIGINT UNIQUE NOT NULL,
            author_id BIGINT NOT NULL,
            state SMALLINT DEFAULT 0
        );
        """,
        """CREATE SEQUENCE IF NOT EXISTS report_id OWNED BY reports.id;""",
        """CREATE INDEX IF NOT EXISTS reports_duplicate_idx ON reports (author_id, state);""",
    ]

    for query in queries:
        try:
            run(conn.execute(query))
        except Exception:
            click.echo(
                'Failed to execute query\n' + traceback.format_exc(), err=True,
            )


@database.command(options_metavar='[options]')
def migrate():
    """Migrate from the last version.

    To migrate between multiple version you'll need to run each
    version's migration in ascending order.
    """
    click.echo('Migrating database.')

    run = asyncio.get_event_loop().run_until_complete

    conn = run(asyncpg.connect(config.postgresql))

    queries = [
        """CREATE TABLE suggestions (
            message_id BIGINT PRIMARY KEY,
            author_id BIGINT NOT NULL,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            content VARCHAR(2000) NOT NULL,
            upvotes INT DEFAULT 1,
            downvotes INT DEFAULT 1
        );""",
        """ALTER TABLE tickets DROP COLUMN type"""
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

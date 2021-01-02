# PWBot

The Project Winter bot

## Setting up and Running

### 1. Get Python 3

This is required to run any part of the bot.

### 2. Set up a Python venv

Simply run `python3 -m venv venv`, then activate it and install the dependencies with `pip install -U -r requirements.txt`.

### 4. Create the database in PostgreSQL

Now you'll need PostgreSQL and inside the `psql` tool run the following to create a user and database. You may want to edit the password.

```sql
CREATE ROLE pwbot WITH LOGIN PASSWORD 'yourpw';
CREATE DATABASE pwbot OWNER pwbot;
```

After that connect to the database with the user you created, and then execute the setup file.

```sql
\c "dbname=pwbot username=pwbot"
\i setup.sql
```

### 4. Set up configuration

Create a new file, `config.py` in the root directory, and use the following template

```py
client_id = 0  # Bot's client ID
token = ''  # Bot's token
postgresql = 'postgresql://pwbot:yourpw@localhost/pwbot'  # Your PostgreSQL info from above
```

Additionally a json file named `settings.json` will be needed. This allows the bot to save certain data past restart.

See `cogs/utils/settings.py` for keys which need to be defined in the json file.

## Migrating

To make migrating the database to newer versions as easy as possible a migration script is included.
This can be ran with the `psql` tool, see the following:

```sql
\c "dbname=pwbot username=pwbot"
\i migrate.sql
```

## Requirements

- Python 3
- PostgreSQL
- discord.py
- asyncpg
- click
- flake8
- dateutil

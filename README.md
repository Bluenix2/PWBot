## PWBot

The Project Winter bot

## Running

1. **Get Python 3**

This is the required version.

2. **Set up venv**

Simply do `python3 -m venv venv`

3. **Install dependencies**

`pip install -U -r requirements.txt`

4. **Create the database in PostgreSQL**

You will need PostgreSQL installed and then type this in the `psql` tool:
```
CREATE ROLE pwbot WITH LOGIN PASSWORD 'yourpw';
CREATE DATABASE pwbot OWNER pwbot;
```

4. **Set up configuration**

Create a new file, `config.py` in the root directory, 
and use the following template:

```py
client_id = ''  # Bot's client ID
token = ''  # Bot's token
postgresql = 'postgresql://pwbot:yourpw@localhost/pwbot'  # Your PostgreSQL info from above
```

## Requirements

- Python 3
- discord.py
- asyncpg
- click

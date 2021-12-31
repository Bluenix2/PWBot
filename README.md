## PWBot

The Project Winter bot

## Running

1. **Get Python 3**

This is the required version.

2. **Install Poetry**

Poetry will be used to manage dependencies and assure that the code will work with the dependancies.
Installation can be done with `pip install poetry`.

3. **Install dependencies**

To install the dependencies simply run `poetry install`.

4. **Create the database in PostgreSQL**

You will need PostgreSQL installed and then type this in the `psql` tool:
```
CREATE ROLE pwbot WITH LOGIN PASSWORD 'yourpw';
CREATE DATABASE pwbot OWNER pwbot;
```

5. **Set up configuration**

Create a new file, `config.py` in the root directory, 
and use the following template:

```py
client_id = 0  # Bot's client ID
token = ''  # Bot's token
postgresql = 'postgresql://pwbot:yourpw@localhost/pwbot'  # Your PostgreSQL info from above
```

Additionally a json file named `settings.json` will be needed.
This allows the bot to save certain data past restart

See `cogs/utils/settings.py` for keys which need to be defined
in the json file.

Name the Google Sheets API key json file `gsheets.json` and place it under cogs.

6. **Starting the bot**
To start the bot you start the postgres database then run `poetry run python launch.py`

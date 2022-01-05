## PWBot

The Project Winter bot

## Running

Docker is recommended for deployment and development as it means that all requirements and
dependencies stay the same, but the bot runs perfectly fine without it.

1. **Set up configuration**

Create a new file, `config.py` in the root directory, and use the following template:

```py
client_id = 0  # Bot's client ID
token = ''  # Bot's token
postgresql = 'postgresql://postgres:postgres@postgres/pwbot'  # Your PostgreSQL info
weather_key = '' # Your weather api key
```

Additionally a json file named `settings.json` will be needed. This allows the bot to save
certain data past restart

See `cogs/utils/settings.py` for keys which need to be defined in the json file.

Name the Google Sheets API key json file `gsheets.json` and place it under cogs.

2. **Install dependencies**

If you use plan on using Docker you can skip this step.

Poetry is used to manage dependencies, it can be installed with `pip install poetry`.
Then install the real project dependencies with `poetry install`.

Lastly, you will need PostgreSQL installed and type this into the `psql` tool:
```
CREATE ROLE pwbot WITH LOGIN PASSWORD 'yourpw';
CREATE DATABASE pwbot OWNER pwbot;
```

Make sure to adjust the `postgresql` variable in `config.py`. It should most likely be:
```python
postgresql = 'postgresql://pwbot:yourpw@localhost/pwbot'
```

3. **Starting the bot**

Using Docker, simply start the bot with `docker-compose up` (or any variatons such as
`sudo docker-compose up` or `docker compose up`).

Without Docker, make sure PostgreSQL is running then execute `poetry run python launcher.py`

4. **Creating database tables**

When the bot starts and is able to connect to the database, open another able process before
running any commands. Run the following command:
```python
# For Docker (replace `pwbot_bot_1` with container name)
docker exec -it pwbot_bot_1 poetry run python launcher.py database init
# For non-Docker setup
poetry run python launcher.py database init
```

When later upgrading run the migrate script with:
```python
# For Docker (replace `pwbot_bot_1` with container name)
docker exec -it pwbot_bot_1 poetry run python launcher.py database migrate
# For non-Docker setup
poetry run python launcher.py database migrate
```

## PWBot

The Project Winter bot

## Running

1. **Install docker and docker-compose**

View [docker](https://www.docker.com/) and [docker compose](https://docs.docker.com/compose/install/)

2. **Set up configuration**

Create a new file, `config.py` in the root directory, 
and use the following template:

```py
client_id = 0  # Bot's client ID
token = ''  # Bot's token
postgresql = 'postgresql://postgres:postgres@database/pwbot'  # Your PostgreSQL info from above
weather_key = '' # Your weather api key
```

Additionally a json file named `settings.json` will be needed.
This allows the bot to save certain data past restart

See `cogs/utils/settings.py` for keys which need to be defined
in the json file.

Name the Google Sheets API key json file `gsheets.json` and place it under cogs.

3. **Starting the bot**

To start the bot you start the postgres database then run `docker-compose up` or any variations such as `sudo docker-compose up` or `docker compose up`

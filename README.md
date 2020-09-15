## PWBot

The Project Winter bot

## Running

1. **Get Python 3**

This is the required version.

2. **Set up venv**

Simply do `python3 -m venv venv`

3. **Install dependencies**

`pip install -U -r requirements.txt`

4. **Set up configuration**

Create a new file, `config.py` in the root directory, 
and use the following template:

```py
client_id = ''  # Bot's client ID
token = ''  # Bot's token
```

## Requirements

- Python 3
- discord.py
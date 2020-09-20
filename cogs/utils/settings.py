import json


class Settings:
    def __init__(self):
        with open('settings.json', 'r') as f:
            settings = json.load(f)
        self.__dict__.update(settings)

    def __setattr__(self, name, value):
        self.__dict__[name] = value
        with open('settings.json', 'w') as f:
            json.dump(self.__dict__, f)

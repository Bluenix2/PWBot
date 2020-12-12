import discord


class Colour(discord.Colour):
    """Custom Clour class with additional colours
    taken from the game.
    """

    @classmethod
    def cyan(cls):
        return cls(0x63C1B1)

    @classmethod
    def light_blue():
        return discord.Colour(0x65A3E6)

    @classmethod
    def red():
        return discord.Colour(0xA62A2A)

    @classmethod
    def unvaulted_red():
        return discord.Color(0xE03D51)

    @classmethod
    def apricot():
        return discord.Colour(0xE16859)

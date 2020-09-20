import discord
from discord.ext import commands


class Lobby:
    """Represents a waiting beta lobby."""

    def __init__(self, message, required_players):
        self.required_players = required_players

        self.message = message
        self.players = set()


class LobbyManager(commands.Cog):
    """Cog for managing waiting beta lobbies."""

    def __init__(self, bot):
        self.bot = bot

        self.lobbies = set()

    @commands.Cog.listener()  # TODO: Add beta channel check
    async def on_raw_reaction_add(self, payload):
        if payload.user_id == self.bot.client_id:     # ignore the bot's reacts
            return

        if str(payload.emoji) != '\N{WHITE MEDIUM STAR}':  # TODO: Change
            return

        lobby = None
        for _lobby in self.lobbies:
            if _lobby.message.id == payload.message_id:
                lobby = _lobby

        if lobby is None:
            return

        lobby.players.add(payload.user_id)

        if lobby.required_players == len(lobby.players):
            await lobby.message.clear_reactions()
            await lobby.message.channel.send(
                "You have enough players to start a game! " + ", ".join(
                    "<@{0}>".format(player) for player in lobby.players
                )
            )

            description = "This lobby reached the desired amount of players"
            await lobby.message.edit(embed=discord.Embed(
                title="Lobby Full!",
                description=description,
                colour=discord.Colour.orange()
            ))

    @commands.command()
    async def lobby(self, ctx, players: int):
        if players < 5 or players > 8:
            return

        message = await ctx.send(embed=discord.Embed(
            title="Looking for players!",
            description="If you are available for a game, react below.",
            colour=discord.Colour.green()
        ))

        self.lobbies.add(Lobby(message, players))

        await message.add_reaction("\N{WHITE MEDIUM STAR}")


def setup(bot):
    bot.add_cog(LobbyManager(bot))

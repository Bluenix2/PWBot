import asyncio

import discord
from discord.ext import commands

from cogs.utils import colours


def beta_channel_only():
    async def predicate(ctx):
        return ctx.channel.id == ctx.bot.settings.beta_channel
    return commands.check(predicate)


class Lobby:
    """Represents a waiting beta lobby."""

    def __init__(self, manager, owner_id, message, required_players):
        self.manager = manager
        self.owner_id = owner_id
        self.required_players = required_players

        self.message = message
        self.players = set()

        async def timeout(timeout=21600):
            await asyncio.sleep(timeout)
            await self.disband(True)

        self.timeout = asyncio.create_task(timeout())

    async def disband(self, timeout=False):
        if not timeout:
            self.timeout.cancel()

        self.manager.lobbies.remove(self)
        await self.message.channel.send(
            '<@{0}> your lobby was disbanded.'.format(
                self.owner_id
            )
        )

        description = 'This lobby was disbanded.'
        await self.message.edit(embed=discord.Embed(
            title='Lobby Disbanded!',
            description=description,
            colour=colours.unvaulted_red(),
        ))


class LobbyManager(commands.Cog):
    """Cog for managing waiting beta lobbies."""

    def __init__(self, bot):
        self.bot = bot

        self.lobbies = set()

    def get_lobby_by_owner(self, owner_id):
        for _lobby in self.lobbies:
            if _lobby.owner_id == owner_id:
                return _lobby

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.channel_id != self.bot.settings.beta_channel:
            return

        if payload.user_id == self.bot.client_id:     # ignore the bot's reacts
            return

        if payload.emoji.id != self.bot.settings.high5_emoji:
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
                'You have enough players to start a game! ' + ', '.join(
                    '<@{0}>'.format(player) for player in lobby.players
                ),
            )
            self.lobbies.remove(lobby)

            description = 'This lobby reached the desired amount of players.'
            await lobby.message.edit(embed=discord.Embed(
                title='Lobby Full!',
                description=description,
                colour=colours.apricot(),
            ))

    @commands.group(
        invoke_without_command=True,
        brief="Open a waiting lobby",
        help="Open a waiting lobby, pinging everyone who reacted when full.")
    @beta_channel_only()
    async def lobby(self, ctx, players: int = 5):
        lobby = self.get_lobby_by_owner(ctx.author.id)

        if lobby:
            return await ctx.send('Please disband your old lobby before opening a new one.')

        if players < 5 or players > 8:
            return

        message = await ctx.send(embed=discord.Embed(
            title='Looking for players!',
            description='If you are available for a game, react below.',
            colour=colours.cyan(),
        ))

        self.lobbies.add(Lobby(self, ctx.author.id, message, players))

        await message.add_reaction('<:high5:{}>'.format(self.bot.settings.high5_emoji))

    @lobby.command(
        name='disband',
        brief='Disband an old lobby')
    @beta_channel_only()
    async def lobby_disband(self, ctx):
        lobby = self.get_lobby_by_owner(ctx.author.id)
        if lobby is None:
            return

        await lobby.disband()


def setup(bot):
    bot.add_cog(LobbyManager(bot))

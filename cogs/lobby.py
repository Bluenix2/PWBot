import asyncio

import discord
from discord.ext import commands

from cogs.utils import colours


def lobby_channel_only():
    async def predicate(ctx):
        return ctx.channel.id in (
            ctx.bot.settings.beta_channel,
            ctx.bot.settings.tournaments_channel
        )
    return commands.check(predicate)


class Lobby:
    """Represents a waiting beta lobby."""

    def __init__(self, manager, owner_id, message, required_players):
        self.manager = manager
        self.owner_id = owner_id
        self.required_players = required_players

        self.message = message
        self.players = set((owner_id,))

        async def timeout(timeout=21600):
            await asyncio.sleep(timeout)
            await self.disband(timeout=True)

        self.timeout = asyncio.create_task(timeout())

    async def disband(self, *, timeout=False):
        if not timeout:
            self.timeout.cancel()

        self.manager.lobbies.remove(self)
        await self.message.clear_reactions()
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
        for lobby in self.lobbies:
            if lobby.owner_id == owner_id:
                return lobby

    def get_lobby_by_message(self, message_id):
        for lobby in self.lobbies:
            if lobby.message.id == message_id:
                return lobby

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.channel_id not in (
                self.bot.settings.beta_channel,
                self.bot.settings.tournaments_channel):
            return

        if payload.user_id == self.bot.client_id:     # ignore the bot's reacts
            return

        if payload.emoji.id != self.bot.settings.high5_emoji:
            return

        lobby = self.get_lobby_by_message(payload.message_id)

        if lobby is None:
            return

        if payload.user_id == lobby.owner_id and lobby.owner_id in lobby.players:
            return await self.bot.http.remove_own_reaction(
                payload.channel_id, payload.message_id,
                ':high5:{}'.format(self.bot.settings.high5_emoji),
            )

        lobby.players.add(payload.user_id)

        if len(lobby.players) == 1:
            await self.bot.http.remove_own_reaction(
                payload.channel_id, payload.message_id,
                ':high5:{}'.format(self.bot.settings.high5_emoji),
            )

        elif lobby.required_players == len(lobby.players):
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

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        if payload.channel_id not in (
                self.bot.settings.beta_channel,
                self.bot.settings.tournaments_channel):
            return

        if payload.user_id == self.bot.client_id:
            return

        if payload.emoji.id != self.bot.settings.high5_emoji:
            return

        lobby = self.get_lobby_by_message(payload.message_id)

        if lobby is None:
            return

        lobby.players.remove(payload.user_id)

        if len(lobby.players) == 0:
            await self.bot.http.add_reaction(
                payload.channel_id, payload.message_id,
                ':high5:{}'.format(self.bot.settings.high5_emoji),
            )

    @commands.group(invoke_without_command=True)
    @lobby_channel_only()
    async def lobby(self, ctx, players: int = 5):
        """
        Open a managed waiting lobby to gather players. This then pings all players when full.
        """
        lobby = self.get_lobby_by_owner(ctx.author.id)

        if lobby:
            return await ctx.send('Please disband your old lobby before opening a new one.')

        if players < 2 or players > 8:
            return

        message = await ctx.send(embed=discord.Embed(
            title='Looking for players!',
            description='If you are available for a game, react below.',
            colour=colours.cyan(),
        ))

        self.lobbies.add(Lobby(self, ctx.author.id, message, players))

        await message.add_reaction(':high5:{}'.format(self.bot.settings.high5_emoji))

    @lobby.command(name='disband')
    @lobby_channel_only()
    async def lobby_disband(self, ctx):
        """Disband an old lobby."""
        lobby = self.get_lobby_by_owner(ctx.author.id)
        if lobby is None:
            return

        await lobby.disband()


def setup(bot):
    bot.add_cog(LobbyManager(bot))

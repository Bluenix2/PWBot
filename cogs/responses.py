from discord.ext import commands


class Responses(commands.Cog):
    """Cog for common responses to issues."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(hidden=True)
    async def log(self, ctx):
        await ctx.send('\n'.join((
            '> Can you grab us your Player.log to help us look into and resolve this issue?',
            '> Copy and paste this address into windows explorer to find it: `C:\\Users\\%username%\\AppData\\LocalLow\\OtherOcean\\ProjectWinter`',
            'https://cdn.discordapp.com/attachments/602287744961609749/641424807107493928/Local-Files.gif'
        )))

    @commands.command(hidden=True)
    async def voip(self, ctx):
        await ctx.send('\n'.join((
            '** Having problems with your voice in chat? Try this: **',
            '> 1. Double check the VOIP capture/playback settings, and set these to your proper headset/mic.'
            "Make sure your recording device is set as the default in Window's Control Panel.",
            '> 2. Ensure you are not using any voice modulating software like Voicemod.',
            '> 3. Ensure you are not behind any firewalls that might block the voice communication.',
            '> 4. Ensure you have the correct **DATE AND TIME** set on your computer.',
            '> 5. Try disabling your IPv6 and reconnecting.\n',

            'If you are still having issues please send us the Player.log file found in'
            '`C:\\Users\\%username%\\AppData\\LocalLow\\OtherOcean\\ProjectWinter` so we can help you further.',
        )))

    @commands.command(hidden=True)
    async def crash(self, ctx):
        await ctx.send('\n'.join((
            '**If you are experiencing crashes please check the following:**',
            '> 1. Install Visual C++ Redistributables (https://support.microsoft.com/en-ca/help/2977003/the-latest-supported-visual-c-downloads)',
            '> 2. Install Directx (https://support.microsoft.com/en-ca/help/179113/how-to-install-the-latest-version-of-directx)',
            '> 3. Install your latest GPU Driver',
            '> 4. If on a laptop, set your GPU performance to "Prefer Maximum Performance '
            '(Right click desktop>  Nvidia control panel > Manage 3D Settings > Power Management Mode >  Prefer Maximum Performance)',
            '> 5. Install any outstanding windows updates',
            '> 6. Ensure you do not have Citrix installed.\n> ',

            '> Project Winter is not supported on Mac or lower speced windows machines.'
            'If your computer does not meet the minimum requirements and your game is crashing,'
            'you can play through GforceNow (https://www.nvidia.com/en-us/geforce-now/).\n> ',

            '> If you are still having issues please send us your Player.log to help us look into and resolve this issue. '
            'Copy and paste this address into windows explorer to find it:  `C:\\Users\\%username%\\AppData\\LocalLow\\OtherOcean\\ProjectWinter`',
        )))

    @commands.command(hidden=True)
    async def disconnect(self, ctx):
        await ctx.send('\n'.join((
            '> If you are having issues with disconnects please ensure you have a good internet connection and change to a wired connection if possible.',
            '> We have basic troubleshooting steps found here: https://steamcommunity.com/app/774861/discussions/0/1841314700716977904/.',
            '> If you are still having issues please provide us with some further information and your logs, '
            'which can be found here: `C:\\Users\\%username%\\AppData\\LocalLow\\OtherOcean\\ProjectWinter`',
        )))

    @commands.command(hidden=True)
    async def input(self, ctx):
        await ctx.send('\n'.join((
            '**Having issues with your cursor being locked? Try the following steps to help fix the issue:**',
            "> 1. Unplug any controller/controller adapter that's connected to your PC.",
            '> 2. Uninstall any virtual controller programs you might have, such as Vjoy',
        )))

    @commands.command(hidden=True)
    async def rdm(self, ctx):
        await ctx.send('\n'.join((
            '> Due to the nature of the game, "RDM" or "teaming" can be subjective due to lack of information, paranoia, new players, etc.'
            'If someone is blatantly doing this to ruin games and you have proof please post it.\n> ',

            "> *The exception to this is Dubem. If you see Dubem in your game feel free to kill him at any time. We don't like Dubem.*",
        )))

    @commands.command(hidden=True)
    async def projectsupreme(self, ctx):
        await ctx.send('\n'.join((
            '> No. This is not the Project Supreme Discord Server. This is Project Winter https://store.steampowered.com/app/774861/Project_Winter/',
            '> Project Winter is an 8 person multiplayer game focusing on social deception and survival.'
            'Communication and teamwork is essential to the survivors’ ultimate goal of escape.',
            '> Gather resources, repair structures, and brave the wilderness together.',
        )))

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        if message.channel.id != self.bot.settings.suggestions_channel:
            return

        await message.add_reaction('\N{THUMBS DOWN SIGN}')
        await message.add_reaction('\N{THUMBS UP SIGN}')


def setup(bot):
    bot.add_cog(Responses(bot))

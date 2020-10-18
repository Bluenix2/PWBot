import discord
from discord.ext import commands

from cogs.utils import checks, colours


class Responses(commands.Cog):
    """Cog for common responses to issues."""

    def __init__(self, bot):
        self.bot = bot

    @commands.group(
        invoke_without_command=True,
        brief='Echo')
    @checks.mod_only()
    async def send(self, ctx, *, text):
        await ctx.message.delete()
        await ctx.send(text)

    @send.command(
        name='roles')
    @commands.is_owner()
    async def send_roles(self, ctx):
        await ctx.message.delete()

        description = """To avoid pinging everyone we've created a few roles to ping instead.

        React to this message to assign the appropriate role.
        If you have any questions feel free to ping a Community Manager
        """
        embed = discord.Embed(
            title='Role Management',
            description=description,
            colour=colours.light_blue()
        )

        embed.add_field(
            name='\N{CHEERING MEGAPHONE} Announcements',
            value='Will get pinged in <#489825441075429378> when the game is updated or the developers have important information to share.',
            inline=False
        )
        embed.add_field(
            name='\N{ADMISSION TICKETS} Events',
            value='Pinged in <#651109293663191061> or <#489825441075429378> when a new event is created, or event details have been released/updated.',
            inline=False
        )
        embed.add_field(
            name='\N{TROPHY} Tournaments',
            value='Pinged in <#647955879844380682> when new community-run tournaments are hosted or information is released/updated.',
            inline=False
        )
        embed.add_field(
            name='\N{GLOBE WITH MERIDIANS} Community Translations',
            value='We are looking to let active community members helps us translate the game.\n**If you want to help please contact a Community Manager**.',
            inline=False
        )

        message = await ctx.send(embed=embed)
        self.bot.settings.reaction_message = message.id

        await message.add_reaction('\N{CHEERING MEGAPHONE}')
        await message.add_reaction('\N{ADMISSION TICKETS}')
        await message.add_reaction('\N{TROPHY}')

    @send.command(
        name='report')
    @commands.is_owner()
    async def send_report(self, ctx):
        await ctx.message.delete()

        description = '\n'.join((
            '*Please make sure you have proof for your report.*\n',

            'Due to the nature of the game, so called "RDM and "teaming" can be subjective due to a lack of information, paranoia '
            'or simply being new players. But if someone is blatantly doing this to ruin games please report that.\n',

            '**Before opening a report ticket please do the following:**',
            '1. Report in-game when you can (hit ESC, click Players, select Report).',
            '2. Record a video or take screenshots.',
            '3. Get a steam link to their account.\n',

            'To open a report ticket simply react below with <:high5:{}>!'.format(self.bot.settings.high5_emoji)
        ))

        embed = discord.Embed(
            title='Report Player',
            description=description,
            colour=colours.light_blue()
        )

        embed.set_footer(text='We are dedicated to ensure a safe and respective community and all reports will be looked into.')

        message = await ctx.send(embed=embed)
        self.bot.settings.report_message = message.id

        await message.add_reaction(':high5:{}'.format(self.bot.settings.high5_emoji))

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

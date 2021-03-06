import asyncio


import discord
import youtube_dl

from discord.ext import commands
description = ''' By typing this you accept that you are helpless and you seek help of Legends. Upcoming commands will be /play, /pause, /delete, /queue'''

Hindibot = commands.Bot(command_prefix='/', description=description)
Hindibot.remove_command('help')
# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ''


ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=50.0):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

class Music(commands.Cog):
    def __init__(self, Hindibot):
        self.Hindibot = Hindibot

    @commands.command()
    async def join(self, ctx, *, channel: discord.VoiceChannel):
        """Joins a voice channel"""

        if ctx.voice_client is not None:
            return await ctx.voice_client.move_to(channel)

        await channel.connect()

    @commands.command()
    async def play(self, ctx, *, query):
        """Plays a file from the local filesystem"""

        source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(query))
        ctx.voice_client.play(source, after=lambda e: print('Player error: %s' % e) if e else None)

        await ctx.send('Now playing: {}'.format(query))


    @commands.command()
    async def yt(self, ctx, *, url):
        """Plays from a url (almost anything youtube_dl supports)"""

        async with ctx.typing():
            player = await YTDLSource.from_url(url, loop=self.Hindibot.loop)
            ctx.voice_client.play(player, after=lambda e: print('Player error: %s' % e) if e else None)
            await ctx.send('Now playing: {}'.format(player.title))

    @commands.command()
    async def pause(self, ctx):
        """Pause from a url (almost anything youtube_dl supports)"""
        SongPlaying = ctx.voice_client.is_playing()
        Paused = ctx.voice_client.is_paused()
        if Paused != True:
            ctx.voice_client.pause()
            await ctx.send("> **Video is now Paused.**")
        else:
            if SongPlaying == True:
                await ctx.send("> **Video is already Paused.**")
            else:
                await ctx.send("> **There is no song currently playing.**")

    @commands.command()
    async def resume(self, ctx):
        """Resumes a paused song [Format: /resume]"""
        Paused = ctx.voice_client.is_paused()
        if Paused == True:
            ctx.voice_client.resume()
            await ctx.send("> **Video is now resuming.**")
        else:
            await ctx.send("> **The video player is not paused.**")

    @commands.command()
    async def stream(self, ctx, *, url):
        """Streams from a url (same as yt, but doesn't predownload)"""
        async with ctx.typing():
            player = await YTDLSource.from_url(url, loop=self.Hindibot.loop, stream=True)
            ctx.voice_client.play(player, after=lambda e: print('Player error: %s' % e) if e else None)

        await ctx.send('Now playing: {}'.format(player.title))

    @commands.command()
    async def volume(self, ctx, volume: int):
        """Changes the player's volume"""

        if ctx.voice_client is None:
            return await ctx.send("Not connected to a voice channel.")

        ctx.voice_client.source.volume = volume / 100
        await ctx.send("Changed volume to {}%".format(volume))

    @commands.command()
    async def stop(self, ctx):
        """Stops and disconnects the Hindibot from voice"""

        await ctx.voice_client.disconnect()

    @play.before_invoke
    @yt.before_invoke
    @stream.before_invoke
    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("You are not connected to a voice channel.")
                raise commands.CommandError("Author not connected to a voice channel.")
        elif ctx.voice_client.is_playing():
            ctx.voice_client.stop()

@Hindibot.command()
async def clear(ctx, amount=10):
        """
        :type amount: Amount is the number of messages to be deleted. These are the most recent messages that gets deleted.
        """
        await ctx.channel.purge(limit=amount)

@Hindibot.command(pass_context=True)
async def help(ctx):
    author = ctx.message.author

    embed = discord.Embed(
        colour=discord.Colour.blue()
    )
    embed.set_author(name='Help')
    embed.add_field(name='/yt <youtube pip url>',value= 'Plays the video and downloads it locally', inline=False)
    embed.add_field(name='/stream <youtube pip url>', value='Streams a Youtube video without downloading.', inline=False)
    embed.add_field(name='/stop',value= 'Stops the playback and Bot leaves the channel', inline=False)
    embed.add_field(name='/pause',value= 'Pauses the playback', inline=False)
    embed.add_field(name='/resume',value= 'Resumes the playback from the last stopping point', inline=False)
    embed.add_field(name='/clear',value= 'Clears 10 recent messages at a time', inline=False)
    embed.add_field(name='/FuckingBot',value= 'Have some fun with the bot.Its all in Hindi language', inline=False)


    await author.send(embed=embed)

@Hindibot.event
async def on_ready():
    print('Logged in as {0} ({0.id})'.format(Hindibot.user))
    print('------')

Hindibot.add_cog(Music(Hindibot))
Hindibot.run('<DiscordToken')

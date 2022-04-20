# This requires the 'message_content' privileged intent to function.
import asyncio
import discord

from discord.ext import commands
from io import BytesIO

ffmpeg_options = {
    'options': '-vn',
}


class gTTSSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = 'Computer M5'

    @classmethod
    async def from_gtts(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        mp3_fp = BytesIO()
        x = lambda: [gTTS('hello', lang='en').write_to_fp(mp3_fp), mp3_fp]
        data = await loop.run_in_executor(None, x)
        return cls(discord.FFmpegPCMAudio("", **ffmpeg_options), data=data)


class M5(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def join(self, ctx, *, channel: discord.VoiceChannel):
        """Joins a voice channel"""
        if ctx.voice_client is not None:
            return await ctx.voice_client.move_to(channel)
        await channel.connect()

    @commands.command()
    async def play(self, ctx, *, content):
        """Streams content using gtts"""
        async with ctx.typing():
            player = await gTTSSource.from_gtts(content, loop=self.bot.loop, stream=True)
            ctx.voice_client.play(player, after=lambda e: print(f'Player error: {e}') if e else None)
        await ctx.send(f'Now playing: {player.title}')

    @commands.command()
    async def volume(self, ctx, volume: int):
        """Changes the player's volume"""
        if ctx.voice_client is None:
            return await ctx.send("Not connected to a voice channel.")
        ctx.voice_client.source.volume = volume / 100
        await ctx.send(f"Changed volume to {volume}%")

    @commands.command()
    async def stop(self, ctx):
        """Stops and disconnects the bot from voice"""
        await ctx.voice_client.disconnect()

    @play.before_invoke
    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("You are not connected to a voice channel.")
                raise commands.CommandError("Author not connected to a voice channel.")
        elif ctx.voice_client.is_playing():
            ctx.voice_client.stop()


intents = discord.Intents.default()
#intents.message_content = True

bot = commands.Bot(
    command_prefix=commands.when_mentioned_or("!"),
    description='Simple LCARS Computer',
    intents=intents,
)


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')


async def main():
    async with bot:
        await bot.add_cog(M5(bot))
        data = ''
        with open('token.txt', 'r') as file:
            data = file.read().replace('\n', '')
        await bot.start(data)


asyncio.run(main())

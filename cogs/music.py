import discord
from discord.ext import commands
import asyncio
import yt_dlp


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_clients = {}
        self.queues = {}  # Dictionary to hold song queues for each server
        self.previous_songs = {}  # Dictionary to hold previous songs for each server
        self.yt_dl_options = {"format": "bestaudio/best"}
        self.ytdl = yt_dlp.YoutubeDL(self.yt_dl_options)
        self.ffmpeg_options = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn -filter:a "volume=0.25"'
        }

    def play_next(self, guild_id):
        """Plays the next song in the queue, if available."""
        if self.queues[guild_id]:
            next_song = self.queues[guild_id].pop(0)
            voice_client = self.voice_clients[guild_id]
            
            # Store the current song in previous_songs before playing the next one
            if guild_id not in self.previous_songs:
                self.previous_songs[guild_id] = []
            if hasattr(voice_client, 'current_song'):
                self.previous_songs[guild_id].append(voice_client.current_song)
                # Keep only the last 10 songs in history
                if len(self.previous_songs[guild_id]) > 10:
                    self.previous_songs[guild_id].pop(0)
            
            # Store the current song reference
            voice_client.current_song = next_song
            
            voice_client.play(
                discord.FFmpegOpusAudio(next_song['url'], **self.ffmpeg_options),
                after=lambda e: self.play_next(guild_id),
            )

    def create_song_embed(self, song, status):
        """Creates a beautiful embed for the song."""
        embed = discord.Embed(
            title=f"🎶 {status}: {song['title']}",
            description=f"[Click here to watch the video]({song['webpage_url']})",
            color=discord.Color.green() if status == "Now Playing" else discord.Color.orange()
        )
        embed.add_field(name="Uploader", value=song['uploader'], inline=True)
        embed.add_field(name="Duration", value=f"{song['duration'] // 60}:{song['duration'] % 60:02}", inline=True)
        embed.set_thumbnail(url=song['thumbnail'] if song.get('thumbnail') else 'https://via.placeholder.com/150')
        embed.set_footer(text="Requested by " + song.get('requested_by', 'Unknown'), icon_url=song.get('avatar_url', 'https://via.placeholder.com/32'))

        return embed

    @commands.hybrid_command(name = 'bajau')
    async def play(self, ctx, *, title: str):
        """Searches and plays audio from YouTube based on the title."""
        try:
            await ctx.defer()

            if ctx.guild.id not in self.voice_clients:
                if ctx.author.voice and ctx.author.voice.channel:
                    voice_client = await ctx.author.voice.channel.connect()
                    self.voice_clients[ctx.guild.id] = voice_client
                    self.queues[ctx.guild.id] = []
                else:
                    await ctx.send("You need to be in a voice channel to use this command.")
                    return

            loop = asyncio.get_event_loop()
            search_url = f"ytsearch:{title}"
            data = await loop.run_in_executor(None, lambda: self.ytdl.extract_info(search_url, download=False))

            if 'entries' not in data or len(data['entries']) == 0:
                await ctx.send("No results found for your search.")
                return

            song = data['entries'][0]

            song_data = {
                'url': song['url'],
                'title': song.get('title', 'Unknown Title'),
                'uploader': song.get('uploader', 'Unknown Uploader'),
                'thumbnail': song.get('thumbnail', None),
                'webpage_url': song.get('webpage_url', song['url']),
                'duration': song.get('duration', 0),
                'requested_by': ctx.author.display_name,
                'avatar_url': ctx.author.avatar.url if ctx.author.avatar else 'https://via.placeholder.com/32'
            }

            self.queues[ctx.guild.id].append(song_data)

            if not self.voice_clients[ctx.guild.id].is_playing():
                self.play_next(ctx.guild.id)
                embed = self.create_song_embed(song_data, "Now Playing")
                await ctx.send(embed=embed)
            else:
                embed = self.create_song_embed(song_data, "Added to Queue")
                await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

    @commands.hybrid_command(name = 'dekhau')
    async def queue(self, ctx):
        """Displays the current song queue."""
        if ctx.guild.id in self.queues and self.queues[ctx.guild.id]:
            queue = self.queues[ctx.guild.id]
            embed = discord.Embed(
                title="🎵 Current Music Queue",
                description="\n".join(
                    [f"**{idx + 1}.** [{song['title']}]({song['webpage_url']})" for idx, song in enumerate(queue)],
                ),
                color=discord.Color.blue(),
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send("The queue is currently empty!")

    @commands.hybrid_command(name = 'arko')
    async def skip(self, ctx):
        """Skips the current song."""
        if ctx.guild.id in self.voice_clients and self.voice_clients[ctx.guild.id].is_playing():
            voice_client = self.voice_clients[ctx.guild.id]
            if self.queues[ctx.guild.id]:
                next_song = self.queues[ctx.guild.id][0]  # Peek at next song without removing it
                voice_client.stop()  # This will trigger play_next
                embed = self.create_song_embed(next_song, "Now Playing")
                await ctx.send(embed=embed)
            else:
                voice_client.stop()
                await ctx.send("No more songs in the queue.")
        else:
            await ctx.send("No song is currently playing.")


    @commands.hybrid_command(name = 'chup')
    async def stop(self, ctx):
        """Stops playback and clears the queue."""
        if ctx.guild.id in self.voice_clients:
            self.voice_clients[ctx.guild.id].stop()
            self.queues[ctx.guild.id].clear()
            self.previous_songs[ctx.guild.id] = []  # Clear the previous songs history
            await self.voice_clients[ctx.guild.id].disconnect()
            del self.voice_clients[ctx.guild.id]
            del self.queues[ctx.guild.id]
            del self.previous_songs[ctx.guild.id]  # Remove the previous songs entry
            await ctx.send("🛑 Stopped playback and disconnected from the voice channel.")
        else:
            await ctx.send("I'm not connected to a voice channel.")

    @commands.hybrid_command(name = 'ekchhin')
    async def pause(self, ctx):
        """Pauses the current song."""
        if ctx.guild.id in self.voice_clients and self.voice_clients[ctx.guild.id].is_playing():
            self.voice_clients[ctx.guild.id].pause()
            await ctx.send("⏸️ Paused the music.")
        else:
            await ctx.send("No song is currently playing.")

    @commands.hybrid_command(name = 'bhayo')
    async def resume(self, ctx):
        """Resumes the current song."""
        if ctx.guild.id in self.voice_clients and self.voice_clients[ctx.guild.id].is_paused():
            self.voice_clients[ctx.guild.id].resume()
            await ctx.send("▶️ Resumed the music.")
        else:
            await ctx.send("No song is currently paused.")


    @commands.hybrid_command(name='aghiko')
    async def previous(self, ctx):
        """Plays the previous song from history."""
        if ctx.guild.id not in self.voice_clients:
            await ctx.send("I'm not connected to a voice channel.")
            return

        if ctx.guild.id not in self.previous_songs or not self.previous_songs[ctx.guild.id]:
            await ctx.send("No previous songs in history!")
            return

        # Get the current song before stopping
        voice_client = self.voice_clients[ctx.guild.id]
        current_song = None
        if hasattr(voice_client, 'current_song'):
            current_song = voice_client.current_song

        # Get the previous song
        previous_song = self.previous_songs[ctx.guild.id].pop()

        # Add current song to the front of the queue
        if current_song:
            self.queues[ctx.guild.id].insert(0, current_song)

        # Add the previous song to the front of the queue
        self.queues[ctx.guild.id].insert(0, previous_song)

        # Stop current playback (this will trigger play_next)
        voice_client.stop()

        # Create and send embed for the previous song
        embed = self.create_song_embed(previous_song, "Now Playing")
        await ctx.send(embed=embed)


async def setup(bot):
    """Sets up the Music cog."""
    await bot.add_cog(Music(bot))
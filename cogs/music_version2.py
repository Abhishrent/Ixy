import discord
from discord.ext import commands
import yt_dlp
import json
import os
import threading

STATE_FILE = os.path.join(os.path.dirname(__file__), "..", "music_state.json")
STATE_FILE = os.path.abspath(STATE_FILE)
IDLE_TIMEOUT = 300  # 5 minutes in seconds

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            try:
                return json.load(f)
            except Exception:
                return {}
    return {}

def save_state(state):
    # Ensure the file and parent directory exist
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

def clear_state():
    if os.path.exists(STATE_FILE):
        os.remove(STATE_FILE)

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_clients = {}
        # Use cookies.txt from the project directory, create if missing
        cookies_path = os.path.join(os.path.dirname(__file__), "..", "cookies.txt")
        cookies_path = os.path.abspath(cookies_path)
        if not os.path.exists(cookies_path):
            # Create an empty cookies.txt if it doesn't exist
            os.makedirs(os.path.dirname(cookies_path), exist_ok=True)
            with open(cookies_path, "w") as f:
                f.write("")
            print(f"Created empty cookies.txt at {cookies_path}. Please replace it with a valid cookies file for YouTube.")
        if os.path.exists(cookies_path):
            self.yt_dl_options = {
                "format": "bestaudio/best",
                "cookiefile": cookies_path
            }
        else:
            print(f"Warning: cookies.txt not found at {cookies_path}. Some YouTube streams may not work.")
            self.yt_dl_options = {
                "format": "bestaudio/best"
            }
        self.ytdl = yt_dlp.YoutubeDL(self.yt_dl_options)
        self.ffmpeg_options = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn -filter:a "volume=0.25"'
        }
        self.state = load_state()
        self.idle_timers = {}  # guild_id: threading.Timer

    def ensure_guild_state(self, guild_id):
        if guild_id not in self.state:
            self.state[guild_id] = {"queue": [], "previous": [], "current_song": None}
        else:
            # Ensure all keys exist
            for key in ("queue", "previous", "current_song"):
                if key not in self.state[guild_id]:
                    self.state[guild_id][key] = [] if key in ("queue", "previous") else None

    def save(self):
        save_state(self.state)

    def start_idle_timer(self, guild_id):
        # Cancel any existing timer
        if guild_id in self.idle_timers:
            self.idle_timers[guild_id].cancel()
        # Start a new timer
        timer = threading.Timer(IDLE_TIMEOUT, lambda: self.bot.loop.call_soon_threadsafe(self.disconnect_if_idle, guild_id))
        self.idle_timers[guild_id] = timer
        timer.start()

    def cancel_idle_timer(self, guild_id):
        if guild_id in self.idle_timers:
            self.idle_timers[guild_id].cancel()
            del self.idle_timers[guild_id]

    def disconnect_if_idle(self, guild_id):
        voice_client = self.voice_clients.get(guild_id)
        if not voice_client:
            return
        # Only disconnect if not playing or paused
        if not voice_client.is_playing() and not voice_client.is_paused():
            coro = self._disconnect_and_cleanup(guild_id)
            fut = discord.utils.maybe_coroutine(coro)
            try:
                asyncio.run_coroutine_threadsafe(fut, self.bot.loop)
            except Exception:
                pass

    async def _disconnect_and_cleanup(self, guild_id):
        voice_client = self.voice_clients.get(guild_id)
        if voice_client:
            await voice_client.disconnect()
            del self.voice_clients[guild_id]
        guild_id_str = str(guild_id)
        if guild_id_str in self.state:
            del self.state[guild_id_str]
            self.save()
        if not self.state:
            clear_state()
        self.cancel_idle_timer(guild_id)

    def play_next(self, guild_id):
        guild_id_str = str(guild_id)
        self.ensure_guild_state(guild_id_str)
        voice_client = self.voice_clients.get(guild_id)
        if not voice_client:
            return
        queue = self.state[guild_id_str]["queue"]
        if queue:
            next_song = queue.pop(0)
            # Save current song to previous
            current_song = self.state[guild_id_str].get("current_song")
            if current_song:
                self.state[guild_id_str]["previous"].append(current_song)
                if len(self.state[guild_id_str]["previous"]) > 10:
                    self.state[guild_id_str]["previous"].pop(0)
            self.state[guild_id_str]["current_song"] = next_song
            self.save()
            # Use yt-dlp to get the best audio URL and headers
            info = self.ytdl.extract_info(next_song['webpage_url'], download=False)
            url = info['url']
            headers = info.get('http_headers', {})
            # Prepare FFmpeg options with headers
            before_options = '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
            if headers:
                header_str = " ".join([f"-headers \"{k}: {v}\\r\\n\"" for k, v in headers.items()])
                before_options += f" {header_str}"
            ffmpeg_options = {
                'before_options': before_options,
                'options': '-vn -filter:a "volume=0.25"'
            }
            voice_client.current_song = next_song
            def after_playing(error):
                if error:
                    print(f"Error in after_playing: {error}")
                # Use call_soon_threadsafe to avoid concurrency issues
                self.bot.loop.call_soon_threadsafe(self.play_next, guild_id)
            try:
                voice_client.play(
                    discord.FFmpegOpusAudio(url, **ffmpeg_options),
                    after=after_playing,
                )
                self.cancel_idle_timer(guild_id)  # Cancel idle timer while playing
            except Exception as e:
                print(f"Error playing audio: {e}")
                self.play_next(guild_id)
        else:
            self.state[guild_id_str]["current_song"] = None
            self.save()
            if hasattr(voice_client, 'current_song'):
                voice_client.current_song = None
            self.start_idle_timer(guild_id)  # Start idle timer when queue is empty

    def create_song_embed(self, song, status):
        embed = discord.Embed(
            title=f"🎶 {status}: {song['title']}",
            color=discord.Color.green() if status == "Now Playing" else discord.Color.orange()
        )
        embed.add_field(name="Uploader", value=song.get('uploader', 'Unknown'), inline=True)
        embed.add_field(name="Duration", value=f"{song.get('duration', 0) // 60}:{song.get('duration', 0) % 60:02}", inline=True)
        embed.set_thumbnail(url=song.get('thumbnail', 'https://via.placeholder.com/150'))
        embed.set_footer(text="Requested by " + song.get('requested_by', 'Unknown'), icon_url=song.get('avatar_url', 'https://via.placeholder.com/32'))
        return embed

    @commands.hybrid_command(name='bajau')
    async def play(self, ctx, *, title: str):
        try:
            await ctx.defer()
            guild_id = str(ctx.guild.id)
            if ctx.guild.id not in self.voice_clients:
                if ctx.author.voice and ctx.author.voice.channel:
                    voice_client = await ctx.author.voice.channel.connect()
                    self.voice_clients[ctx.guild.id] = voice_client
                else:
                    await ctx.send("You need to be in a voice channel to use this command.")
                    return
            self.ensure_guild_state(guild_id)
            loop = self.bot.loop
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
            self.state[guild_id]["queue"].append(song_data)
            self.save()
            if not self.voice_clients[ctx.guild.id].is_playing():
                self.play_next(ctx.guild.id)
                embed = self.create_song_embed(song_data, "Now Playing")
                await ctx.send(embed=embed)
            else:
                embed = self.create_song_embed(song_data, "Added to Queue")
                await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

    @commands.hybrid_command(name='dekhau')
    async def queue(self, ctx):
        guild_id = str(ctx.guild.id)
        self.ensure_guild_state(guild_id)
        state = self.state[guild_id]
        current_song = state.get("current_song")
        queue = state.get("queue", [])
        description = ""
        if current_song:
            description += f"**Now Playing:** [{current_song['title']}]({current_song['webpage_url']})\n\n"
        if queue:
            description += "\n".join(
                [f"**{idx + 1}.** [{song['title']}]({song['webpage_url']})" for idx, song in enumerate(queue)]
            )
        if description:
            embed = discord.Embed(
                title="🎵 Current Music Queue",
                description=description,
                color=discord.Color.blue(),
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send("The queue is currently empty!")

    @commands.hybrid_command(name='arko')
    async def skip(self, ctx):
        guild_id = str(ctx.guild.id)
        if ctx.guild.id in self.voice_clients and self.voice_clients[ctx.guild.id].is_playing():
            voice_client = self.voice_clients[ctx.guild.id]
            self.ensure_guild_state(guild_id)
            state = self.state[guild_id]
            current_song = state.get("current_song")
            if current_song:
                state["previous"].append(current_song)
                if len(state["previous"]) > 10:
                    state["previous"].pop(0)
            state["current_song"] = None
            self.save()
            if hasattr(voice_client, 'current_song'):
                voice_client.current_song = None
            voice_client.stop()
            self.start_idle_timer(ctx.guild.id)  # Start idle timer after skip
            await ctx.send("⏭️ Skipped to the next song.")
        else:
            await ctx.send("No song is currently playing.")

    @commands.hybrid_command(name='chup')
    async def stop(self, ctx):
        guild_id = str(ctx.guild.id)
        if ctx.guild.id in self.voice_clients:
            self.voice_clients[ctx.guild.id].stop()
            await self.voice_clients[ctx.guild.id].disconnect()
            del self.voice_clients[ctx.guild.id]
            if guild_id in self.state:
                del self.state[guild_id]
                self.save()
            # If no more guilds, clear the file
            if not self.state:
                clear_state()
            self.cancel_idle_timer(ctx.guild.id)
            await ctx.send("🛑 Stopped playback and disconnected from the voice channel.")
        else:
            await ctx.send("I'm not connected to a voice channel.")

    @commands.hybrid_command(name='ekchhin')
    async def pause(self, ctx):
        if ctx.guild.id in self.voice_clients and self.voice_clients[ctx.guild.id].is_playing():
            self.voice_clients[ctx.guild.id].pause()
            self.start_idle_timer(ctx.guild.id)  # Start idle timer when paused
            await ctx.send("⏸️ Paused the music.")
        else:
            await ctx.send("No song is currently playing.")

    @commands.hybrid_command(name='bhayo')
    async def resume(self, ctx):
        if ctx.guild.id in self.voice_clients and self.voice_clients[ctx.guild.id].is_paused():
            self.voice_clients[ctx.guild.id].resume()
            self.cancel_idle_timer(ctx.guild.id)  # Cancel idle timer when resumed
            await ctx.send("▶️ Resumed the music.")
        else:
            await ctx.send("No song is currently paused.")

    @commands.hybrid_command(name='aghiko')
    async def previous(self, ctx):
        guild_id = str(ctx.guild.id)
        if ctx.guild.id not in self.voice_clients:
            await ctx.send("I'm not connected to a voice channel.")
            return
        self.ensure_guild_state(guild_id)
        state = self.state[guild_id]
        if not state.get("previous"):
            await ctx.send("No previous songs in history!")
            return
        previous_song = state["previous"].pop()
        state["queue"].insert(0, previous_song)
        state["current_song"] = None
        self.save()
        voice_client = self.voice_clients[ctx.guild.id]
        if hasattr(voice_client, 'current_song'):
            voice_client.current_song = None
        voice_client.stop()
        self.start_idle_timer(ctx.guild.id)  # Start idle timer after previous if idle
        await ctx.send("⏮️ Playing the previous song.")

async def setup(bot):
    await bot.add_cog(Music(bot))
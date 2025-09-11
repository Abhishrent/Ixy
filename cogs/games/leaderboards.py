import discord
from discord.ext import commands
import os
import json
from config import EMBED_THUMBNAIL

MEDALS = [":first_place:", ":second_place:", ":third_place:"]

MEMORY_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "game_files", "memory.json")
SEQUENCE_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "game_files", "sequence.json")
WORDLE_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "game_files", "daily_wordle.json")
LEADERBOARD_USERS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "game_files", "leaderboards.json")

class Leaderboards(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def load_json(self, path):
        if not os.path.exists(path):
            return []
        try:
            with open(path, "r") as f:
                data = json.load(f)
                # Ensure we return a list, even if the file contains something else
                return data if isinstance(data, list) else []
        except Exception as e:
            print(f"Error loading {path}: {e}")
            return []

    def load_leaderboard_users(self):
        if not os.path.exists(LEADERBOARD_USERS_FILE):
            return {}
        try:
            with open(LEADERBOARD_USERS_FILE, "r") as f:
                data = json.load(f)
                # Ensure we return a dict, even if the file contains something else
                return data if isinstance(data, dict) else {}
        except Exception as e:
            print(f"Error loading {LEADERBOARD_USERS_FILE}: {e}")
            return {}

    def user_mention(self, user_id):
        try:
            return f"<@{int(user_id)}>"
        except Exception:
            return str(user_id)

    @commands.hybrid_command(name="leaderboards", with_app_command=True)
    async def leaderboards(self, ctx):
        """Show the leaderboards for all games"""

        # Load username mapping if available
        user_map = self.load_leaderboard_users()

        # --- Memory Matching Game ---
        memory_scores = self.load_json(MEMORY_FILE)
        memory_text = ""
        if memory_scores:
            for idx, entry in enumerate(memory_scores, 1):
                medal = MEDALS[idx-1] if idx <= 3 else ""
                user_id = entry.get("user_id")
                mention = self.user_mention(user_id)
                username = user_map.get(str(user_id), entry.get("username", "Unknown"))
                memory_text += f"{medal} {mention} ({username})\nTime: **{entry.get('time_display', '--:--')}** (`{entry.get('best_time', 0):.2f}`s)\nDate: {entry.get('date', '-')}\n\n"
        else:
            memory_text = "No scores yet."

        # --- Sequence Memory Game ---
        sequence_scores = self.load_json(SEQUENCE_FILE)
        sequence_text = ""
        if sequence_scores:
            for idx, entry in enumerate(sequence_scores, 1):
                medal = MEDALS[idx-1] if idx <= 3 else ""
                user_id = entry.get("user_id")
                mention = self.user_mention(user_id)
                username = user_map.get(str(user_id), entry.get("username", "Unknown"))
                sequence_text += f"{medal} {mention} ({username})\nRound: **{entry.get('max_round', 0)}** | Tiles: **{entry.get('tiles_memorised', 0)}**\nDate: {entry.get('date', '-')}\n\n"
        else:
            sequence_text = "No scores yet."

        # --- Daily Wordle ---
        wordle_text = ""
        if os.path.exists(WORDLE_FILE):
            try:
                with open(WORDLE_FILE, "r") as f:
                    data = json.load(f)
                top_streaks = data.get("top_streaks", [])
            except Exception:
                top_streaks = []
            if top_streaks:
                for idx, entry in enumerate(top_streaks, 1):
                    medal = MEDALS[idx-1] if idx <= 3 else ""
                    user_id = entry.get("user_id")
                    mention = self.user_mention(user_id)
                    username = user_map.get(str(user_id), entry.get("username", "Unknown"))
                    wordle_text += f"{medal} {mention} ({username})\nStreak: **{entry.get('max_streak', 0)}**\nDate: {entry.get('date', '-')}\n\n"
            else:
                wordle_text = "No streaks yet."
        else:
            wordle_text = "No streaks yet."

        embed = discord.Embed(
            title="🏅 Game Leaderboards",
            color=discord.Color.purple()
        )
        embed.set_thumbnail(url=EMBED_THUMBNAIL)
        embed.add_field(
            name="🧠 Memory Matching Game (Fastest Times)",
            value=memory_text,
            inline=True
        )
        embed.add_field(
            name="🔢 Sequence Memory Game (Highest Rounds)",
            value=sequence_text,
            inline=True
        )
        embed.add_field(
            name="🏆 Daily Wordle (Longest Streaks)",
            value=wordle_text,
            inline=True
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Leaderboards(bot))

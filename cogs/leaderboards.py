import discord
from discord.ext import commands
import os
import json
from config import EMBED_THUMBNAIL

MEMORY_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "game_files", "memory.json")
SEQUENCE_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "game_files", "sequence.json")
WORDLE_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "game_files", "daily_wordle.json")

MEDALS = [":first_place:", ":second_place:", ":third_place:"]

class Leaderboards(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def load_json(self, path):
        if not os.path.exists(path):
            return []
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception:
            return []

    def user_mention(self, user_id):
        try:
            return f"<@{int(user_id)}>"
        except Exception:
            return str(user_id)

# --- DM logic merged from leaderboards_dm.py ---
    async def try_dm(self, user_id, embed):
        user = self.bot.get_user(int(user_id))
        if user:
            try:
                await user.send(embed=embed)
            except Exception:
                pass

    def get_previous_leaderboard(self, path):
        prev_path = path + ".prev"
        if not os.path.exists(prev_path):
            return []
        try:
            with open(prev_path, "r") as f:
                return json.load(f)
        except Exception:
            return []

    def save_previous_leaderboard(self, path, data):
        prev_path = path + ".prev"
        with open(prev_path, "w") as f:
            json.dump(data, f, indent=2)

    @commands.Cog.listener()
    async def on_ready(self):
        # --- Memory Matching Game ---
        memory_scores = self.load_json(MEMORY_FILE)
        prev_memory = self.get_previous_leaderboard(MEMORY_FILE)
        prev_ids = [e.get("user_id") for e in prev_memory]
        current_ids = [e.get("user_id") for e in memory_scores]
        # Notify new entries or position changes
        for idx, entry in enumerate(memory_scores, 1):
            prev_pos = None
            for pidx, prev_entry in enumerate(prev_memory, 1):
                if prev_entry.get("user_id") == entry.get("user_id"):
                    prev_pos = pidx
                    break
            if prev_pos is None or prev_pos != idx or "notified" not in entry or not entry["notified"]:
                if prev_pos is None:
                    msg = f"Congratulations! You are now #{idx} on the Memory Matching Game leaderboard!"
                else:
                    msg = f"Your position on the Memory Matching Game leaderboard has changed: #{prev_pos} → #{idx}!"
                embed = discord.Embed(
                    title="🏅 Memory Matching Game Leaderboard!",
                    description=f"{msg}\n\nTime: **{entry['time_display']}** (`{entry['best_time']:.2f}`s)\nDate: {entry['date']}",
                    color=discord.Color.green()
                )
                await self.try_dm(entry["user_id"], embed)
                entry["notified"] = True
        # Notify users who lost their spot
        for prev_entry in prev_memory:
            if prev_entry.get("user_id") not in current_ids:
                embed = discord.Embed(
                    title="😢 You lost your leaderboard spot!",
                    description="Someone has beaten your score and you are no longer in the top 3 for Memory Matching Game.",
                    color=discord.Color.red()
                )
                await self.try_dm(prev_entry.get("user_id"), embed)
        if memory_scores and any("notified" in e for e in memory_scores):
            with open(MEMORY_FILE, "w") as f:
                json.dump(memory_scores, f, indent=2)
        self.save_previous_leaderboard(MEMORY_FILE, memory_scores)

        # --- Sequence Memory Game ---
        sequence_scores = self.load_json(SEQUENCE_FILE)
        prev_sequence = self.get_previous_leaderboard(SEQUENCE_FILE)
        prev_ids = [e.get("user_id") for e in prev_sequence]
        current_ids = [e.get("user_id") for e in sequence_scores]
        for idx, entry in enumerate(sequence_scores, 1):
            prev_pos = None
            for pidx, prev_entry in enumerate(prev_sequence, 1):
                if prev_entry.get("user_id") == entry.get("user_id"):
                    prev_pos = pidx
                    break
            if prev_pos is None or prev_pos != idx or "notified" not in entry or not entry["notified"]:
                if prev_pos is None:
                    msg = f"Congratulations! You are now #{idx} on the Sequence Memory Game leaderboard!"
                else:
                    msg = f"Your position on the Sequence Memory Game leaderboard has changed: #{prev_pos} → #{idx}!"
                embed = discord.Embed(
                    title="🏅 Sequence Memory Game Leaderboard!",
                    description=f"{msg}\n\nRound: **{entry['max_round']}** | Tiles: **{entry['tiles_memorised']}**\nDate: {entry['date']}",
                    color=discord.Color.blue()
                )
                await self.try_dm(entry["user_id"], embed)
                entry["notified"] = True
        for prev_entry in prev_sequence:
            if prev_entry.get("user_id") not in current_ids:
                embed = discord.Embed(
                    title="😢 You lost your leaderboard spot!",
                    description="Someone has beaten your score and you are no longer in the top 3 for Sequence Memory Game.",
                    color=discord.Color.red()
                )
                await self.try_dm(prev_entry.get("user_id"), embed)
        if sequence_scores and any("notified" in e for e in sequence_scores):
            with open(SEQUENCE_FILE, "w") as f:
                json.dump(sequence_scores, f, indent=2)
        self.save_previous_leaderboard(SEQUENCE_FILE, sequence_scores)

        # --- Daily Wordle ---
        if os.path.exists(WORDLE_FILE):
            try:
                with open(WORDLE_FILE, "r") as f:
                    data = json.load(f)
                top_streaks = data.get("top_streaks", [])
                prev_wordle = self.get_previous_leaderboard(WORDLE_FILE)
                prev_ids = [e.get("user_id") for e in prev_wordle]
                current_ids = [e.get("user_id") for e in top_streaks]
                updated = False
                for idx, entry in enumerate(top_streaks, 1):
                    prev_pos = None
                    for pidx, prev_entry in enumerate(prev_wordle, 1):
                        if prev_entry.get("user_id") == entry.get("user_id"):
                            prev_pos = pidx
                            break
                    if prev_pos is None or prev_pos != idx or "notified" not in entry or not entry["notified"]:
                        if prev_pos is None:
                            msg = f"Congratulations! You are now #{idx} on the Daily Wordle Streaks leaderboard!"
                        else:
                            msg = f"Your position on the Daily Wordle Streaks leaderboard has changed: #{prev_pos} → #{idx}!"
                        embed = discord.Embed(
                            title="🏅 Daily Wordle Streaks Leaderboard!",
                            description=f"{msg}\n\nStreak: **{entry['max_streak']}**\nDate: {entry['date']}",
                            color=discord.Color.gold()
                        )
                        await self.try_dm(entry["user_id"], embed)
                        entry["notified"] = True
                        updated = True
                for prev_entry in prev_wordle:
                    if prev_entry.get("user_id") not in current_ids:
                        embed = discord.Embed(
                            title="😢 You lost your leaderboard spot!",
                            description="Someone has beaten your streak and you are no longer in the top 3 for Daily Wordle.",
                            color=discord.Color.red()
                        )
                        await self.try_dm(prev_entry.get("user_id"), embed)
                if updated:
                    data["top_streaks"] = top_streaks
                    with open(WORDLE_FILE, "w") as f:
                        json.dump(data, f, indent=2)
                self.save_previous_leaderboard(WORDLE_FILE, top_streaks)
            except Exception:
                pass

    @commands.hybrid_command(name="leaderboards", with_app_command=True)
    async def leaderboards(self, ctx):
        """Show the leaderboards for all games"""
        # Memory Matching Game
        memory_scores = self.load_json(MEMORY_FILE)
        memory_text = ""
        if memory_scores:
            for idx, entry in enumerate(memory_scores, 1):
                medal = MEDALS[idx-1] if idx <= 3 else ""
                mention = self.user_mention(entry.get("user_id"))
                memory_text += f"{medal} {mention}\nTime: **{entry['time_display']}** (`{entry['best_time']:.2f}`s)\nDate: {entry['date']}\n\n"
        else:
            memory_text = "No scores yet."

        # Sequence Memory Game
        sequence_scores = self.load_json(SEQUENCE_FILE)
        sequence_text = ""
        if sequence_scores:
            for idx, entry in enumerate(sequence_scores, 1):
                medal = MEDALS[idx-1] if idx <= 3 else ""
                mention = self.user_mention(entry.get("user_id"))
                sequence_text += f"{medal} {mention}\nRound: **{entry['max_round']}** | Tiles: **{entry['tiles_memorised']}**\nDate: {entry['date']}\n\n"
        else:
            sequence_text = "No scores yet."

        # Daily Wordle
        wordle_text = ""
        current_streak_text = ""
        if os.path.exists(WORDLE_FILE):
            try:
                with open(WORDLE_FILE, "r") as f:
                    data = json.load(f)
                top_streaks = data.get("top_streaks", [])
                streaks = data.get("streaks", {})
            except Exception:
                top_streaks = []
                streaks = {}
            if top_streaks:
                for idx, entry in enumerate(top_streaks, 1):
                    medal = MEDALS[idx-1] if idx <= 3 else ""
                    mention = self.user_mention(entry.get("user_id"))
                    wordle_text += f"{medal} {mention}\nStreak: **{entry['max_streak']}**\nDate: {entry['date']}\n\n"
            else:
                wordle_text = "No streaks yet."
            # Show current ongoing streak (if any)
            if streaks:
                max_streak = max(streaks.values(), default=0)
                if max_streak > 0:
                    leaders = [uid for uid, streak in streaks.items() if streak == max_streak]
                    leader_mentions = ", ".join(self.user_mention(uid) for uid in leaders)
                    current_streak_text = f"🔥 Current Streak: **{max_streak}** by {leader_mentions}"
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
        wordle_field_value = wordle_text
        if current_streak_text:
            wordle_field_value = f"{current_streak_text}\n\n{wordle_text}"
        embed.add_field(
            name="🏆 Daily Wordle (Longest Streaks)",
            value=wordle_field_value,
            inline=True
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Leaderboards(bot))

import discord
from discord.ext import commands, tasks
import os
import json
import asyncio
from datetime import datetime
from config import EMBED_THUMBNAIL

# --- File paths ---
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
GAME_FILES = os.path.join(BASE_DIR, "game_files")
MEMORY_FILE = os.path.join(GAME_FILES, "memory.json")
SEQUENCE_FILE = os.path.join(GAME_FILES, "sequence.json")
WORDLE_FILE = os.path.join(GAME_FILES, "daily_wordle.json")
LEADERBOARD_STATE_FILE = os.path.join(GAME_FILES, "leaderboards.json")

# --- Channel to post leaderboard changes ---
LEADERBOARD_CHANNEL_ID = 1408845348214018118  # Replace with your channel ID

# --- Helper functions ---
def safe_load_json(path, default):
    try:
        if not os.path.exists(path):
            return default
        with open(path, "r") as f:
            return json.load(f)
    except Exception:
        return default

def safe_save_json(path, data):
    try:
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass

def get_user_id(entry):
    # Handles both int and str user_id
    return str(entry.get("user_id"))

def leaderboard_to_dict(entries, key_fields):
    # Returns dict: user_id -> entry (with only relevant fields)
    return {
        get_user_id(e): {k: e.get(k) for k in key_fields}
        for e in entries
    }

def leaderboard_positions(entries):
    # Returns dict: user_id -> position (1-based)
    return {get_user_id(e): idx+1 for idx, e in enumerate(entries)}

class LeaderboardWatcher(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.memory_fields = ["user_id", "username", "best_time", "time_display", "date"]
        self.sequence_fields = ["user_id", "username", "max_round", "tiles_memorised", "date"]
        self.wordle_fields = ["user_id", "username", "max_streak", "date"]
        self.check_leaderboards.start()

    def cog_unload(self):
        self.check_leaderboards.cancel()

    @tasks.loop(minutes=1)
    async def check_leaderboards(self):
        await self.bot.wait_until_ready()
        channel = self.bot.get_channel(LEADERBOARD_CHANNEL_ID)
        if channel is None:
            return

        # Load previous state
        prev_state = safe_load_json(LEADERBOARD_STATE_FILE, {})

        # Load current leaderboards
        memory = safe_load_json(MEMORY_FILE, [])
        sequence = safe_load_json(SEQUENCE_FILE, [])
        wordle_data = safe_load_json(WORDLE_FILE, {})
        wordle = wordle_data.get("top_streaks", [])

        # Prepare current state
        curr_state = {
            "memory": memory,
            "sequence": sequence,
            "wordle": wordle
        }

        # Compare and detect changes for each game
        await self.process_game(
            "Memory",
            memory,
            prev_state.get("memory", []),
            self.memory_fields,
            key_score="best_time",
            better="lower",
            channel=channel
        )
        await self.process_game(
            "Sequence",
            sequence,
            prev_state.get("sequence", []),
            self.sequence_fields,
            key_score="max_round",
            better="higher",
            channel=channel
        )
        await self.process_game(
            "Wordle",
            wordle,
            prev_state.get("wordle", []),
            self.wordle_fields,
            key_score="max_streak",
            better="higher",
            channel=channel
        )

        # Save new state
        safe_save_json(LEADERBOARD_STATE_FILE, curr_state)

    async def process_game(self, game_name, curr_entries, prev_entries, key_fields, key_score, better, channel):
        curr_dict = leaderboard_to_dict(curr_entries, key_fields)
        prev_dict = leaderboard_to_dict(prev_entries, key_fields)
        curr_pos = leaderboard_positions(curr_entries)
        prev_pos = leaderboard_positions(prev_entries)

        # All user_ids involved
        user_ids = set(curr_dict.keys()) | set(prev_dict.keys())

        for user_id in user_ids:
            curr = curr_dict.get(user_id)
            prev = prev_dict.get(user_id)
            curr_rank = curr_pos.get(user_id)
            prev_rank = prev_pos.get(user_id)

            # Get user object
            user = None
            try:
                user = await self.bot.fetch_user(int(user_id))
            except Exception:
                pass

            # New entry
            if curr and not prev:
                msg = f"{user.mention if user else user_id} entered the {game_name} leaderboard at position {curr_rank}!"
                await self.announce(user, channel, msg)
            # Removal
            elif prev and not curr:
                msg = f"{user.mention if user else user_id} was removed from the {game_name} leaderboard (was position {prev_rank})."
                await self.announce(user, channel, msg)
            # Still present, check for promotion/demotion/personal best
            elif curr and prev:
                # Promotion/Demotion
                if curr_rank < prev_rank:
                    msg = f"{user.mention if user else user_id} moved up to position {curr_rank} in {game_name}!"
                    await self.announce(user, channel, msg)
                elif curr_rank > prev_rank:
                    msg = f"{user.mention if user else user_id} moved down to position {curr_rank} in {game_name}."
                    await self.announce(user, channel, msg)
                # Personal best
                curr_score = curr.get(key_score)
                prev_score = prev.get(key_score)
                try:
                    if curr_score is not None and prev_score is not None:
                        if better == "lower" and float(curr_score) < float(prev_score):
                            msg = f"{user.mention if user else user_id} achieved a new personal best in {game_name}! ({curr_score})"
                            await self.announce(user, channel, msg)
                        elif better == "higher" and float(curr_score) > float(prev_score):
                            msg = f"{user.mention if user else user_id} achieved a new personal best in {game_name}! ({curr_score})"
                            await self.announce(user, channel, msg)
                except Exception:
                    pass

    async def announce(self, user, channel, msg):
        # DM uses direct address, channel uses third person
        # msg is always in third person, so convert for DM

        # Mention arcade role
        channel_content = f"<@&1406096504850223276>"  # Arcade role mention

        # Try to convert third person to second person for DM
        dm_msg = msg
        if user:
            # Replace mention with "You"
            dm_msg = dm_msg.replace(user.mention, "You")
            # Replace "was" with "were" for removals
            dm_msg = dm_msg.replace(" was ", " were ")
            # Replace "moved up to position" with "moved up to position"
            dm_msg = dm_msg.replace("moved up to position", "moved up to position")
            dm_msg = dm_msg.replace("moved down to position", "moved down to position")
            # Replace "entered the" with "entered the"
            dm_msg = dm_msg.replace("entered the", "entered the")
            # Replace "achieved a new personal best" with "achieved a new personal best"
            dm_msg = dm_msg.replace("achieved a new personal best", "achieved a new personal best")

        # Channel embed (third person)
        embed = discord.Embed(
            description=msg,
            color=discord.Color.gold()
        )
        embed.timestamp = discord.utils.utcnow()
        embed.set_thumbnail(url=EMBED_THUMBNAIL)

        # DM embed (second person)
        dm_embed = discord.Embed(
            description=dm_msg,
            color=discord.Color.gold()
        )
        dm_embed.timestamp = discord.utils.utcnow()
        dm_embed.set_thumbnail(url=EMBED_THUMBNAIL)

        # Send DM
        if user:
            try:
                await user.send(embed=dm_embed)
            except Exception:
                pass
        # Post to channel with arcade role mention in content
        try:
            await channel.send(content=channel_content, embed=embed)
        except Exception:
            pass

async def setup(bot):
    await bot.add_cog(LeaderboardWatcher(bot))

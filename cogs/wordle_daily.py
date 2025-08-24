import discord
from discord.ext import commands, tasks
import json
import os
from datetime import datetime, timezone, timedelta
import random
from config import EMBED_THUMBNAIL

# Constants
DAILY_WORDLE_CHANNEL_ID = 1397577365957382316  # Replace with your desired channel ID
WINNER_ANNOUNCEMENT_CHANNEL_ID = 1397578103571615774

GAME_DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../game_files/daily_wordle.json")

class DailyWordleGame(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.hackathon_words = [
            "CODES", "BYTES", "DEBUG", "LOGIC", "STACK", "QUERY", "BUILD", 
            "MERGE", "PATCH", "REACT", "LINUX", "MYSQL", "FLASK", "CODER",
            "NODES", "LOOPS", "ARRAY", "CLASS", "HOOKS", "PROPS", "STATE",
            "ASYNC", "AWAIT", "CACHE", "FRAME", "INDEX", "REGEX", "SWIFT",
            "UNITY", "PIXEL", "GRAPH", "PARSE", "TOKEN", "USERS", "ADMIN",
            "NGINX", "REDIS", "KAFKA", "SPARK", "MAVEN", "GRUNT", "BABEL",
            "STYLE", "SCOPE", "EVENT", "MODAL", "FORMS", "VIEWS", "ROUTE",
            "SERVE", "FETCH", "HTTPS", "OAUTH", "TOKEN", "BENCH", "SCALE"
        ]
        self.game_data = self.load_game_data()
        # Add streaks dict if not present
        if "streaks" not in self.game_data:
            self.game_data["streaks"] = {}
        self.daily_reset.start()

    def cog_unload(self):
        self.daily_reset.cancel()

    def load_game_data(self):
        """Load game data from JSON file"""
        if os.path.exists(GAME_DATA_FILE):
            try:
                with open(GAME_DATA_FILE, 'r') as f:
                    data = json.load(f)
                    # Ensure streaks key exists
                    if "streaks" not in data:
                        data["streaks"] = {}
                    return data
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        
        # Create default data structure
        return {
            "current_word": "",
            "current_date": "",
            "winner": None,
            "game_active": True,
            "guesses_today": [],
            "streaks": {}
        }

    def save_game_data(self):
        """Save game data to JSON file"""
        os.makedirs(os.path.dirname(GAME_DATA_FILE), exist_ok=True)
        with open(GAME_DATA_FILE, 'w') as f:
            json.dump(self.game_data, f, indent=2)

    def get_today_date(self):
        """Get today's date in YYYY-MM-DD format"""
        return datetime.now(timezone.utc).strftime('%Y-%m-%d')

    def get_new_daily_word(self):
        """Get a new word for today"""
        return random.choice(self.hackathon_words)

    def reset_daily_game(self):
        """Reset the game for a new day. Update streaks and recalculate top streaks."""
        today = self.get_today_date()
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime('%Y-%m-%d')
        previous_word = self.game_data.get("current_word")
        previous_winner = self.game_data.get("winner")
        streaks = self.game_data.get("streaks", {})

        # If there was no winner yesterday, reset all streaks to 0
        if self.game_data["current_date"] != today:
            if previous_winner and previous_winner.get("date") == yesterday:
                # Increment streak for the winner
                winner_id = str(previous_winner["user_id"])
                streaks[winner_id] = streaks.get(winner_id, 0) + 1
            else:
                # Reset all streaks to 0 if no winner
                streaks = {uid: 0 for uid in streaks}

            # Recalculate top streaks
            self.update_top_streaks(
                streak=max(streaks.values(), default=0),
                user_id=max(streaks, key=streaks.get, default=None),
                username=None  # Username will be updated in `update_top_streaks`
            )

            # Reset game data for the new day
            self.game_data = {
                "current_word": self.get_new_daily_word(),
                "current_date": today,
                "winner": None,
                "game_active": True,
                "guesses_today": [],
                "previous_word": previous_word,
                "previous_day_winner": previous_winner is not None and previous_winner.get("date") == yesterday,
                "streaks": streaks
            }
            self.save_game_data()
            return True, previous_word, previous_winner is not None and previous_winner.get("date") == yesterday
        return False, None, False

    @tasks.loop(minutes=1)  # Check every minute for date change
    async def daily_reset(self):
        """Check if we need to reset for a new day"""
        reset_result = self.reset_daily_game()
        if reset_result[0]:  # If reset happened
            previous_word = reset_result[1]
            had_winner = reset_result[2]
            # Always reveal previous word if there was no winner
            await self.setup_daily_game(previous_word if not had_winner else None)

    @daily_reset.before_loop
    async def before_daily_reset(self):
        await self.bot.wait_until_ready()

    async def setup_daily_game(self, previous_word=None):
        """Set up the daily game in the designated channel"""
        channel = self.bot.get_channel(DAILY_WORDLE_CHANNEL_ID)
        if not channel:
            print(f"Could not find daily wordle channel with ID: {DAILY_WORDLE_CHANNEL_ID}")
            return

        # If there was a previous word that wasn't guessed, reveal it
        if previous_word:
            reveal_embed = discord.Embed(
                title="📝 Yesterday's Word Revealed",
                description=f"Nobody guessed yesterday's word!\n\nThe word was: **{previous_word}**",
                color=discord.Color.orange()
            )
            reveal_embed.set_thumbnail(url=EMBED_THUMBNAIL)
            await channel.send(embed=reveal_embed)

        # Create the game display
        view = discord.ui.View()
        for i in range(5):
            button = discord.ui.Button(label="\u200b", style=discord.ButtonStyle.secondary)
            view.add_item(button)

        embed = discord.Embed(
            title="🎯 Daily Hackathon Wordle Challenge!",
            description=f"**Date:** {self.game_data['current_date']}\n\nGuess today's 5-letter hackathon-related word!\nFirst correct guess wins! 🏆",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="How to Play", 
            value="• Type a 5-letter word related to hackathons/coding\n• Green = Correct letter in correct position\n• Red = Correct letter in wrong position\n• Gray = Letter not in word\n• First correct guess wins the day!", 
            inline=False
        )
        embed.add_field(
            name="Status", 
            value="🟢 Game Active - Good luck!", 
            inline=False
        )
        embed.set_thumbnail(url=EMBED_THUMBNAIL)
        embed.set_footer(text="New word every day at midnight UTC!")

        await channel.send(embed=embed, view=view)

    @commands.Cog.listener()
    async def on_ready(self):
        """Set up the game when bot comes online"""
        # Reset game if needed and get previous word info
        reset_result = self.reset_daily_game()
        
        # Set up the daily game, revealing previous word if no one won
        if reset_result[0]:  # If reset happened
            previous_word = reset_result[1]
            had_winner = reset_result[2]
            await self.setup_daily_game(previous_word if not had_winner else None)
        else:
            # If bot restarts in the middle of the day, check if yesterday's word needs to be revealed
            if self.game_data.get("previous_word") and not self.game_data.get("previous_day_winner"):
                await self.setup_daily_game(self.game_data.get("previous_word"))
                # Clear previous_word after revealing
                self.game_data["previous_word"] = None
                self.save_game_data()
            else:
                await self.setup_daily_game()

    @commands.Cog.listener()
    async def on_message(self, message):
        """Handle guesses in the daily wordle channel"""
        # Ignore bot messages
        if message.author.bot:
            return

        # Only process messages in the daily wordle channel
        if message.channel.id != DAILY_WORDLE_CHANNEL_ID:
            return

        # Delete non-5-letter-word messages
        content = message.content.strip().upper()
        if len(content) != 5 or not content.isalpha():
            try:
                await message.delete()
            except discord.NotFound:
                pass
            return

        # Check if game is still active
        if not self.game_data["game_active"] or self.game_data["winner"]:
            try:
                await message.delete()
                # Send temporary message about game being over
                temp_msg = await message.channel.send(
                    embed=discord.Embed(
                        title="Game Over",
                        description="Today's game has already been won! New word tomorrow at midnight UTC.",
                        color=discord.Color.red()
                    ).set_thumbnail(url=EMBED_THUMBNAIL),
                    delete_after=5
                )
            except discord.NotFound:
                pass
            return

        # Process the guess
        await self.process_guess(message, content)

    async def process_guess(self, message, guess):
        """Process a user's guess"""
        try:
            # Check if user already guessed this word today
            user_id = str(message.author.id)
            if guess in self.game_data["guesses_today"]:
                await message.delete()
                temp_msg = await message.channel.send(
                    embed=discord.Embed(
                        title="Already Guessed",
                        description="This word has already been guessed today!",
                        color=discord.Color.orange()
                    ).set_thumbnail(url=EMBED_THUMBNAIL),
                    delete_after=5
                )
                return

            # Add guess to today's guesses
            self.game_data["guesses_today"].append(guess)
            
            target_word = self.game_data["current_word"]
            
            # Check if it's the correct guess
            if guess == target_word:
                await self.handle_winner(message, guess)
                return

            # Create visual feedback for incorrect guess
            button_styles = []
            for i in range(5):
                if guess[i] == target_word[i]:
                    button_styles.append(discord.ButtonStyle.success)  # Green - correct position
                elif guess[i] in target_word:
                    button_styles.append(discord.ButtonStyle.danger)   # Red - wrong position
                else:
                    button_styles.append(discord.ButtonStyle.secondary) # Gray - not in word

            # Create view with the guess result
            view = discord.ui.View()
            for i in range(5):
                button = discord.ui.Button(label=guess[i], style=button_styles[i])
                view.add_item(button)

            # Create embed for the guess
            embed = discord.Embed(
                title="Guess Result",
                description=f"{message.author.mention} guessed: **{guess}**",
                color=discord.Color.yellow()
            )
            embed.add_field(
                name="Legend",
                value="🟢 Green = Right letter, right spot\n🔴 Red = Right letter, wrong spot\n⚫ Gray = Not in word",
                inline=False
            )
            embed.set_thumbnail(url=EMBED_THUMBNAIL)

            await message.channel.send(embed=embed, view=view)
            await message.delete()
            
            # Save the updated game data
            self.save_game_data()

        except Exception as e:
            print(f"Error processing guess: {e}")
            try:
                await message.delete()
            except:
                pass

    def update_top_streaks(self, streak, user_id, username):
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        new_entry = {
            "max_streak": streak,
            "user_id": user_id,
            "username": username,
            "date": today
        }
        # Store top streaks in the same file as game data
        # Load the main game data file
        if os.path.exists(GAME_DATA_FILE):
            try:
                with open(GAME_DATA_FILE, "r") as f:
                    data = json.load(f)
            except Exception:
                data = {}
        else:
            data = {}

        # Ensure top_streaks exists
        top_streaks = data.get("top_streaks", [])
        
        # Check if user already exists in top_streaks
        user_exists = False
        for i, entry in enumerate(top_streaks):
            if entry["user_id"] == user_id:
                user_exists = True
                # Only update if the new streak is higher
                if streak > entry["max_streak"]:
                    top_streaks[i] = new_entry
                break
        
        # If user doesn't exist in top_streaks, add them
        if not user_exists:
            top_streaks.append(new_entry)
            
        # Sort by max_streak DESC, then most recent date
        top_streaks = sorted(top_streaks, key=lambda x: (-x["max_streak"], x["date"]))[:3]
        data["top_streaks"] = top_streaks

        # Save back to the same file
        os.makedirs(os.path.dirname(GAME_DATA_FILE), exist_ok=True)
        with open(GAME_DATA_FILE, "w") as f:
            json.dump(data, f, indent=2)

    async def handle_winner(self, message, correct_guess):
        """Handle when someone wins the daily challenge and update streaks"""
        try:
            user_id = str(message.author.id)
            today = self.get_today_date()
            streaks = self.game_data.get("streaks", {})

            # Find the current highest streak and its owner (excluding the current winner)
            highest_streak = 0
            highest_streak_user = None
            for uid, streak in streaks.items():
                if uid != user_id and streak > highest_streak:
                    highest_streak = streak
                    highest_streak_user = uid

            # If someone else has a streak, steal it
            if highest_streak_user and highest_streak > 0:
                # Winner gets a new streak of 1 (not previous streak + 1)
                streaks[user_id] = 1
                # Previous streak holder's streak resets to 0
                streaks[highest_streak_user] = 0
                streak_stolen = True
                stolen_from = highest_streak_user
                stolen_count = highest_streak
            else:
                # No streak to steal, start/continue own streak
                streaks[user_id] = streaks.get(user_id, 0) + 1
                streak_stolen = False
                stolen_from = None
                stolen_count = 0

            # Update game data
            self.game_data["winner"] = {
                "user_id": message.author.id,
                "username": str(message.author),
                "guess": correct_guess,
                "date": today
            }
            self.game_data["game_active"] = False
            self.game_data["streaks"] = streaks
            self.save_game_data()

            streak_count = streaks.get(user_id, 0)

            # Update top streaks JSON if this is a new personal best
            if streak_count > 0:
                self.update_top_streaks(
                    streak=streak_count,
                    user_id=message.author.id,
                    username=str(message.author)
                )

            # DM previous streak holder if streak was stolen
            if streak_stolen and stolen_from:
                prev_member = message.guild.get_member(int(stolen_from))
                if prev_member:
                    try:
                        embed = discord.Embed(
                            title="😢 Your Wordle Streak Was Ended!",
                            description=(
                                f"Your {stolen_count} day Wordle streak was ended by "
                                f"{message.author.display_name}!\n"
                                f"Try to start a new streak tomorrow!"
                            ),
                            color=discord.Color.red()
                        )
                        embed.set_thumbnail(url=EMBED_THUMBNAIL)
                        await prev_member.send(embed=embed)
                    except Exception as e:
                        print(f"Failed to DM previous streak holder: {e}")

            # Create winner view
            view = discord.ui.View()
            for i in range(5):
                button = discord.ui.Button(label=correct_guess[i], style=discord.ButtonStyle.success)
                view.add_item(button)

            # Winner announcement in the game channel
            winner_embed = discord.Embed(
                title="🎉 WINNER! 🎉",
                description=f"**{message.author.mention} got it right!**\n\nThe word was: **{correct_guess}**\n\nCongratulations! 🏆",
                color=discord.Color.gold()
            )
            if streak_stolen and stolen_from:
                winner_embed.add_field(
                    name="Streak Ended!",
                    value=(
                        f"<@{user_id}> ended a {stolen_count} day streak held by <@{stolen_from}>!"
                    ),
                    inline=False
                )
            else:
                winner_embed.add_field(
                    name="Streak",
                    value=f"{message.author.display_name} is on a {streak_count} day streak! 🔥",
                    inline=True
                )
            winner_embed.set_thumbnail(url=EMBED_THUMBNAIL)
            winner_embed.set_footer(text="New word tomorrow at midnight UTC!")

            await message.channel.send(embed=winner_embed, view=view)
            await message.delete()

            # Announcement in the winner channel
            announcement_channel = self.bot.get_channel(WINNER_ANNOUNCEMENT_CHANNEL_ID)
            if announcement_channel:
                role_mention = "<@&1406096504850223276>"
                announcement_embed = discord.Embed(
                    title="🏆 Daily Wordle Champion!",
                    description=f"**{message.author.mention}** won today's Daily Hackathon Wordle!\n\n**Word:** {correct_guess}\n**Date:** {self.get_today_date()}",
                )
                if streak_stolen and stolen_from:
                    announcement_embed.add_field(
                        name="Streak Ended!",
                        value=(
                            f"<@{user_id}> ended a {stolen_count} day streak held by <@{stolen_from}>!"
                        ),
                        inline=False
                    )
                else:
                    announcement_embed.add_field(
                        name="Streak",
                        value=f"{message.author.display_name} is on a {streak_count} day streak! 🔥",
                        inline=False
                    )
                announcement_embed.set_thumbnail(url=EMBED_THUMBNAIL)
                await announcement_channel.send(content=role_mention, embed=announcement_embed)

        except Exception as e:
            print(f"Error handling winner: {e}")

    @commands.hybrid_command(name="daily_wordle_status", with_app_command=True)
    async def daily_status(self, ctx):
        """Check the status of today's daily wordle"""
        # Reload the latest game data from file
        if os.path.exists(GAME_DATA_FILE):
            try:
                with open(GAME_DATA_FILE, 'r') as f:
                    self.game_data = json.load(f)
            except Exception:
                pass

        embed = discord.Embed(
            title="📊 Daily Wordle Status",
            color=discord.Color.blue()
        )
        embed.add_field(name="Date", value=self.game_data["current_date"], inline=True)
        embed.add_field(name="Total Guesses", value=str(len(self.game_data["guesses_today"])), inline=True)
        
        if self.game_data["winner"]:
            embed.add_field(name="Winner", value=f"<@{self.game_data['winner']['user_id']}>", inline=True)
            embed.add_field(name="Winning Word", value=self.game_data["winner"]["guess"], inline=True)
            # Show streak if available
            streaks = self.game_data.get("streaks", {})
            winner_id = str(self.game_data["winner"]["user_id"])
            streak_count = streaks.get(winner_id, 0)
            member = ctx.guild.get_member(int(winner_id))
            winner_name = member.display_name if member else f"User {winner_id}"
            embed.add_field(
                name="Streak",
                value=f"{winner_name} is on a {streak_count} day streak! 🔥",
                inline=False
            )
            embed.color = discord.Color.gold()
        else:
            embed.add_field(name="Status", value="🟢 Active", inline=True)
            embed.add_field(name="Word Length", value="5 letters", inline=True)
        
        embed.set_thumbnail(url=EMBED_THUMBNAIL)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="reset_daily_wordle", with_app_command=True)
    @commands.has_permissions(administrator=True)
    async def force_reset(self, ctx):
        """Force reset the daily wordle (Admin only)"""
        self.game_data = {
            "current_word": self.get_new_daily_word(),
            "current_date": self.get_today_date(), 
            "winner": None,
            "game_active": True,
            "guesses_today": [],
            "streaks": self.game_data.get("streaks", {})
        }
        self.save_game_data()
        
        embed = discord.Embed(
            title="🔄 Daily Wordle Reset",
            description="The daily wordle has been reset with a new word!",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=EMBED_THUMBNAIL)
        await ctx.send(embed=embed)
        
        await self.setup_daily_game()

async def setup(bot):
    await bot.add_cog(DailyWordleGame(bot))
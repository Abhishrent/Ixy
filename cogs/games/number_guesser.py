import discord
from discord.ext import commands, tasks
import json
import os
import random
import asyncio

GAME_DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "game_files/number_guesser.json")
GUESS_CHANNEL_ID = 1130051976667865095  # Channel where guess embeds are sent

def load_scores():
    if os.path.exists(GAME_DATA_FILE):
        try:
            with open(GAME_DATA_FILE, "r") as f:
                data = json.load(f)
                # Return both scores and active game if they exist
                return data.get("scores", {}), data.get("active_game", None)
        except Exception:
            pass
    return {}, None

def save_data(scores, active_game=None):
    os.makedirs(os.path.dirname(GAME_DATA_FILE), exist_ok=True)
    data = {
        "scores": scores,
        "active_game": active_game
    }
    with open(GAME_DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

class GuessNumber(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.scores, saved_game = load_scores()
        self.active_games = {}
        
        # Restore active game if it exists
        if saved_game:
            self.active_games[saved_game["channel_id"]] = saved_game
            
        self.random_game_drop.start()

    def cog_unload(self):
        self.random_game_drop.cancel()

    @tasks.loop(minutes=1)  # Check every minute
    async def random_game_drop(self):
        """Randomly start a number guessing game"""
        # Only start if no active game in the guess channel
        if GUESS_CHANNEL_ID in self.active_games:
            return
            
        # 1% chance every minute (roughly 1 game per 1.5-2 hours on average)
        if random.randint(1, 100) <= 1:
            await self.start_random_game()

    @random_game_drop.before_loop
    async def before_random_game_drop(self):
        await self.bot.wait_until_ready()
        await asyncio.sleep(5)

    async def start_random_game(self):
        """Start a random number guessing game"""
        # Fixed range for random drops
        min_num, max_num = 1, 1000
        
        secret_number = random.randint(min_num, max_num)
        game_data = {
            "secret_number": secret_number,
            "min_range": min_num,
            "max_range": max_num,
            "attempts": 0,
            "starter": self.bot.user.id,  # Bot started this game
            "channel_id": GUESS_CHANNEL_ID,
            "is_random_drop": True
        }
        self.active_games[GUESS_CHANNEL_ID] = game_data
        
        # Save game state
        save_data(self.scores, game_data)

        # Send game embed to the guess channel
        guess_channel = self.bot.get_channel(GUESS_CHANNEL_ID)
        if guess_channel:
            embed = discord.Embed(
                title="🎲 Random Number Drop! 🎯",
                description=f"**A wild number appears!**\n\nI'm thinking of a number between **{min_num}** and **{max_num}**!\n\nMake your guess by typing a number!",
                color=discord.Color.purple()
            )
            embed.add_field(
                name="How to Play",
                value="• Type a number to guess\n• I'll tell you if it's higher or lower\n• First person to guess correctly wins!",
                inline=False
            )
            embed.set_footer(text="🎲 Random game drop! Good luck!")
            await guess_channel.send(embed=embed)

    @commands.hybrid_command(name="guess_number", with_app_command=True)
    async def start_game(self, ctx, min_num: int = 1, max_num: int = 1000):
        """Start a guess the number game"""
        # Check if there's already an active game in the guess channel (where all games are played)
        if GUESS_CHANNEL_ID in self.active_games:
            await ctx.send("❌ A game is already active!")
            return

        if min_num >= max_num:
            await ctx.send("❌ Minimum number must be less than maximum number!")
            return

        secret_number = random.randint(min_num, max_num)
        game_data = {
            "secret_number": secret_number,
            "min_range": min_num,
            "max_range": max_num,
            "attempts": 0,
            "starter": ctx.author.id,
            "channel_id": GUESS_CHANNEL_ID  # Always use the guess channel
        }
        self.active_games[GUESS_CHANNEL_ID] = game_data
        
        # Save game state
        save_data(self.scores, game_data)

        # Send initial embed to the designated guess channel
        guess_channel = self.bot.get_channel(GUESS_CHANNEL_ID)
        if guess_channel:
            embed = discord.Embed(
                title="🎯 Guess the Number Game!",
                description=f"I'm thinking of a number between **{min_num}** and **{max_num}**!\n\nMake your guess by typing a number!",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="How to Play",
                value="• Type a number to guess\n• I'll tell you if it's higher or lower\n• First person to guess correctly wins!",
                inline=False
            )
            embed.set_footer(text=f"Game started by {ctx.author.display_name}")
            await guess_channel.send(embed=embed)
        
        await ctx.send(f"✅ Number guessing game started! Check <#{GUESS_CHANNEL_ID}> to play.")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
            
        # Only process messages in the guess channel
        if message.channel.id != GUESS_CHANNEL_ID:
            return
            
        # Check if there's an active game in the guess channel
        if GUESS_CHANNEL_ID not in self.active_games:
            return
            
        # Get the active game from the guess channel
        game = self.active_games[GUESS_CHANNEL_ID]
        content = message.content.strip()

        # Check if the message is a number
        if content.isdigit():
            guess = int(content)
            game["attempts"] += 1
            
            # Save updated game state
            save_data(self.scores, game)
            
            if guess == game["secret_number"]:
                # Winner!
                user_id = str(message.author.id)
                self.scores[user_id] = self.scores.get(user_id, 0) + 1
                
                # Clear active game and save
                save_data(self.scores, None)

                # Different embed for random drops
                if game.get("is_random_drop"):
                    title = "🎲🎉 Random Drop Winner! 🎉🎲"
                    description = f"**{message.author.mention} caught the random number!**\n\n**The number was: {game['secret_number']}**\n**Attempts: {game['attempts']}**"
                else:
                    title = "🎉 WINNER! 🎉"
                    description = f"**{message.author.mention} guessed the correct number!**\n\n**The number was: {game['secret_number']}**\n**Attempts: {game['attempts']}**"

                embed = discord.Embed(
                    title=title,
                    description=description,
                    color=discord.Color.gold()
                )
                embed.set_thumbnail(url=message.author.display_avatar.url)
                await message.channel.send(embed=embed)
                
                del self.active_games[GUESS_CHANNEL_ID]
                return
            
            elif guess < game["secret_number"]:
                # Too low
                embed = discord.Embed(
                    title="📈 Higher!",
                    description=f"**{guess}** is too low! Try a higher number.\n\n**Range:** {game['min_range']} - {game['max_range']}\n**Attempts:** {game['attempts']}",
                    color=discord.Color.orange()
                )
                await message.channel.send(embed=embed)
                
            else:
                # Too high
                embed = discord.Embed(
                    title="📉 Lower!",
                    description=f"**{guess}** is too high! Try a lower number.\n\n**Range:** {game['min_range']} - {game['max_range']}\n**Attempts:** {game['attempts']}",
                    color=discord.Color.orange()
                )
                await message.channel.send(embed=embed)

    @commands.hybrid_command(name="stop_number_game", with_app_command=True)
    async def stop_game(self, ctx):
        """Stop the current number guessing game"""
        if GUESS_CHANNEL_ID not in self.active_games:
            await ctx.send("❌ No active game!")
            return

        game = self.active_games[GUESS_CHANNEL_ID]
        if ctx.author.id != game["starter"] and not ctx.author.guild_permissions.manage_messages:
            await ctx.send("❌ Only the game starter or moderators can stop the game!")
            return

        # Clear active game and save
        save_data(self.scores, None)
        
        embed = discord.Embed(
            title="🛑 Game Stopped",
            description=f"The number guessing game has been stopped.\n**The secret number was: {game['secret_number']}**",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        del self.active_games[GUESS_CHANNEL_ID]

    @commands.hybrid_command(name="number_scores", with_app_command=True)
    async def show_scores(self, ctx):
        """Show the number guessing game leaderboard"""
        if not self.scores:
            await ctx.send("No scores yet!")
            return

        sorted_scores = sorted(self.scores.items(), key=lambda x: -x[1])[:10]
        desc = "\n".join([f"<@{uid}>: {score} wins" for uid, score in sorted_scores])
        
        embed = discord.Embed(
            title="🏆 Number Guessing Leaderboard",
            description=desc,
            color=discord.Color.gold()
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(GuessNumber(bot))
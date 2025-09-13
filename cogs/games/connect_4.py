import discord
from discord.ext import commands, tasks
import json
import os
import time
import asyncio
from config import EMBED_THUMBNAIL

GAME_DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "game_files/connect_4.json")

def load_scores():
    if os.path.exists(GAME_DATA_FILE):
        try:
            with open(GAME_DATA_FILE, "r") as f:
                data = json.load(f)
                return data.get("scores", {}), data.get("active_games", {})
        except Exception:
            pass
    return {}, {}

def save_data(scores, active_games):
    os.makedirs(os.path.dirname(GAME_DATA_FILE), exist_ok=True)
    data = {
        "scores": scores,
        "active_games": active_games
    }
    with open(GAME_DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

class Connect4(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.scores, self.active_games = load_scores()
        self.timeout_check.start()  # Start the timeout checker
        
    def cog_unload(self):
        self.timeout_check.cancel()
        
    @tasks.loop(minutes=2)  # Check every 2 minutes
    async def timeout_check(self):
        """Check for timed out games and clean them up"""
        current_time = time.time()
        expired_games = []
        
        for channel_id, game in self.active_games.items():
            # Check if game has been inactive for more than 10 minutes
            if current_time - game.get("last_move", game.get("start_time", current_time)) > 600:  # 10 minutes
                expired_games.append(channel_id)
        
        # Clean up expired games
        for channel_id in expired_games:
            game = self.active_games[channel_id]
            channel = self.bot.get_channel(game["channel_id"])
            
            if channel:
                embed = discord.Embed(
                    title="⏰ Connect 4 Game Timed Out",
                    description="The game has been automatically ended due to inactivity (10 minutes).",
                    color=discord.Color.orange()
                )
                embed.add_field(
                    name="Final Board",
                    value=self.display_board(game["board"]),
                    inline=False
                )
                await channel.send(embed=embed)
            
            del self.active_games[channel_id]
        
        # Save updated games
        if expired_games:
            save_data(self.scores, self.active_games)
    
    @timeout_check.before_loop
    async def before_timeout_check(self):
        await self.bot.wait_until_ready()
        
    def create_board(self):
        """Create an empty 7x6 Connect 4 board"""
        return [['⚫' for _ in range(7)] for _ in range(6)]
    
    def display_board(self, board):
        """Convert board to visual string representation"""
        # Column numbers
        board_str = "```\n 1️⃣2️⃣3️⃣4️⃣5️⃣6️⃣7️⃣\n"
        
        # Board rows
        for row in board:
            board_str += "│"
            for cell in row:
                board_str += cell
            board_str += "│\n"
        
        board_str += "```"
        return board_str
    
    def drop_piece(self, board, column, player_piece):
        """Drop a piece in the specified column. Returns True if successful."""
        if column < 0 or column > 6:
            return False
        
        # Check if column is full
        if board[0][column] != '⚫':
            return False
        
        # Drop the piece to the lowest available row
        for row in range(5, -1, -1):
            if board[row][column] == '⚫':
                board[row][column] = player_piece
                return True
        
        return False
    
    def check_winner(self, board, piece):
        """Check if the specified piece has won"""
        rows, cols = 6, 7
        
        # Check horizontal
        for row in range(rows):
            for col in range(cols - 3):
                if all(board[row][col + i] == piece for i in range(4)):
                    return True
        
        # Check vertical
        for row in range(rows - 3):
            for col in range(cols):
                if all(board[row + i][col] == piece for i in range(4)):
                    return True
        
        # Check diagonal (top-left to bottom-right)
        for row in range(rows - 3):
            for col in range(cols - 3):
                if all(board[row + i][col + i] == piece for i in range(4)):
                    return True
        
        # Check diagonal (top-right to bottom-left)
        for row in range(rows - 3):
            for col in range(3, cols):
                if all(board[row + i][col - i] == piece for i in range(4)):
                    return True
        
        return False
    
    def is_board_full(self, board):
        """Check if the board is full (tie game)"""
        return all(board[0][col] != '⚫' for col in range(7))
    
    @commands.hybrid_command(name="connect4", with_app_command=True)
    async def start_connect4(self, ctx, opponent: discord.Member):
        """Start a Connect 4 game with another player"""
        if opponent.bot:
            await ctx.send("❌ You can't play against a bot!")
            return
        
        if opponent.id == ctx.author.id:
            await ctx.send("❌ You can't play against yourself!")
            return
        
        channel_id = str(ctx.channel.id)
        
        # Check if there's already a game in this channel
        if channel_id in self.active_games:
            await ctx.send("❌ There's already a Connect 4 game in this channel!")
            return
        
        # Create new game
        board = self.create_board()
        current_time = time.time()
        game_data = {
            "board": board,
            "player1": ctx.author.id,
            "player2": opponent.id,
            "current_turn": ctx.author.id,
            "player1_piece": "🔴",
            "player2_piece": "🟡",
            "channel_id": ctx.channel.id,
            "start_time": current_time,
            "last_move": current_time,
            "game_message_id": None  # Will store the message ID to edit
        }
        
        self.active_games[channel_id] = game_data
        save_data(self.scores, self.active_games)
        
        embed = discord.Embed(
            title="🔴🟡 Connect 4 Game Started! 🟡🔴",
            description=f"**{ctx.author.display_name}** 🔴 vs **{opponent.display_name}** 🟡\n\n{ctx.author.mention}'s turn!",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="Game Board",
            value=self.display_board(board),
            inline=False
        )
        embed.add_field(
            name="How to Play",
            value="Type a number (1-7) to drop your piece in that column!\nGet 4 in a row to win! (horizontal, vertical, or diagonal)",
            inline=False
        )
        embed.set_thumbnail(url=EMBED_THUMBNAIL)
        embed.set_footer(text="Connect 4 • First to 4 in a row wins! • 10min timeout")
        
        # Send initial message and store its ID for editing
        game_message = await ctx.send(embed=embed)
        game_data["game_message_id"] = game_message.id
        save_data(self.scores, self.active_games)
    
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        
        channel_id = str(message.channel.id)
        
        # Check if there's an active game in this channel
        if channel_id not in self.active_games:
            return
        
        game = self.active_games[channel_id]
        
        # Check if it's the player's turn
        if message.author.id != game["current_turn"]:
            return
        
        # Check if message is a valid column number
        content = message.content.strip()
        if not content.isdigit():
            return
        
        column = int(content) - 1  # Convert to 0-based index
        
        if column < 0 or column > 6:
            await message.channel.send("❌ Please choose a column between 1 and 7!")
            return
        
        # Determine current player's piece
        current_piece = game["player1_piece"] if message.author.id == game["player1"] else game["player2_piece"]
        
        # Try to drop the piece
        if not self.drop_piece(game["board"], column, current_piece):
            await message.channel.send("❌ That column is full! Choose another column.")
            return
        
        # Update last move time
        game["last_move"] = time.time()
        
        # Check for winner
        if self.check_winner(game["board"], current_piece):
            # We have a winner!
            winner_id = str(message.author.id)
            self.scores[winner_id] = self.scores.get(winner_id, 0) + 1
            
            embed = discord.Embed(
                title="🎉 CONNECT 4 WINNER! 🎉",
                description=f"**{message.author.display_name}** wins with {current_piece}!",
                color=discord.Color.gold()
            )
            embed.add_field(
                name="Final Board",
                value=self.display_board(game["board"]),
                inline=False
            )
            embed.set_thumbnail(url=message.author.display_avatar.url)
            
            # Clean up game
            del self.active_games[channel_id]
            save_data(self.scores, self.active_games)
            
            await message.channel.send(embed=embed)
            return
        
        # Check for tie
        if self.is_board_full(game["board"]):
            embed = discord.Embed(
                title="🤝 It's a Tie!",
                description="The board is full! Nobody wins this round.",
                color=discord.Color.orange()
            )
            embed.add_field(
                name="Final Board",
                value=self.display_board(game["board"]),
                inline=False
            )
            
            # Clean up game
            del self.active_games[channel_id]
            save_data(self.scores, self.active_games)
            
            await message.channel.send(embed=embed)
            return
        
        # Switch turns
        game["current_turn"] = game["player2"] if game["current_turn"] == game["player1"] else game["player1"]
        next_player = self.bot.get_user(game["current_turn"])
        
        # Save updated game state
        save_data(self.scores, self.active_games)
        
        # Update the original embed message instead of sending a new one
        embed = discord.Embed(
            title="🔴🟡 Connect 4 Game 🟡🔴",
            description=f"**{next_player.display_name}'s** turn! ({game['player1_piece'] if game['current_turn'] == game['player1'] else game['player2_piece']})",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="Game Board",
            value=self.display_board(game["board"]),
            inline=False
        )
        embed.add_field(
            name="Next Move",
            value="Type a number (1-7) to drop your piece!",
            inline=False
        )
        embed.set_thumbnail(url=EMBED_THUMBNAIL)
        embed.set_footer(text="Connect 4 • First to 4 in a row wins! • 10min timeout")
        
        # Edit the original message instead of sending a new one
        try:
            if game.get("game_message_id"):
                game_message = await message.channel.fetch_message(game["game_message_id"])
                await game_message.edit(embed=embed)
            else:
                # Fallback: send new message if original is lost
                new_message = await message.channel.send(embed=embed)
                game["game_message_id"] = new_message.id
                save_data(self.scores, self.active_games)
        except discord.NotFound:
            # Original message was deleted, send a new one
            new_message = await message.channel.send(embed=embed)
            game["game_message_id"] = new_message.id
            save_data(self.scores, self.active_games)
    
    @commands.hybrid_command(name="stop_connect4", with_app_command=True)
    async def stop_connect4(self, ctx):
        """Stop the current Connect 4 game"""
        channel_id = str(ctx.channel.id)
        
        if channel_id not in self.active_games:
            await ctx.send("❌ No active Connect 4 game in this channel!")
            return
        
        game = self.active_games[channel_id]
        
        # Check if user is one of the players or has manage permissions
        if (ctx.author.id not in [game["player1"], game["player2"]] and 
            not ctx.author.guild_permissions.manage_messages):
            await ctx.send("❌ Only the players or moderators can stop the game!")
            return
        
        embed = discord.Embed(
            title="🛑 Connect 4 Game Stopped",
            description="The game has been stopped.",
            color=discord.Color.red()
        )
        embed.add_field(
            name="Final Board",
            value=self.display_board(game["board"]),
            inline=False
        )
        
        del self.active_games[channel_id]
        save_data(self.scores, self.active_games)
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="connect4_scores", with_app_command=True)
    async def show_connect4_scores(self, ctx):
        """Show Connect 4 leaderboard"""
        if not self.scores:
            await ctx.send("No Connect 4 scores yet!")
            return
        
        sorted_scores = sorted(self.scores.items(), key=lambda x: -x[1])[:10]
        desc = "\n".join([f"<@{uid}>: {score} wins" for uid, score in sorted_scores])
        
        embed = discord.Embed(
            title="🏆 Connect 4 Leaderboard",
            description=desc,
            color=discord.Color.gold()
        )
        embed.set_thumbnail(url=EMBED_THUMBNAIL)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Connect4(bot))
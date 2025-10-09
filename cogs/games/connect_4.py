import discord
from discord.ext import commands, tasks
import json
import os
import time
import asyncio
import random
from config import EMBED_THUMBNAIL, BOT_NAME

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
    
    def get_ai_move(self, board, difficulty, ai_piece, player_piece):
        """Get AI move based on difficulty level"""
        if difficulty == "easy":
            return self._easy_ai_move(board)
        elif difficulty == "normal":
            return self._normal_ai_move(board, ai_piece, player_piece)
        elif difficulty == "hard":
            return self._hard_ai_move(board, ai_piece, player_piece)
        else:
            return self._easy_ai_move(board)
    
    def _easy_ai_move(self, board):
        """Easy AI - just picks a random valid column"""
        valid_columns = [col for col in range(7) if board[0][col] == '⚫']
        return random.choice(valid_columns) if valid_columns else None
    
    def _normal_ai_move(self, board, ai_piece, player_piece):
        """Normal AI - blocks player wins and goes for easy wins"""
        # First, check if AI can win
        for col in range(7):
            if board[0][col] == '⚫':  # Column not full
                # Try placing AI piece
                temp_board = [row[:] for row in board]
                if self.drop_piece(temp_board, col, ai_piece):
                    if self.check_winner(temp_board, ai_piece):
                        return col
        
        # Second, check if AI needs to block player
        for col in range(7):
            if board[0][col] == '⚫':  # Column not full
                # Try placing player piece
                temp_board = [row[:] for row in board]
                if self.drop_piece(temp_board, col, player_piece):
                    if self.check_winner(temp_board, player_piece):
                        return col
        
        # Otherwise, prefer center columns
        center_columns = [3, 2, 4, 1, 5, 0, 6]
        for col in center_columns:
            if board[0][col] == '⚫':
                return col
        
        return None
    
    def _hard_ai_move(self, board, ai_piece, player_piece):
        """Hard AI - uses minimax algorithm with depth 4"""
        best_col = None
        best_score = float('-inf')
        
        for col in range(7):
            if board[0][col] == '⚫':  # Column not full
                temp_board = [row[:] for row in board]
                if self.drop_piece(temp_board, col, ai_piece):
                    score = self._minimax(temp_board, 4, False, ai_piece, player_piece, float('-inf'), float('inf'))
                    if score > best_score:
                        best_score = score
                        best_col = col
        
        return best_col
    
    def _minimax(self, board, depth, is_maximizing, ai_piece, player_piece, alpha, beta):
        """Minimax algorithm with alpha-beta pruning"""
        # Check terminal states
        if self.check_winner(board, ai_piece):
            return 100 + depth  # AI wins (prefer quicker wins)
        if self.check_winner(board, player_piece):
            return -100 - depth  # Player wins (prefer slower losses)
        if self.is_board_full(board) or depth == 0:
            return self._evaluate_board(board, ai_piece, player_piece)
        
        if is_maximizing:  # AI's turn
            max_eval = float('-inf')
            for col in range(7):
                if board[0][col] == '⚫':
                    temp_board = [row[:] for row in board]
                    if self.drop_piece(temp_board, col, ai_piece):
                        eval_score = self._minimax(temp_board, depth - 1, False, ai_piece, player_piece, alpha, beta)
                        max_eval = max(max_eval, eval_score)
                        alpha = max(alpha, eval_score)
                        if beta <= alpha:
                            break  # Alpha-beta pruning
            return max_eval
        else:  # Player's turn
            min_eval = float('inf')
            for col in range(7):
                if board[0][col] == '⚫':
                    temp_board = [row[:] for row in board]
                    if self.drop_piece(temp_board, col, player_piece):
                        eval_score = self._minimax(temp_board, depth - 1, True, ai_piece, player_piece, alpha, beta)
                        min_eval = min(min_eval, eval_score)
                        beta = min(beta, eval_score)
                        if beta <= alpha:
                            break  # Alpha-beta pruning
            return min_eval
    
    def _evaluate_board(self, board, ai_piece, player_piece):
        """Evaluate board position for minimax"""
        score = 0
        
        # Check all possible 4-in-a-row positions
        for row in range(6):
            for col in range(7):
                # Horizontal
                if col <= 3:
                    window = [board[row][col + i] for i in range(4)]
                    score += self._evaluate_window(window, ai_piece, player_piece)
                
                # Vertical
                if row <= 2:
                    window = [board[row + i][col] for i in range(4)]
                    score += self._evaluate_window(window, ai_piece, player_piece)
                
                # Diagonal (positive slope)
                if row <= 2 and col <= 3:
                    window = [board[row + i][col + i] for i in range(4)]
                    score += self._evaluate_window(window, ai_piece, player_piece)
                
                # Diagonal (negative slope)
                if row >= 3 and col <= 3:
                    window = [board[row - i][col + i] for i in range(4)]
                    score += self._evaluate_window(window, ai_piece, player_piece)
        
        return score
    
    def _evaluate_window(self, window, ai_piece, player_piece):
        """Evaluate a 4-piece window"""
        score = 0
        ai_count = window.count(ai_piece)
        player_count = window.count(player_piece)
        empty_count = window.count('⚫')
        
        if ai_count == 4:
            score += 100
        elif ai_count == 3 and empty_count == 1:
            score += 10
        elif ai_count == 2 and empty_count == 2:
            score += 2
        
        if player_count == 3 and empty_count == 1:
            score -= 80
        elif player_count == 2 and empty_count == 2:
            score -= 2
        
        return score
    
    @commands.hybrid_group(name="connect_4", description="Connect 4 game commands.")
    async def connect_4(self, ctx):
        """Connect 4 game commands."""
        if ctx.invoked_subcommand is None:
            await ctx.send("Please use a subcommand. Available: `start`, `stop`, `scores`")

    @connect_4.command(name="start", description="Start a Connect 4 game against another player or AI")
    async def start(self, ctx, player1: discord.Member = None, player2: discord.Member = None, difficulty: str = "normal"):
        """Start a Connect 4 game against another player or AI
        
        Args:
            player1: First player (defaults to command user)
            player2: Second player (leave empty for AI, or specify a player)
            difficulty: AI difficulty level (easy, normal, hard) - only used when playing against AI
        """
        channel_id = str(ctx.channel.id)
        
        # Check if there's already a game in this channel
        if channel_id in self.active_games:
            await ctx.send("❌ There's already a Connect 4 game in this channel!")
            return
        
        # Default player1 to the user who used the command
        player1 = player1 or ctx.author
        is_ai_game = player2 is None
        
        # Determine player2
        player2 = player2 if not is_ai_game else BOT_NAME
        
        # Validate players
        if not is_ai_game:
            if player2.bot:
                await ctx.send(f"❌ You can't play against a bot! Leave player2 empty to play against {BOT_NAME}.")
                return
            
            if player1.id == player2.id:
                await ctx.send("❌ Players can't be the same person!")
                return
        
        # Create new gamez
        board = self.create_board()
        current_time = time.time()
        
        if is_ai_game:
            # Bot Game
            difficulty = difficulty.lower()
            if difficulty not in ["easy", "normal", "hard"]:
                await ctx.send("❌ Invalid difficulty! Choose: easy, normal, or hard")
                return
            
            game_data = {
                "board": board,
                "player1": player1.id,
                "player2": BOT_NAME,  # Bot player
                "current_turn": player1.id,
                "player1_piece": "🔴",
                "player2_piece": "🟡",
                "channel_id": ctx.channel.id,
                "start_time": current_time,
                "last_move": current_time,
                "game_message_id": None,
                "is_ai_game": True,
                "ai_difficulty": difficulty
            }
            
            difficulty_emojis = {"easy": "😊", "normal": "🤔", "hard": "😈"}
            embed = discord.Embed(
                title=f"🔴🤖 Connect 4 Game Started Against {BOT_NAME}! 🤖🟡",
                description=f"**{player1.display_name}** 🔴 vs **{BOT_NAME} ({difficulty.title()})** 🟡 {difficulty_emojis.get(difficulty, '🤖')}\n\n{player1.mention}'s turn!",
                color=discord.Color.blue()
            )
            embed.set_footer(text=f"Connect 4 against {BOT_NAME} ({difficulty.title()}) • First to 4 in a row wins! • 10min timeout")
        else:
            # Player vs Player Game
            game_data = {
                "board": board,
                "player1": player1.id,
                "player2": player2.id,
                "current_turn": player1.id,
                "player1_piece": "🔴",
                "player2_piece": "🟡",
                "channel_id": ctx.channel.id,
                "start_time": current_time,
                "last_move": current_time,
                "game_message_id": None
            }
            
            embed = discord.Embed(
                title="🔴🟡 Connect 4 Game Started! 🟡🔴",
                description=f"**{player1.display_name}** 🔴 vs **{player2.display_name}** 🟡\n\n{player1.mention}'s turn!",
                color=discord.Color.blue()
            )
            embed.set_footer(text="Connect 4 • First to 4 in a row wins! • 10min timeout")
        
        # Common embed fields
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
        
        self.active_games[channel_id] = game_data
        save_data(self.scores, self.active_games)
        
        # Send initial message and store its ID for editing
        if is_ai_game:
            game_message = await ctx.send(embed=embed)
        else:
            game_message = await ctx.send(f"{player1.mention} vs {player2.mention}", embed=embed)
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
        
        # Delete the user's move message to keep chat clean
        try:
            await message.delete()
        except (discord.Forbidden, discord.NotFound):
            pass  # Bot doesn't have permission or message already deleted
        
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
            
            # Edit the original message instead of sending new one
            try:
                if game.get("game_message_id"):
                    game_message = await message.channel.fetch_message(game["game_message_id"])
                    await game_message.edit(embed=embed)
                else:
                    await message.channel.send(embed=embed)
            except discord.NotFound:
                await message.channel.send(embed=embed)
            
            # Clean up game
            del self.active_games[channel_id]
            save_data(self.scores, self.active_games)
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
            
            # Edit the original message instead of sending new one
            try:
                if game.get("game_message_id"):
                    game_message = await message.channel.fetch_message(game["game_message_id"])
                    await game_message.edit(embed=embed)
                else:
                    await message.channel.send(embed=embed)
            except discord.NotFound:
                await message.channel.send(embed=embed)
            
            # Clean up game
            del self.active_games[channel_id]
            save_data(self.scores, self.active_games)
            return
        
        # Handle Bot turn if this is a bot game
        if game.get("is_ai_game") and game["player2"] == BOT_NAME:
            # Switch to Bot turn
            game["current_turn"] = BOT_NAME
            save_data(self.scores, self.active_games)
            
            # Bot makes its move
            await asyncio.sleep(1)  # Brief delay for realism
            ai_move = self.get_ai_move(game["board"], game["ai_difficulty"], game["player2_piece"], game["player1_piece"])
            
            if ai_move is not None:
                # Bot drops piece
                self.drop_piece(game["board"], ai_move, game["player2_piece"])
                game["last_move"] = time.time()
                
                # Check if Bot wins
                if self.check_winner(game["board"], game["player2_piece"]):
                    embed = discord.Embed(
                        title=f"🤖 {BOT_NAME} WINS! 🤖",
                        description=f"**{BOT_NAME} ({game['ai_difficulty'].title()})** wins with {game['player2_piece']}!",
                        color=discord.Color.red()
                    )
                    embed.add_field(
                        name="Final Board",
                        value=self.display_board(game["board"]),
                        inline=False
                    )
                    
                    # Edit the original message instead of sending new one
                    try:
                        if game.get("game_message_id"):
                            game_message = await message.channel.fetch_message(game["game_message_id"])
                            await game_message.edit(embed=embed)
                        else:
                            await message.channel.send(embed=embed)
                    except discord.NotFound:
                        await message.channel.send(embed=embed)
                    
                    # Clean up game
                    del self.active_games[channel_id]
                    save_data(self.scores, self.active_games)
                    return
                
                # Check for tie after Bot move
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
                    
                    # Edit the original message instead of sending new one
                    try:
                        if game.get("game_message_id"):
                            game_message = await message.channel.fetch_message(game["game_message_id"])
                            await game_message.edit(embed=embed)
                        else:
                            await message.channel.send(embed=embed)
                    except discord.NotFound:
                        await message.channel.send(embed=embed)
                    
                    # Clean up game
                    del self.active_games[channel_id]
                    save_data(self.scores, self.active_games)
                    return
                
                # Switch back to player
                game["current_turn"] = game["player1"]
                save_data(self.scores, self.active_games)
                
                # Update embed with Bot move
                embed = discord.Embed(
                    title=f"🔴🤖 Connect 4 Game Started Against {BOT_NAME} 🤖🟡",
                    description=f"**{BOT_NAME} placed in column {ai_move + 1}!**\n\n**{message.author.display_name}'s** turn! 🔴",
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
                embed.set_footer(text=f"Connect 4 against {BOT_NAME} ({game['ai_difficulty'].title()}) • First to 4 in a row wins! • 10min timeout")
                
                # Edit the original message
                try:
                    if game.get("game_message_id"):
                        game_message = await message.channel.fetch_message(game["game_message_id"])
                        await game_message.edit(embed=embed)
                    else:
                        new_message = await message.channel.send(embed=embed)
                        game["game_message_id"] = new_message.id
                        save_data(self.scores, self.active_games)
                except discord.NotFound:
                    new_message = await message.channel.send(embed=embed)
                    game["game_message_id"] = new_message.id
                    save_data(self.scores, self.active_games)
            
            return
        
        # Regular player vs player game continues here
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
    
    @connect_4.command(name="stop", description="Stop the current Connect 4 game")
    async def stop(self, ctx):
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
    
    @connect_4.command(name="scores", description="Show Connect 4 leaderboard")
    async def scores(self, ctx):
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
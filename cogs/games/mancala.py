import discord
from discord.ext import commands, tasks
import json
import os
import time
import asyncio
import random
from config import EMBED_THUMBNAIL, BOT_NAME

GAME_DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "game_files/mancala.json")

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

class Mancala(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.scores, self.active_games = load_scores()
        self.timeout_check.start()
        
    def cog_unload(self):
        self.timeout_check.cancel()
    
    async def update_game_embed(self, channel, game, title="🏺 Mancala Game", description=None, color=discord.Color.purple()):
        """Update the game embed with current state"""
        if description is None:
            if game["current_turn"] == 1:
                description = f"{game['player1_name']}'s turn!"
            else:
                description = f"{game['player2_name']}'s turn!"
        
        embed = discord.Embed(title=title, description=description, color=color)
        embed.add_field(
            name="Game Board",
            value=self.display_board(game["board"], game["player1_store"], game["player2_store"], 
                                   game["player1_name"], game["player2_name"]),
            inline=False
        )
        embed.add_field(
            name="Score",
            value=f"{game['player1_name']}: {game['player1_store']} stones\n{game['player2_name']}: {game['player2_store']} stones",
            inline=False
        )
        
        if not title.startswith("🏆") and not title.startswith("🤝"):  # Not game over
            embed.add_field(name="Next Move", value="Type a number (1-6) to choose your pit!", inline=False)
        
        embed.set_thumbnail(url=EMBED_THUMBNAIL)
        
        footer_text = "Mancala"
        if game.get("is_ai_game"):
            footer_text += f" vs {BOT_NAME}"
            if game.get("ai_difficulty"):
                footer_text += f" ({game['ai_difficulty'].title()})"
        footer_text += " • Collect the most stones! • 10min timeout"
        embed.set_footer(text=footer_text)
        
        try:
            if game.get("game_message_id"):
                game_message = await channel.fetch_message(game["game_message_id"])
                await game_message.edit(embed=embed)
            else:
                new_message = await channel.send(embed=embed)
                game["game_message_id"] = new_message.id
        except discord.NotFound:
            new_message = await channel.send(embed=embed)
            game["game_message_id"] = new_message.id
        
    @tasks.loop(minutes=2)
    async def timeout_check(self):
        """Check for timed out games and clean them up"""
        current_time = time.time()
        expired_games = []
        
        for channel_id, game in self.active_games.items():
            if current_time - game.get("last_move", game.get("start_time", current_time)) > 600:  # 10 minutes
                expired_games.append(channel_id)
        
        for channel_id in expired_games:
            game = self.active_games[channel_id]
            channel = self.bot.get_channel(game["channel_id"])
            
            if channel:
                await self.update_game_embed(
                    channel, game,
                    title="⏰ Mancala Game Timed Out",
                    description="The game has been automatically ended due to inactivity (10 minutes).",
                    color=discord.Color.orange()
                )
            
            del self.active_games[channel_id]
        
        if expired_games:
            save_data(self.scores, self.active_games)
    
    @timeout_check.before_loop
    async def before_timeout_check(self):
        await self.bot.wait_until_ready()
        
    def create_board(self):
        """Create initial Mancala board with 4 stones in each pit"""
        return [4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4]  # 6 pits per player
    
    def display_board(self, board, player1_store, player2_store, player1_name="Player 1", player2_name="Player 2"):
        """Display the Mancala board with the given design and player names."""
        return f"""```
       +---------------------------+
       |       {player2_name} ({player2_store})      |
       +---------------------------+
R1 ->  |     {board[11]}        |     {board[0]}      |  <- R1
R2 ->  |     {board[10]}        |     {board[1]}      |  <- R2
R3 ->  |     {board[9]}        |     {board[2]}      |  <- R3
R4 ->  |     {board[8]}        |     {board[3]}      |  <- R4
R5 ->  |     {board[7]}        |     {board[4]}      |  <- R5
R6 ->  |     {board[6]}        |     {board[5]}      |  <- R6
       +---------------------------+
       |       {player1_name} ({player1_store})      |
       +---------------------------+
       ```"""
    
    def make_move(self, board, player1_store, player2_store, pit_index, current_player):
        """
        Make a move in Mancala. Returns (new_board, new_p1_store, new_p2_store, extra_turn, game_over, winner)
        """
        board = board.copy()
        
        # Validate move
        if current_player == 1:
            if pit_index < 0 or pit_index > 5 or board[pit_index] == 0:
                return None, None, None, False, False, None
        else:  # Player 2
            if pit_index < 6 or pit_index > 11 or board[pit_index] == 0:
                return None, None, None, False, False, None
        
        # Pick up stones from the chosen pit
        stones = board[pit_index]
        board[pit_index] = 0
        current_pos = pit_index
        
        # Distribute stones counter-clockwise
        extra_turn = False
        
        while stones > 0:
            current_pos += 1
            
            # Handle wrapping and stores
            if current_pos == 6:  # Reached Player 1's store position
                if current_player == 1:
                    player1_store += 1
                    stones -= 1
                    if stones == 0:
                        extra_turn = True
                    continue
                else:
                    # Player 2 skips Player 1's store
                    current_pos = 6
            elif current_pos == 12:  # Reached Player 2's store position
                if current_player == 2:
                    player2_store += 1
                    stones -= 1
                    if stones == 0:
                        extra_turn = True
                    current_pos = -1  # Will become 0 next iteration
                    continue
                else:
                    # Player 1 skips Player 2's store, wrap to beginning
                    current_pos = -1  # Will become 0 next iteration
            
            # Ensure we stay within board bounds
            if current_pos >= 12:
                current_pos = 0
            
            # Place stone in pit
            board[current_pos] += 1
            stones -= 1
            
            # Capture rule: last stone in empty pit on your side
            if stones == 0:  # This was the last stone
                if current_player == 1 and 0 <= current_pos <= 5 and board[current_pos] == 1:
                    # Player 1 captures from opposite pit
                    opposite_pit = 11 - current_pos
                    if opposite_pit >= 6 and opposite_pit <= 11 and board[opposite_pit] > 0:
                        captured = board[opposite_pit] + board[current_pos]
                        board[opposite_pit] = 0
                        board[current_pos] = 0
                        player1_store += captured
                elif current_player == 2 and 6 <= current_pos <= 11 and board[current_pos] == 1:
                    # Player 2 captures from opposite pit
                    opposite_pit = 11 - current_pos
                    if opposite_pit >= 0 and opposite_pit <= 5 and board[opposite_pit] > 0:
                        captured = board[opposite_pit] + board[current_pos]
                        board[opposite_pit] = 0
                        board[current_pos] = 0
                        player2_store += captured
        
        # Check for game over
        p1_stones = sum(board[0:6])
        p2_stones = sum(board[6:12])
        
        game_over = False
        winner = None
        
        if p1_stones == 0 or p2_stones == 0:
            # Game over - collect remaining stones
            player1_store += p1_stones
            player2_store += p2_stones
            board = [0] * 12
            game_over = True
            
            if player1_store > player2_store:
                winner = 1
            elif player2_store > player1_store:
                winner = 2
            else:
                winner = 0  # Tie
        
        return board, player1_store, player2_store, extra_turn, game_over, winner
    
    def get_valid_moves(self, board, player):
        """Get list of valid moves for a player"""
        if player == 1:
            return [i for i in range(6) if board[i] > 0]
        else:
            return [i for i in range(6, 12) if board[i] > 0]
    
    def get_ai_move(self, board, player1_store, player2_store, difficulty, ai_player):
        """Get AI move based on difficulty level"""
        if difficulty == "easy":
            return self._easy_ai_move(board, ai_player)
        elif difficulty == "normal":
            return self._normal_ai_move(board, player1_store, player2_store, ai_player)
        elif difficulty == "hard":
            return self._hard_ai_move(board, player1_store, player2_store, ai_player)
        else:
            return self._easy_ai_move(board, ai_player)
    
    def _easy_ai_move(self, board, ai_player):
        """Easy AI - random valid move"""
        valid_moves = self.get_valid_moves(board, ai_player)
        return random.choice(valid_moves) if valid_moves else None
    
    def _normal_ai_move(self, board, player1_store, player2_store, ai_player):
        """Normal AI - prefers moves that give extra turns or capture stones"""
        valid_moves = self.get_valid_moves(board, ai_player)
        if not valid_moves:
            return None
        
        best_moves = []
        best_score = -1
        
        for move in valid_moves:
            score = 0
            temp_board, temp_p1, temp_p2, extra_turn, _, _ = self.make_move(
                board, player1_store, player2_store, move, ai_player
            )
            
            if temp_board is None:
                continue
            
            # Prefer extra turns
            if extra_turn:
                score += 10
            
            # Prefer moves that gain stones
            if ai_player == 1:
                stones_gained = temp_p1 - player1_store
            else:
                stones_gained = temp_p2 - player2_store
            score += stones_gained
            
            if score > best_score:
                best_score = score
                best_moves = [move]
            elif score == best_score:
                best_moves.append(move)
        
        return random.choice(best_moves) if best_moves else random.choice(valid_moves)
    
    def _hard_ai_move(self, board, player1_store, player2_store, ai_player):
        """Hard AI - uses minimax with limited depth"""
        valid_moves = self.get_valid_moves(board, ai_player)
        if not valid_moves:
            return None
        
        best_move = None
        best_score = float('-inf')
        
        for move in valid_moves:
            temp_board, temp_p1, temp_p2, extra_turn, game_over, winner = self.make_move(
                board, player1_store, player2_store, move, ai_player
            )
            
            if temp_board is None:
                continue
            
            if game_over:
                if winner == ai_player:
                    score = 1000
                elif winner == 0:
                    score = 0
                else:
                    score = -1000
            else:
                next_player = ai_player if extra_turn else (3 - ai_player)
                score = self._minimax(temp_board, temp_p1, temp_p2, 3, False if extra_turn else True, ai_player, next_player)
            
            if score > best_score:
                best_score = score
                best_move = move
        
        return best_move if best_move is not None else random.choice(valid_moves)
    
    def _minimax(self, board, p1_store, p2_store, depth, maximizing, ai_player, current_player):
        """Minimax algorithm for hard AI"""
        if depth == 0:
            return self._evaluate_position(board, p1_store, p2_store, ai_player)
        
        valid_moves = self.get_valid_moves(board, current_player)
        if not valid_moves:
            return self._evaluate_position(board, p1_store, p2_store, ai_player)
        
        if maximizing:
            max_eval = float('-inf')
            for move in valid_moves:
                temp_board, temp_p1, temp_p2, extra_turn, game_over, winner = self.make_move(
                    board, p1_store, p2_store, move, current_player
                )
                
                if temp_board is None:
                    continue
                
                if game_over:
                    if winner == ai_player:
                        eval_score = 1000
                    elif winner == 0:
                        eval_score = 0
                    else:
                        eval_score = -1000
                else:
                    next_player = current_player if extra_turn else (3 - current_player)
                    eval_score = self._minimax(temp_board, temp_p1, temp_p2, depth - 1, 
                                             not extra_turn if current_player == ai_player else maximizing, 
                                             ai_player, next_player)
                
                max_eval = max(max_eval, eval_score)
            return max_eval
        else:
            min_eval = float('inf')
            for move in valid_moves:
                temp_board, temp_p1, temp_p2, extra_turn, game_over, winner = self.make_move(
                    board, p1_store, p2_store, move, current_player
                )
                
                if temp_board is None:
                    continue
                
                if game_over:
                    if winner == ai_player:
                        eval_score = 1000
                    elif winner == 0:
                        eval_score = 0
                    else:
                        eval_score = -1000
                else:
                    next_player = current_player if extra_turn else (3 - current_player)
                    eval_score = self._minimax(temp_board, temp_p1, temp_p2, depth - 1, 
                                             extra_turn if current_player == ai_player else maximizing, 
                                             ai_player, next_player)
                
                min_eval = min(min_eval, eval_score)
            return min_eval
    
    def _evaluate_position(self, board, p1_store, p2_store, ai_player):
        """Evaluate current position for AI"""
        if ai_player == 1:
            return p1_store - p2_store
        else:
            return p2_store - p1_store
    
    async def process_ai_turn(self, channel_id):
        """Process AI turn in a separate method"""
        game = self.active_games.get(channel_id)
        if not game or not game.get("is_ai_game"):
            return

        channel = self.bot.get_channel(game["channel_id"])
        if not channel:
            return

        # Show AI thinking
        await self.update_game_embed(channel, game, description=f"🤖 {BOT_NAME} is thinking...", color=discord.Color.blue())

        # Simulate thinking time based on difficulty
        difficulty = game.get("ai_difficulty", "normal")
        think_time = {"easy": (0.5, 1.5), "normal": (1.0, 2.5), "hard": (2.0, 4.0)}
        await asyncio.sleep(random.uniform(*think_time[difficulty]))

        # Get AI move
        ai_move = self.get_ai_move(
            game["board"],
            game["player1_store"],
            game["player2_store"],
            difficulty,
            2  # AI is always Player 2
        )

        if ai_move is None:
            await channel.send("❌ AI has no valid moves available!")
            return

        # Make the AI move
        result = self.make_move(
            game["board"],
            game["player1_store"],
            game["player2_store"],
            ai_move,
            2  # AI is Player 2
        )

        if result[0] is None:
            await channel.send("❌ AI move failed!")
            return

        new_board, new_p1_store, new_p2_store, extra_turn, game_over, winner = result

        # Update game state
        game["board"] = new_board
        game["player1_store"] = new_p1_store
        game["player2_store"] = new_p2_store
        game["last_move"] = time.time()

        # Show AI's move
        ai_pit_display = ai_move - 5  # Convert back to 1-6 display format for Player 2
        await self.update_game_embed(channel, game, description=f"{BOT_NAME} chose pit {ai_pit_display}!", color=discord.Color.green())

        if game_over:
            # Handle game over
            del self.active_games[channel_id]

            # Update scores
            if winner == 1:
                winner_name = self.bot.get_user(game["player1"]).display_name
                self.scores[str(game["player1"])] = self.scores.get(str(game["player1"]), 0) + 1
            elif winner == 2:
                winner_name = BOT_NAME

            title = "🤝 Mancala Tie!" if winner == 0 else "🏆 Mancala Winner!"
            description = "Both players collected the same number of stones!" if winner == 0 else f"**{winner_name}** wins with {new_p1_store if winner == 1 else new_p2_store} stones!"
            color = discord.Color.orange() if winner == 0 else discord.Color.gold()
            
            await self.update_game_embed(channel, game, title=title, description=description, color=color)
            save_data(self.scores, self.active_games)
            return

        # Switch turns if no extra turn
        if not extra_turn:
            game["current_turn"] = 1  # Back to player 1

        save_data(self.scores, self.active_games)

        # If AI gets another turn, schedule it
        if extra_turn:
            await asyncio.sleep(1)  # Brief pause before next AI move
            await self.process_ai_turn(channel_id)
            return

        # Show updated board for player's turn
        await self.update_game_embed(channel, game)
    
    @commands.hybrid_command(name="mancala", with_app_command=True)
    async def start_mancala(self, ctx, player1: discord.Member = None, player2: discord.Member = None, difficulty: str = "normal"):
        """Start a Mancala game against another player or AI
        
        Args:
            player1: First player (defaults to command user)
            player2: Second player (leave empty for AI, or specify a player)
            difficulty: AI difficulty level (easy, normal, hard) - only used when playing against AI
        """
        channel_id = str(ctx.channel.id)
        
        if channel_id in self.active_games:
            await ctx.send("❌ There's already a Mancala game in this channel!")
            return
        
        player1 = player1 or ctx.author
        is_ai_game = player2 is None
        
        player2 = player2 if not is_ai_game else BOT_NAME
        
        if not is_ai_game:
            if player2.bot:
                await ctx.send(f"❌ You can't play against a bot! Leave player2 empty to play against {BOT_NAME}.")
                return
            
            if player1.id == player2.id:
                await ctx.send("❌ Players can't be the same person!")
                return
        
        board = self.create_board()
        current_time = time.time()
        
        player1_name = player1.display_name
        player2_name = player2 if is_ai_game else player2.display_name
        
        game_data = {
            "board": board,
            "player1": player1.id,
            "player2": player2 if is_ai_game else player2.id,
            "player1_store": 0,
            "player2_store": 0,
            "current_turn": 1,  # Player 1 always starts
            "channel_id": ctx.channel.id,
            "start_time": current_time,
            "last_move": current_time,
            "game_message_id": None,
            "is_ai_game": is_ai_game,
            "ai_difficulty": difficulty if is_ai_game else None,
            "player1_name": player1_name,
            "player2_name": player2_name
        }
        
        if is_ai_game:
            difficulty_emojis = {"easy": "😊", "normal": "🤔", "hard": "😈"}
            embed = discord.Embed(
                title=f"🏺 Mancala vs {BOT_NAME}! 🤖",
                description=f"**{player1_name}** vs **{BOT_NAME} ({difficulty.title()})** {difficulty_emojis.get(difficulty, '🤖')}\n\n{player1.mention}'s turn!",
                color=discord.Color.purple()
            )
            embed.set_footer(text=f"Mancala vs {BOT_NAME} ({difficulty.title()}) • Collect the most stones! • 10min timeout")
        else:
            embed = discord.Embed(
                title="🏺 Mancala Game Started! 🏺",
                description=f"**{player1_name}** vs **{player2_name}**\n\n{player1.mention}'s turn!",
                color=discord.Color.purple()
            )
            embed.set_footer(text="Mancala • Collect the most stones! • 10min timeout")
        
        embed.add_field(
            name="Game Board",
            value=self.display_board(board, 0, 0, player1_name, player2_name),
            inline=False
        )
        embed.add_field(
            name="How to Play",
            value="Type a number (1-6) to choose a pit on your side!\nCollect stones by moving them around the board.\nLanding in your store gives an extra turn!",
            inline=False
        )
        embed.set_thumbnail(url=EMBED_THUMBNAIL)
        
        self.active_games[channel_id] = game_data
        save_data(self.scores, self.active_games)
        
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
        
        if channel_id not in self.active_games:
            return
        
        game = self.active_games[channel_id]
        
        # Check if it's the player's turn (and not AI game with AI turn)
        if game.get("is_ai_game") and game["current_turn"] == 2:
            return  # It's AI's turn, ignore human messages
        
        current_player_id = game["player1"] if game["current_turn"] == 1 else game["player2"]
        if message.author.id != current_player_id:
            return
        
        content = message.content.strip()
        if not content.isdigit():
            return
        
        pit_number = int(content)
        
        if pit_number < 1 or pit_number > 6:
            await message.channel.send("❌ Please choose a pit between 1 and 6!")
            return
        
        # Convert to board index
        if game["current_turn"] == 1:
            pit_index = pit_number - 1  # Player 1 uses pits 0-5
            if pit_index < 0 or pit_index > 5:
                await message.channel.send("❌ Please choose a pit between 1 and 6!")
                return
        else:
            pit_index = pit_number + 5   # Player 2 uses pits 6-11
            if pit_index < 6 or pit_index > 11:
                await message.channel.send("❌ Please choose a pit between 1 and 6!")
                return
        
        # Check if pit has stones
        if game["board"][pit_index] == 0:
            await message.channel.send("❌ That pit is empty! Choose a pit with stones.")
            return
        
        # Make the move
        result = self.make_move(
            game["board"], 
            game["player1_store"], 
            game["player2_store"], 
            pit_index, 
            game["current_turn"]
        )
        
        if result[0] is None:
            await message.channel.send("❌ Invalid move! That pit is empty or not on your side.")
            return
        
        new_board, new_p1_store, new_p2_store, extra_turn, game_over, winner = result
        
        # Update game state
        game["board"] = new_board
        game["player1_store"] = new_p1_store
        game["player2_store"] = new_p2_store
        game["last_move"] = time.time()
        
        # Delete the user's move message
        try:
            await message.delete()
        except (discord.Forbidden, discord.NotFound):
            pass
        
        save_data(self.scores, self.active_games)
        
        if game_over:
            # Game ended
            del self.active_games[channel_id]
            
            winner_id = None
            if winner == 1:
                winner_id = str(game["player1"])
                winner_name = game["player1_name"]
                self.scores[winner_id] = self.scores.get(winner_id, 0) + 1
            elif winner == 2:
                if game.get("is_ai_game"):
                    winner_name = BOT_NAME
                else:
                    winner_id = str(game["player2"])
                    winner_name = game["player2_name"]
                    self.scores[winner_id] = self.scores.get(winner_id, 0) + 1
            
            title = "🤝 Mancala Tie!" if winner == 0 else "🏆 Mancala Winner!"
            description = "Both players collected the same number of stones!" if winner == 0 else f"**{winner_name}** wins with {new_p1_store if winner == 1 else new_p2_store} stones!"
            color = discord.Color.orange() if winner == 0 else discord.Color.gold()
            
            await self.update_game_embed(message.channel, game, title=title, description=description, color=color)
            save_data(self.scores, self.active_games)
            return
        
        # Switch turns (unless extra turn)
        if not extra_turn:
            game["current_turn"] = 3 - game["current_turn"]  # Switch between 1 and 2
        
        save_data(self.scores, self.active_games)
        
        # Handle AI turn
        if game.get("is_ai_game") and game["current_turn"] == 2:
            # Schedule AI turn
            asyncio.create_task(self.process_ai_turn(channel_id))
            return
        
        # Show turn message with extra turn indicator if applicable
        turn_text = f"{game['player1_name']}'s turn!" if game["current_turn"] == 1 else f"{game['player2_name']}'s turn!"
        if extra_turn:
            turn_text = f"Extra turn! {turn_text}"
        
        await self.update_game_embed(message.channel, game, description=turn_text)
        save_data(self.scores, self.active_games)
    
    @commands.hybrid_command(name="stop_mancala", with_app_command=True)
    async def stop_mancala(self, ctx):
        """Stop the current Mancala game"""
        channel_id = str(ctx.channel.id)
        
        if channel_id not in self.active_games:
            await ctx.send("❌ No active Mancala game in this channel!")
            return
        
        game = self.active_games[channel_id]
        
        if (ctx.author.id not in [game["player1"], game["player2"]] and 
            not ctx.author.guild_permissions.manage_messages):
            await ctx.send("❌ Only the players or moderators can stop the game!")
            return
        
        await self.update_game_embed(
            ctx.channel, game,
            title="🛑 Mancala Game Stopped",
            description="The game has been stopped.",
            color=discord.Color.red()
        )
        
        del self.active_games[channel_id]
        save_data(self.scores, self.active_games)
    
    @commands.hybrid_command(name="mancala_scores", with_app_command=True)
    async def show_mancala_scores(self, ctx):
        """Show Mancala leaderboard"""
        if not self.scores:
            await ctx.send("No Mancala scores yet!")
            return
        
        sorted_scores = sorted(self.scores.items(), key=lambda x: -x[1])[:10]
        desc = "\n".join([f"<@{uid}>: {score} wins" for uid, score in sorted_scores])
        
        embed = discord.Embed(
            title="🏆 Mancala Leaderboard",
            description=desc,
            color=discord.Color.gold()
        )
        embed.set_thumbnail(url=EMBED_THUMBNAIL)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Mancala(bot))
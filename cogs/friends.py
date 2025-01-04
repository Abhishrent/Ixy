import random
import asyncio
from discord.ext import commands
import discord
from friends_trivia_questions import questions

class PlayerSession:
    def __init__(self, initiator_id):
        self.players = {initiator_id}  # Set of player IDs who have joined the game
        self.player_scores = {}  # Scores for each player
        self.answered_questions = {}  # Track which questions each player has answered
        self.total_questions = 0
        self.completed_players = 0
        self.selected_questions = []  # Store selected questions for correct answer reference

class FriendsTrivia(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.questions = questions
        self.active_sessions = {}  # Tracks active game sessions per channel

    @commands.command('friends')
    async def friends_quiz(self, ctx, num_questions: int = 1):
        """FRIENDS Trivia game with dynamic multiplayer support."""
        # Validate number of questions
        if num_questions < 1 or num_questions > len(self.questions) or num_questions > 10:
            await ctx.send(f"⚠️ Please specify a number between 1 and min({len(self.questions)}, 10).")
            return

        # Create a new session for this channel
        session = PlayerSession(ctx.author.id)
        session.total_questions = num_questions
        session.player_scores[ctx.author.id] = 0
        self.active_sessions[ctx.channel.id] = session

        # Shuffle the questions
        selected_questions = random.sample(self.questions, num_questions)
        session.selected_questions = selected_questions

        # Ask the specified number of questions
        for question_index, question_data in enumerate(selected_questions):
            question = question_data["question"]
            correct_answer = question_data["correct_answer"]
            incorrect_answers = question_data["incorrect_answers"]

            # Shuffle options
            options = incorrect_answers + [correct_answer]
            random.shuffle(options)

            # Prepare buttons for the options
            buttons = [
                discord.ui.Button(
                    label=options[0], 
                    custom_id=f"q{question_index}_answer_{options[0]}",
                    style=discord.ButtonStyle.primary
                ),
                discord.ui.Button(
                    label=options[1], 
                    custom_id=f"q{question_index}_answer_{options[1]}",
                    style=discord.ButtonStyle.primary
                ),
                discord.ui.Button(
                    label=options[2], 
                    custom_id=f"q{question_index}_answer_{options[2]}",
                    style=discord.ButtonStyle.primary
                ),
                discord.ui.Button(
                    label=options[3], 
                    custom_id=f"q{question_index}_answer_{options[3]}",
                    style=discord.ButtonStyle.primary
                )
            ]

            # Create a view to hold the buttons
            view = discord.ui.View()
            for button in buttons:
                button.callback = self.button_callback
                view.add_item(button)

            # Create an embed for the trivia question
            embed = discord.Embed(
                title=f"📺 **FRIENDS Trivia Question {question_index + 1}/{num_questions}**",
                description=question,
                color=discord.Color.purple()
            )
            #embed.add_field(name="Answer Options", value="🔓 Click a button to answer!", inline=False)

            # Send the trivia question with the embed and buttons
            await ctx.send(embed=embed, view=view)

            # Wait a moment between questions
            await asyncio.sleep(1)

        # Wait for all players to finish
        await self.wait_for_players_to_finish(ctx)

    async def button_callback(self, interaction: discord.Interaction):
        """Handle button interactions for all questions"""
        channel_id = interaction.channel_id
        user_id = interaction.user.id

        # Ensure a session exists for this channel
        if channel_id not in self.active_sessions:
            await interaction.response.send_message("❌ No active trivia game in this channel.", ephemeral=True)
            return

        session = self.active_sessions[channel_id]

        # Add new player if not already in the game
        if user_id not in session.players:
            session.players.add(user_id)
            session.player_scores[user_id] = 0

        # Parse question index and answer from custom_id
        custom_id = interaction.data['custom_id']
        question_index = int(custom_id.split('_')[0][1:])
        user_answer = custom_id.split('_', 2)[2]

        # Check if this player has already answered this question
        if (question_index in session.answered_questions.get(user_id, set())):
            await interaction.response.send_message("❌ You've already answered this question!", ephemeral=True)
            return

        # Track answered questions for this player
        if user_id not in session.answered_questions:
            session.answered_questions[user_id] = set()
        session.answered_questions[user_id].add(question_index)

        # Get the correct answer from the selected questions
        correct_answer = session.selected_questions[question_index]["correct_answer"]

        # Check if the answer is correct
        if user_answer == correct_answer:
            session.player_scores[user_id] += 1
            response_text = f"✅ **Correct Answer, {interaction.user.display_name}!** `{correct_answer}`"
        else:
            response_text = f"❌ **Incorrect Answer, {interaction.user.display_name}!** The correct answer was: `{correct_answer}`"

        # Mark player's questions as complete if they've answered all questions
        if len(session.answered_questions.get(user_id, [])) == session.total_questions:
            session.completed_players += 1

        await interaction.response.send_message(response_text, ephemeral=True)

    async def wait_for_players_to_finish(self, ctx):
        """Wait for all players to complete their questions"""
        session = self.active_sessions[ctx.channel.id]
        
        # Wait until all players have completed their questions
        while session.completed_players < len(session.players):
            await asyncio.sleep(2)

        # Show leaderboard
        leaderboard = sorted(session.player_scores.items(), key=lambda x: x[1], reverse=True)
        leaderboard_text = ""
        rank = 1
        for user_id, score in leaderboard:
            user = self.bot.get_user(user_id)
            if user:  # Ensure the user still exists in the bot's cache
                rank_emoji = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"#{rank}"
                leaderboard_text += f"{rank_emoji} {user.display_name}: {score}\n"
                rank += 1

        # Create and send leaderboard embed
        embed = discord.Embed(
            title="🏆 **FRIENDS Trivia Scoreboard**",
            description="Here are the final scores and rankings for all players:",
            color=discord.Color.green()
        )
        embed.add_field(name="Scores", value=leaderboard_text or "No scores yet!", inline=False)
        await ctx.send(embed=embed)

        # Clean up the session
        del self.active_sessions[ctx.channel.id]

# Add the cog to the bot
async def setup(bot):
    await bot.add_cog(FriendsTrivia(bot))
import discord
from discord.ext import commands
import requests
import random
import asyncio
import html  # Import the html module to decode HTML entities
from config import EMBED_THUMBNAIL  # Import the thumbnail URL

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.scores = {}  # Dictionary to store user scores

    @commands.hybrid_command('toss')
    async def make_choice(self, ctx):
        """Simulates a coin toss."""
        choices = ['HEADS', 'TAILS']
        choice = random.choice(choices)
        await ctx.send(f'{choice}')

    @commands.hybrid_command('meme')
    async def meme(self, ctx):
        """Fetches a random meme from Reddit."""
        url = 'https://www.reddit.com/r/memes/hot.json?limit=100'
        headers = {'User-Agent': 'DiscordBot'}
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            posts = data['data']['children']
            # Filter to only include posts with images
            image_posts = [post for post in posts if post['data']['post_hint'] == 'image']

            if image_posts:
                random_post = random.choice(image_posts)
                title = random_post['data']['title']
                image_url = random_post['data']['url']
                post_link = f"https://reddit.com{random_post['data']['permalink']}"

                # Create an embed for the meme
                embed = discord.Embed(title=title, url=post_link, color=discord.Color.blue())
                embed.set_image(url=image_url)
                embed.set_footer(text="Source: r/memes")
                embed.set_thumbnail(url=EMBED_THUMBNAIL)  # Use config thumbnail

                await ctx.send(embed=embed)
            else:
                await ctx.send("Couldn't find any memes at the moment. Try again later.")
        else:
            await ctx.send("Failed to retrieve memes. Please try again later.")

    @commands.hybrid_command('quiz')
    async def quiz(self, ctx, num_questions: int = 1, difficulty: str = "easy"):
        """Trivia game with difficulty selection and scores displayed in an embed."""
        # Validate the difficulty argument
        valid_difficulties = ["easy", "medium", "hard"]
        if difficulty not in valid_difficulties:
            await ctx.send("⚠️ Invalid difficulty. Please choose from 'easy', 'medium', or 'hard'.")
            return

        # Ensure num_questions is within a reasonable range
        if num_questions < 1 or num_questions > 10:
            await ctx.send("⚠️ Please specify a number between 1 and 10.")
            return

        # Initialize score for the user if they haven't played before
        if ctx.author.id not in self.scores:
            self.scores[ctx.author.id] = 0

        # Ask the specified number of questions
        for _ in range(num_questions):
            url = f"https://opentdb.com/api.php?amount=1&category=18&difficulty={difficulty}&type=multiple"

            try:
                # Fetch trivia data
                response = requests.get(url)
                if response.status_code == 200:
                    data = response.json()

                    # Check if trivia data is available
                    if data["response_code"] == 0:
                        trivia = data["results"][0]
                        question = trivia["question"]
                        correct_answer = trivia["correct_answer"]
                        incorrect_answers = trivia["incorrect_answers"]

                        # Decode the HTML entities in the question and answers
                        question = html.unescape(question)  # Decode question
                        correct_answer = html.unescape(correct_answer)  # Decode correct answer
                        incorrect_answers = [html.unescape(answer) for answer in incorrect_answers]  # Decode all incorrect answers

                        # Shuffle options
                        options = incorrect_answers + [correct_answer]
                        random.shuffle(options)

                        # Prepare buttons for the options
                        buttons = [
                            discord.ui.Button(label=options[0], custom_id=options[0]),
                            discord.ui.Button(label=options[1], custom_id=options[1]),
                            discord.ui.Button(label=options[2], custom_id=options[2]),
                            discord.ui.Button(label=options[3], custom_id=options[3])
                        ]

                        # Create a view to hold the buttons
                        view = discord.ui.View()
                        for button in buttons:
                            view.add_item(button)

                        # Create an embed for the trivia question with locked emoji
                        embed = discord.Embed(
                            title="💡 **Tech Trivia Question**",
                            description=question,
                            color=discord.Color.blue()
                        )
                        embed.add_field(name="Answer Options", value="🔒 Answering is locked. You will be able to answer in a few seconds...", inline=False)
                        embed.set_thumbnail(url=EMBED_THUMBNAIL)  # Use config thumbnail

                        # Send the trivia question with the embed and buttons (locked)
                        message = await ctx.send(embed=embed, view=view)

                        # Wait for 5 seconds before unlocking answers
                        await asyncio.sleep(5)

                        # Change the embed field to indicate answering is now unlocked
                        embed.set_field_at(0, name="Answer Options", value="🔓 Answering is now open! Click a button to answer.", inline=False)
                        await message.edit(embed=embed)

                        # Wait for the user to click a button
                        def check(interaction):
                            return interaction.user == ctx.author and interaction.message.id == message.id

                        try:
                            # Check for the interaction (button press)
                            interaction = await self.bot.wait_for('interaction', check=check, timeout=30.0)

                            # Check if the user pressed the correct answer
                            if interaction.data['custom_id'] == correct_answer:
                                self.scores[ctx.author.id] += 1  # Increment score for correct answer
                                await interaction.response.send_message(f"✅ **Correct Answer!** `{correct_answer}`", ephemeral=True)
                            else:
                                await interaction.response.send_message(f"❌ **Incorrect Answer!** The correct answer was: `{correct_answer}`", ephemeral=True)

                        except asyncio.TimeoutError:
                            # If the user doesn't answer in time
                            await ctx.send("⏳ **Time's up!** Moving on to the next question.")

                        await asyncio.sleep(1)  # Pause before the next question to avoid spamming API

                    else:
                        await ctx.send("⚠️ Couldn't find any trivia facts right now. Try again later!")
                else:
                    await ctx.send("⚠️ Could not fetch trivia at the moment. Please try again later.")
            except Exception as e:
                await ctx.send(f"⚠️ An error occurred: {e}")

        # Send the individual score immediately after the last question
        individual_score = self.scores[ctx.author.id]
        embed = discord.Embed(
            title="🎯 **Your Score**",
            description=f"{ctx.author.display_name}, you answered {individual_score}/{num_questions} questions correctly.",  # Using display_name instead of name
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=EMBED_THUMBNAIL)  # Use config thumbnail
        await ctx.send(embed=embed)

        # After all questions are asked, prepare and send the final leaderboard
        await asyncio.sleep(10)  # Wait a moment before displaying the final leaderboard

        # Prepare the final leaderboard
        leaderboard = sorted(self.scores.items(), key=lambda x: x[1], reverse=True)
        leaderboard_text = ""
        rank = 1
        for user_id, score in leaderboard:
            user = self.bot.get_user(user_id)
            rank_emoji = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"#{rank}"
            leaderboard_text += f"{rank_emoji} {user.display_name}: {score}\n"  # Using display_name instead of name
            rank += 1

        embed = discord.Embed(
            title="🏆 **Final Trivia Scoreboard**",
            description="Here are the final scores and rankings for all players:",
            color=discord.Color.green()
        )
        embed.add_field(name="Scores", value=leaderboard_text, inline=False)
        embed.set_thumbnail(url=EMBED_THUMBNAIL)  # Use config thumbnail
        await ctx.send(embed=embed)

        # Reset scores after the trivia session (optional)
        self.scores.clear()

# Setup function to add the cog
async def setup(bot):
    await bot.add_cog(Fun(bot))

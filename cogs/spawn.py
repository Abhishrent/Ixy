import discord
from discord.ext import commands
from discord import app_commands
import praw
import random

class RedditImage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.reddit = praw.Reddit(
            client_id="***REMOVED***",
            client_secret="***REMOVED***",
            user_agent="Phul Baby"
        )
        # Predefined list of subreddits
        self.subreddits = {
            "beautiful_asians": "BeautifulAsianss", #key:value => unique_vale:actual subreddit name
            "nature_pics": "EarthPorn",
            "cat": "cat",
        }

    @commands.hybrid_command(name="spawn", description="Fetch a random image from a subreddit.")
    @app_commands.choices(
        choice=[
            app_commands.Choice(name="abg", value="beautiful_asians"),
            app_commands.Choice(name="nature", value="nature_pics"),
            app_commands.Choice(name="cat", value="cat"),
        ]
    )
    async def spawn(self, ctx: commands.Context, choice: app_commands.Choice[str]):
        """Fetches a random image from the selected subreddit and sends it in an embed."""
        subreddit_key = choice.value
        subreddit_name = self.subreddits[subreddit_key]

        try:
            reddit_subreddit = self.reddit.subreddit(subreddit_name)
            # Fetch posts with image URLs only
            posts = [
                post for post in reddit_subreddit.hot(limit=50)
                if post.url.endswith(("jpg", "jpeg", "png", "gif"))
            ]

            if not posts:
                await ctx.send(f"No image posts found in r/{subreddit_name}.")
                return

            # Pick a random post
            random_post = random.choice(posts)

            # Create embed with the content and extra info
            embed = discord.Embed(
                title=random_post.title,
                url=random_post.url,
                description=f"Posted by **{random_post.author.name}** in **r/{subreddit_name}**",
                color=discord.Color.blue()
            )

            # Set the image for the embed
            embed.set_image(url=random_post.url)

            embed.set_footer(text=f"Upvotes: {random_post.score} | Comments: {random_post.num_comments}")

            # Respond appropriately based on context (interaction or message)
            if isinstance(ctx, commands.Context):  # Prefix command
                await ctx.send(embed=embed)
            else:  # Slash command interaction
                await ctx.interaction.response.send_message(embed=embed)

        except Exception as e:
            if isinstance(ctx, commands.Context):
                await ctx.send(f"An error occurred: {str(e)}")
            else:
                await ctx.interaction.response.send_message(f"An error occurred: {str(e)}", ephemeral=True)

# Setup function to add the Cog to the bot
async def setup(bot):
    await bot.add_cog(RedditImage(bot))

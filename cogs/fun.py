import discord
from discord.ext import commands
import praw
import random
import os
from dotenv import load_dotenv
from config import EMBED_THUMBNAIL

load_dotenv()

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.reddit = praw.Reddit(
            client_id=os.environ.get("REDDIT_CLIENT_ID"),
            client_secret=os.environ.get("REDDIT_CLIENT_SECRET"),
            user_agent="Phul Baby"
        )
    
    @commands.hybrid_command(name="meme", description="Fetch a random meme from r/memes")
    async def meme(self, ctx: commands.Context):
        """Fetches a random meme from r/memes and sends it in an embed."""
        try:
            await ctx.defer()
            
            reddit_subreddit = self.reddit.subreddit("memes")
            
            # Fetch posts with image URLs only
            posts = [
                post for post in reddit_subreddit.hot(limit=100)
                if post.url.endswith(("jpg", "jpeg", "png", "gif")) and not post.over_18
            ]
            
            if not posts:
                await ctx.send("No memes found at the moment. Try again later!")
                return
            
            # Pick a random post
            random_post = random.choice(posts)
            
            # Create embed with the meme
            embed = discord.Embed(
                title=random_post.title[:256],
                url=f"https://reddit.com{random_post.permalink}",
                color=discord.Color.blue()
            )
            embed.set_thumbnail(url=EMBED_THUMBNAIL)
            embed.set_image(url=random_post.url)
            embed.set_footer(text=f"👍 {random_post.score} | 💬 {random_post.num_comments} | r/memes")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"An error occurred while fetching memes: {str(e)}")

async def setup(bot):
    await bot.add_cog(Fun(bot))
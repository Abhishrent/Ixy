# cogs/insta_watcher.py

import discord
from discord.ext import commands, tasks
import instaloader
from config import INSTA_CHANNEL_ID

class InstaWatcher(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.loader = instaloader.Instaloader()
        self.username = "mbmc_ideax"  # <-- Replace with desired username
        self.channel_id = INSTA_CHANNEL_ID # <-- Replace with your Discord channel ID
        self.last_shortcode = None
        self.check_instagram.start()

    @tasks.loop(minutes=1.0)
    async def check_instagram(self):
        try:
            profile = instaloader.Profile.from_username(self.loader.context, self.username)
            posts = profile.get_posts()
            latest_post = next(posts)

            if self.last_shortcode != latest_post.shortcode:
                self.last_shortcode = latest_post.shortcode
                post_url = f"https://www.instagram.com/p/{latest_post.shortcode}/"

                embed = discord.Embed(
                    title=f"New post from @{self.username}",
                    url=post_url,
                    description=latest_post.caption[:200] + "..." if latest_post.caption else "",
                    color=discord.Color.purple()
                )
                embed.set_image(url=latest_post.url)

                channel = self.bot.get_channel(self.channel_id)
                if channel:
                    await channel.send(embed=embed)

        except Exception as e:
            print(f"[InstaWatcher] Error: {e}")

    @check_instagram.before_loop
    async def before_check(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(InstaWatcher(bot))

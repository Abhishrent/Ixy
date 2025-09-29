import discord
from discord.ext import commands, tasks
import os
import json
from datetime import datetime, timedelta
import pytz
from config import BOT_NAME
from config import GENERAL_CHANNEL_ID

BIRTHDAYS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../bot_memory/birthdays.json")
GIF_URL = "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExYjEwaXMzcWd1YTR0eGY2NHdpMXpsdTUwZ2htbGk5dXR1eHc4aHR5OCZlcD12MV9naWZzX3NlYXJjaCZjdD1n/IQF90tVlBIByw/giphy.gif"

# Helper to load and save birthdays

def load_birthdays():
    if os.path.exists(BIRTHDAYS_FILE):
        try:
            with open(BIRTHDAYS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_birthdays(birthdays):
    os.makedirs(os.path.dirname(BIRTHDAYS_FILE), exist_ok=True)
    with open(BIRTHDAYS_FILE, "w") as f:
        json.dump(birthdays, f, indent=2)

class BirthdaysCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.birthdays = load_birthdays()  # {user_id: "YYYY-MM-DD"}
        self.birthday_wisher.start()
        self._wished_today = set()  # Track user_ids already wished today
        self._last_wish_date = None

    @commands.hybrid_command(name="register_birthday", description="Register your or another user's birthday (format: YYYY-MM-DD)")
    async def register_birthday(self, ctx, date: str, user: discord.Member = None):
        """Register your or another user's birthday (format: YYYY-MM-DD)"""
        try:
            # Validate date
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            await ctx.reply("Please use the format YYYY-MM-DD (e.g., 2000-01-31)", ephemeral=True)
            return
        target_user = user or ctx.author
        user_id = str(target_user.id)
        self.birthdays[user_id] = date
        save_birthdays(self.birthdays)
        if user and user != ctx.author:
            await ctx.reply(f"Birthday for {target_user.mention} has been registered as {date}! 🎂", ephemeral=True)
        else:
            await ctx.reply(f"Your birthday has been registered as {date}! 🎂", ephemeral=True)

    @commands.hybrid_command(name="remove_birthday", description="Remove your or another user's registered birthday.")
    async def remove_birthday(self, ctx, user: discord.Member = None):
        """Remove your or another user's registered birthday."""
        target_user = user or ctx.author
        user_id = str(target_user.id)
        # Only allow removing another user's birthday if the invoker is an admin
        if user and user != ctx.author and not ctx.author.guild_permissions.administrator:
            await ctx.reply("You need to be an administrator to remove another user's birthday.", ephemeral=True)
            return
        if user_id in self.birthdays:
            del self.birthdays[user_id]
            save_birthdays(self.birthdays)
            if user and user != ctx.author:
                await ctx.reply(f"Birthday for {target_user.mention} has been removed.", ephemeral=True)
            else:
                await ctx.reply("Your birthday has been removed.", ephemeral=True)
        else:
            await ctx.reply("No birthday found to remove.", ephemeral=True)

    @tasks.loop(minutes=1)
    async def birthday_wisher(self):
        await self.bot.wait_until_ready()
        now = datetime.now(pytz.timezone("Asia/Kathmandu"))
        today_str = now.strftime("%m-%d")
        # Reset wished list at midnight
        if self._last_wish_date != today_str:
            self._wished_today = set()
            self._last_wish_date = today_str
        channel = self.bot.get_channel(GENERAL_CHANNEL_ID)
        for user_id, date_str in self.birthdays.items():
            try:
                # Check if today is the user's birthday and not already wished
                if date_str[5:] == today_str and user_id not in self._wished_today:
                    user = self.bot.get_user(int(user_id))
                    # DM the user with an embed
                    if user:
                        try:
                            dm_embed = discord.Embed(
                                title=f"🎉 Happy Birthday, {user.display_name}! 🎂",
                                description=f"Wishing you a fantastic year ahead from everyone at MBM IdeaX!",
                                color=discord.Color.gold()
                            )
                            dm_embed.set_footer(text=f"-{BOT_NAME}")
                            dm_embed.set_thumbnail(url=user.display_avatar.url)
                            dm_embed.set_image(url=GIF_URL)
                            await user.send(embed=dm_embed)
                        except Exception:
                            pass
                    # Wish in general channel with an embed and mention in content
                    if channel:
                        public_embed = discord.Embed(
                            title="🎉 Today is a special day!",
                            description=f"Everyone, please wish {user.mention if user else f'<@{user_id}>'} a very happy birthday! 🥳🎂",
                            color=discord.Color.gold()
                        )
                        public_embed.set_footer(text=f"-{BOT_NAME}")
                        public_embed.set_thumbnail(url=user.display_avatar.url if user else discord.Embed.Empty)
                        public_embed.set_image(url=GIF_URL)
                        await channel.send(content=f"{user.mention if user else f'<@{user_id}>'}", embed=public_embed)
                    self._wished_today.add(user_id)
            except Exception:
                continue

    @birthday_wisher.before_loop
    async def before_birthday_wisher(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(BirthdaysCog(bot))
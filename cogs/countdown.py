import discord
from discord.ext import commands
from discord.ext.commands import hybrid_command
import asyncio
from datetime import timedelta

class CountdownCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @hybrid_command(name="countdown")
    @commands.has_permissions(manage_messages=True)  # Optional permission check
    async def countdown(self, ctx, time: str, mentions: str = ""):
        """
        Starts a countdown and sends an embed message.
        Optionally mentions members or roles when the countdown ends.
        time: A string representing the countdown time (e.g., "10s", "2m", "1h").
        mentions: A comma-separated list of members or roles to mention after countdown (optional).
        """
        # Parse time input (e.g., "10s", "2m", "1h")
        time_left = self.parse_time(time)
        if time_left is None:
            await ctx.send("Invalid time format. Please use format like '10s', '2m', '1h'.")
            return
        
        # Emojis for the animation cycle
        emojis = ["🕛", "🕐", "🕑","🕒"]
        
        # Send an initial embed with the countdown
        embed = discord.Embed(title="Countdown", description=f"{emojis[0]} **Time left:** {self.format_time(time_left)}", color=discord.Color.green())
        countdown_message = await ctx.send(embed=embed)

        # Countdown loop with emoji animation
        index = 1
        while time_left > timedelta(seconds=0):
            await asyncio.sleep(1)
            time_left -= timedelta(seconds=1)
            embed.description = f"{emojis[index]} **Time left:** {self.format_time(time_left)} "
            await countdown_message.edit(embed=embed)
            
            # Cycle through the emojis
            index = (index + 1) % len(emojis)

        # When time's up, update the embed
        embed.description = "⏰ **Time's up!**"
        await countdown_message.edit(embed=embed)

        # Process mentions if provided
        mentions_text = self.process_mentions(mentions)
        if mentions_text:
            await ctx.send(content=mentions_text)

    def parse_time(self, time_str):
        """Parse the time string (e.g., '10s', '2m', '1h') into a timedelta object."""
        time_units = {'s': 'seconds', 'm': 'minutes', 'h': 'hours'}
        unit = time_str[-1]
        if unit not in time_units:
            return None
        
        try:
            value = int(time_str[:-1])
            return timedelta(**{time_units[unit]: value})
        except ValueError:
            return None

    def format_time(self, time_left):
        """Format the timedelta object into a human-readable string."""
        seconds = time_left.total_seconds()
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        return f"{hours}h {minutes}m {seconds}s" if hours > 0 else f"{minutes}m {seconds}s"

    def process_mentions(self, mentions):
        """Format the mentions string (supports roles and users) from a comma-separated list."""
        mentions_text = ""
        if mentions:
            mentions_list = mentions.split(",")
            mentions_text = " ".join([mention.strip() for mention in mentions_list])
        return mentions_text


# Setup function to add the cog to the bot
async def setup(bot):
    await bot.add_cog(CountdownCog(bot))

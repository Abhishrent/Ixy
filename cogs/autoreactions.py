import discord
from discord.ext import commands

# Define a dictionary mapping trigger words to specific reactions (emojis)
TRIGGER_REACTIONS = {
    'hello': '👋', 
    'bye': '👋',
    'thanks': '🙏', 
    'goodnight': '😴',
    'good morning': '🌄',
    'firoj': '💣',
    'sachi': '🎀'
}

class AutoReactionCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        # Avoid the bot reacting to its own messages
        if message.author == self.bot.user:
            return

        # Check if any trigger word is in the message (case-insensitive)
        for word, emoji in TRIGGER_REACTIONS.items():
            if word.lower() in message.content.lower():
                # React to the message with the specific emoji
                await message.add_reaction(emoji)

# Setup the cog
async def setup(bot):
    await bot.add_cog(AutoReactionCog(bot))

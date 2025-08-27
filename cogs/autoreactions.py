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
    'sachi': '🎀',
    'miraj': '🏳‍🌈',
    'famous': '🥚',
    'nili': '💃',
    'mainali': '🧨',
    'queen':'💅',
    'loozah':'🤕',
    'reeju':'💸',
    'jeeban':'💰',
    'aashika':'☕',
    'banshaj':'🧯',
    'sudikshya':'💉',
    'bardan': '🛕',
    'swastik':'🏙',
    'krijal':'📷',
    'vishal':'📹',
    'roshan':'🖨',
    'bibek':'🛏'
}

REPLY_TRIGGERS = {
    'good morning': 'Good morning! 🌄',
    'goodnight': 'Good night! 😴',
    'good night': 'Good night! 😴',
    'hello': 'Hello there! 👋',
    'bye': 'Goodbye! 👋',
    'thanks': 'You\'re welcome! 🙏',
    'xaks': "that's Banshaj",
    'bungo':"that's Firoj"
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

        # Check for reply triggers (case-insensitive, only reply to first match)
        for word, reply in REPLY_TRIGGERS.items():
            if word.lower() in message.content.lower():
                await message.reply(reply, mention_author=False)
                break

    @commands.hybrid_command(name="bhana")
    async def bhana(self, ctx, *, message: str):
        """Repeats whatever you say."""
        # Check if money emoji is in the message (payment received)
        if "💰" in message or "💵" in message:
            # Remove the money emojis from the message
            filtered_message = message.replace("💰", "").replace("💵", "")
            await ctx.send(filtered_message)
        elif ctx.author.id == 542227412671397899:
            await ctx.reply("bhandina ja mya", mention_author=False)
            return
        else:
            await ctx.send(message)

# Setup the cog
async def setup(bot):
    await bot.add_cog(AutoReactionCog(bot))

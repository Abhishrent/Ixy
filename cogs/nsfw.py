import discord
import random
from discord.ext import commands

class AutoResponseCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.trigger_words = ['muji', 'machikney', 'machikne', 'randi', 'rando', 'khatey', 'jatho', 'jathi', 'mya']  # List of words to trigger responses
        self.responses = [
            "Chup muji",
            "Mukh nachhad hai randi",
            "Ban khalas hai machikne",
            "Hero banchhas randi ko ban",
            "Barta naho hai muji"
        ]  # List of possible responses to send

    @commands.Cog.listener()
    async def on_message(self, message):
        # Prevent the bot from responding to its own messages
        if message.author == self.bot.user:
            return
        
        # Check if any of the trigger words are in the message as whole words (case insensitive)
        # Split the message into words and check for exact matches
        msg_words = message.content.lower().split()
        if any(word.lower() in msg_words for word in self.trigger_words):
            # Pick a random response from the list
            response = random.choice(self.responses)
            # Send the response in the same channel where the message was sent
            await message.channel.send(response)

    @commands.command()
    async def add_trigger(self, ctx, *, word: str):
        """Add a new trigger word."""
        if word not in self.trigger_words:
            self.trigger_words.append(word)
            await ctx.send(f"'{word}' has been added to the trigger list.")
        else:
            await ctx.send(f"'{word}' is already a trigger word.")

    @commands.command()
    async def remove_trigger(self, ctx, *, word: str):
        """Remove a trigger word."""
        if word in self.trigger_words:
            self.trigger_words.remove(word)
            await ctx.send(f"'{word}' has been removed from the trigger list.")
        else:
            await ctx.send(f"'{word}' is not a trigger word.")

    @commands.command()
    async def list_triggers(self, ctx):
        """List all current trigger words."""
        trigger_list = ", ".join(self.trigger_words)
        await ctx.send(f"Current trigger words: {trigger_list}")

    @commands.command()
    async def add_response(self, ctx, *, response: str):
        """Add a new response to the list."""
        self.responses.append(response)
        await ctx.send(f"New response added: {response}")

    @commands.command()
    async def remove_response(self, ctx, *, response: str):
        """Remove a response from the list."""
        if response in self.responses:
            self.responses.remove(response)
            await ctx.send(f"Response removed: {response}")
        else:
            await ctx.send(f"Response not found in the list.")

    @commands.command()
    async def list_responses(self, ctx):
        """List all current responses."""
        response_list = "\n".join(f"{i+1}. {resp}" for i, resp in enumerate(self.responses))
        await ctx.send(f"Current responses:\n{response_list}")

async def setup(bot):
    await bot.add_cog(AutoResponseCog(bot))
import discord
from discord.ext import commands
import random
import os 

class GuessTheFlag(commands.Cog):
    def __init__(self,bot): 
        self.bot = bot
        flags_dir = os.path.join(os.path.dirname(__file__), "..", "flags")
        self.flag_images = os.listdir(flags_dir)

    @commands.command(name="flagguesser")
    async def flag_guesser(self, ctx):
        await ctx.send("Guess the flag!")


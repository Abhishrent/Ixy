import discord
from discord.ext import commands
import os
import json

BOT_MEMORY_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../bot_memory")
USER_ID_FILE = os.path.join(BOT_MEMORY_DIR, "server_user_id.json")

class FetchID(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="fetchids")
    @commands.has_permissions(administrator=True)
    async def fetch_ids(self, ctx):
        """Fetch all user IDs and display names in the server and store them in server_user_id.json."""
        guild = ctx.guild
        if not guild:
            await ctx.send("This command can only be used in a server.")
            return

        user_data = []
        for member in guild.members:
            user_data.append({
                "user_id": member.id,
                "display_name": member.display_name
            })

        os.makedirs(BOT_MEMORY_DIR, exist_ok=True)
        with open(USER_ID_FILE, "w") as f:
            json.dump(user_data, f, indent=2)

        await ctx.send(f"Fetched and stored {len(user_data)} user IDs in server_user_id.json.")

async def setup(bot):
    await bot.add_cog(FetchID(bot))

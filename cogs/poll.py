import discord
from discord.ext import commands
import asyncio
import re
from discord import app_commands

EMOJI_LIST = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']

def parse_duration(duration_str):
    match = re.match(r"(\d+)([smhd])", duration_str.lower())
    if not match:
        return None
    num, unit = match.groups()
    num = int(num)
    return {
        "s": num,
        "m": num * 60,
        "h": num * 3600,
        "d": num * 86400
    }.get(unit, None)

class Poll(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="poll", description="Create a reaction poll: /poll <duration> <question> <comma-separated options>")
    @app_commands.describe(
    duration="Time the poll lasts (e.g. 30s, 5m, 2h)",
    question="The poll question",
    options="Comma-separated options (max 10)")
    async def poll(self, ctx: commands.Context, duration: str, question: str, options: str):
        """Create a timed emoji poll. Duration like 10s, 1m, 2h. Max 10 options."""
        duration_seconds = parse_duration(duration)
        if not duration_seconds:
            await ctx.send("❌ Invalid duration! Use formats like `10s`, `5m`, `2h`")
            return

        option_list = [opt.strip() for opt in options.split(",")]
        if len(option_list) < 2 or len(option_list) > 10:
            await ctx.send("❌ You must provide 2 to 10 options, separated by commas.")
            return

        embed = discord.Embed(title="📊 Poll", description=f'**{question}**', color=discord.Color.blurple())
        for i, option in enumerate(option_list):
            embed.add_field(name=f"{EMOJI_LIST[i]} {option}", value="\u200b", inline=False)
        embed.set_footer(text=f"Poll ends in {duration}")
        msg = await ctx.send(embed=embed)

        for i in range(len(option_list)):
            await msg.add_reaction(EMOJI_LIST[i])

        await asyncio.sleep(duration_seconds)

        # Refresh message to get accurate reaction count
        msg = await ctx.channel.fetch_message(msg.id)
        results = []
        for i, option in enumerate(option_list):
            emoji = EMOJI_LIST[i]
            reaction = discord.utils.get(msg.reactions, emoji=emoji)
            count = (reaction.count - 1) if reaction else 0
            results.append((option, count))

        results.sort(key=lambda x: x[1], reverse=True)
        result_embed = discord.Embed(title="✅ Poll Results", description=f'**{question}**', color=discord.Color.green())
        for option, count in results:
            result_embed.add_field(name=option, value=f"Votes: **{count}**", inline=False)
        await ctx.send(embed=result_embed)

async def setup(bot):
    await bot.add_cog(Poll(bot))

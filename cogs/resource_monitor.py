import discord
from discord.ext import commands
import psutil
import os
import asyncio

class ResourceMonitor(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="usage", description="Show system resources used by the bot")
    @commands.is_owner()
    async def resources(self, ctx):
        process = psutil.Process(os.getpid())

        psutil.cpu_percent(interval=None)
        await asyncio.sleep(1)
        sys_cpu = psutil.cpu_percent(interval=None)
        mem_info = process.memory_info()
        mem_usage_mb = mem_info.rss / 1024 / 1024
        total_mem = psutil.virtual_memory().total / 1024 / 1024
        used_mem = psutil.virtual_memory().used / 1024 / 1024
        mem_percent = psutil.virtual_memory().percent
        bot_mem_percent = (mem_info.rss / psutil.virtual_memory().total) * 100
        disk = psutil.disk_usage('/')

        def bar(percent, length=20):
            filled = int(length * percent // 100)
            empty = length - filled
            return f"[{'█' * filled}{'—' * empty}] {percent:.2f}%"

        embed = discord.Embed(
            title="🖥️ Bot & System Resource Usage",
            color=discord.Color.blurple()
        )
        embed.add_field(
            name="Bot PID",
            value=f"`{os.getpid()}`",
            inline=False
        )
        embed.add_field(
            name="System CPU Usage",
            value=bar(sys_cpu),
            inline=False
        )
        embed.add_field(
            name="Bot Memory Usage",
            value=f"{mem_usage_mb:,.2f} MB " + bar(bot_mem_percent),
            inline=False
        )
        embed.add_field(
            name="System Memory Usage",
            value=f"{used_mem:,.2f} / {total_mem:,.2f} MB " + bar(mem_percent),
            inline=False
        )
        embed.add_field(
            name="Disk Usage",
            value=f"{disk.used / (1024**2):,.2f} / {disk.total / (1024**2):,.2f} MB {bar(disk.percent)}",
            inline=False
        )
        embed.set_footer(text="Resource usage for the current bot process and system.")

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ResourceMonitor(bot))

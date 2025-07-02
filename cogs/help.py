import discord
from discord.ext import commands
from config import HELP_CHANNEL_ID


class HelpEmbedCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.last_help_message_id = None

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        if message.channel.id != HELP_CHANNEL_ID:
            return

        # Delete previous help message if it exists
        if self.last_help_message_id:
            try:
                prev_msg = await message.channel.fetch_message(self.last_help_message_id)
                await prev_msg.delete()
            except discord.NotFound:
                pass  # Message already deleted

        # Send new help embed with support command usage
        embed = discord.Embed(
            title="Need Personal Assistance?",
            description="Use the following slash commands to contact the organizing committee:",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="/open",
            value="Open a private support ticket with the organizing committee.",
            inline=True
        )
        embed.add_field(
            name="/close",
            value="Close your open support ticket when your issue is resolved.",
            inline=True
        )
        embed.set_footer(text="The organizing committee will respond as soon as possible.")
        help_msg = await message.channel.send(embed=embed)
        self.last_help_message_id = help_msg.id

async def setup(bot):
    await bot.add_cog(HelpEmbedCog(bot))

import discord
from discord.ext import commands
from config import *

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        try:
            # Sending DM to the new member
            embed = discord.Embed(
                title=f'Welcome to the server, {member.name}!',
                description=f'I am {BOT_NAME}, the official bot of MBM IDEAX🎉 We are glad to have you here!',
                color=discord.Color.blue()
            )

            embed.set_image(url=f'{WELCOME_BANNER}')
            embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
            embed.add_field(name="Field 1", value="This is the first inline field.", inline=True)
            embed.add_field(name="Field 2", value="This is the second inline field.", inline=True)
            embed.add_field(name="Field 3", value="This is the third inline field.", inline=True)

            await member.send(embed=embed)
            print(f'Sent DM to {member.name}')
        except discord.Forbidden:
            print(f'Could not send DM to {member.name}. They might have DMs disabled.')

        # Sending a welcome message in the specified channel
        try:
            channel = member.guild.get_channel(WELCOME_CHANNEL_ID)
            embed = discord.Embed(
                title=f'Welcome to the server, {member.name}!',
                color=discord.Color.blue()
            )

            embed.set_image(url=f'{WELCOME_BANNER}')
            embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
            await channel.send(embed=embed)
            print(f'Sent welcome message in {channel.name}')
        except Exception as e:
            print(f"Error sending welcome message: {e}")

# Adding the cog to the bot
async def setup(bot):
    await bot.add_cog(Welcome(bot))

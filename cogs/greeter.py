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
                title=f'Welcome to the server, {member.display_name}!',
                description=f'I am {BOT_NAME}, the official bot of MBMC IDEAX🎉 We are glad to have you here!',
                color=discord.Color.blue()
            )

            embed.set_image(url=f'{WELCOME_BANNER}')
            embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
            embed.add_field(
                name="👋 Getting Started",
                value="Introduce yourself in the server and check out the <#general> channel to say hi!",
                inline=False
            )
            embed.add_field(
                name="📢 Stay Updated",
                value="Keep an eye on <#announcements> for the latest news and events.",
                inline=False
            )
            embed.add_field(
                name="🎭 Explore & Connect",
                value="Visit <#roles> to pick your interests and unlock more channels. Don't forget to check our socials below!",
                inline=False
            )

            # Social media buttons
            view = discord.ui.View()
            view.add_item(discord.ui.Button(label="LinkedIn", style=discord.ButtonStyle.link, url="https://www.linkedin.com/company/mbmc-ideax/"))
            view.add_item(discord.ui.Button(label="Instagram", style=discord.ButtonStyle.link, url="https://www.instagram.com/mbmc_ideax/"))
            view.add_item(discord.ui.Button(label="Facebook", style=discord.ButtonStyle.link, url="https://www.facebook.com/mbmcideax/"))
            view.add_item(discord.ui.Button(label="X", style=discord.ButtonStyle.link, url="https://x.com/mbmc_ideax"))
            view.add_item(discord.ui.Button(label="Discord", style=discord.ButtonStyle.link, url="https://discord.gg/FSFsaCVMqf"))

            await member.send(embed=embed, view=view)
            print(f'Sent DM to {member.display_name}')
        except discord.Forbidden:
            print(f'Could not send DM to {member.display_name}. They might have DMs disabled.')

        # Sending a welcome message in the specified channel
        try:
            channel = member.guild.get_channel(WELCOME_CHANNEL_ID)
            embed = discord.Embed(
                title=f'Welcome to the server, {member.display_name}!',
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

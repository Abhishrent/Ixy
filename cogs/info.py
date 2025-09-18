import discord
from config import *
from discord.ext import commands
from discord.ui import Button, View

class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command('commands', description="List all available bot commands.")
    async def listcommands(self, ctx):
        # Create an embed for listing commands
        embed = discord.Embed(
            title = f"{PREFIX[0]} Bot Commands 📜",
            description=f"\n\n`Prefix: {PREFIX[0]}`\n\n",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=f"{EMBED_THUMBNAIL}")
        
        # Add each command with description as fields
        embed.add_field(name="🎟️ **Support & Tickets** (You might need this!)", value="", inline=False)
        embed.add_field(name="/open", value="Creates a private support ticket.", inline=True)
        embed.add_field(name="/close", value="Closes an existing support ticket.", inline=True)
        embed.add_field(
            name="How to use commands",
            value=(
                f"• **Prefix commands:** Type commands starting with the prefix, e.g. `{PREFIX[0]}commands`\n"
                f"• **Slash commands:** Type `/` in the chat and select a command from the menu"
            ),
            inline=False
        )
        embed.set_footer(text="Explore the rest of the commands using slash commands (type `/` in the chat)")

        await ctx.send(embed=embed)

    @commands.hybrid_command('socials', description="Check out our social media links.")
    async def social_media(self, ctx):
        # Create buttons for different social media links
        button_linkedin = Button(label="LinkedIn", style=discord.ButtonStyle.link, url=LINKEDIN_URL)
        button_instagram = Button(label="Instagram", style=discord.ButtonStyle.link, url=INSTAGRAM_URL)
        button_facebook = Button(label="Facebook", style=discord.ButtonStyle.link, url=FACEBOOK_URL)
        button_x = Button(label="X", style=discord.ButtonStyle.link, url=X_URL)

        embed = discord.Embed(
            title="Connect with MBM IdeaX",
            description="Follow us on our official platforms using the buttons below!",
            color=discord.Color.teal()
        )
        embed.set_thumbnail(url=f"{EMBED_THUMBNAIL}")

        # Add buttons to a view
        view = View()
        view.add_item(button_linkedin)
        view.add_item(button_instagram)
        view.add_item(button_facebook)
        view.add_item(button_x)

        # Send the embed with the buttons
        await ctx.send(embed=embed, view=view)

    @commands.hybrid_command('myroles', description="Show your current roles in the server.")
    async def myroles(self, ctx):
        roles = [role.mention for role in ctx.author.roles if role.name != "@everyone"]
        
        if roles:
            roles_list = "\n".join(roles)
        else:
            roles_list = "Currently लावारिस"

        embed = discord.Embed(
            title=f"Roles for {ctx.author.display_name}",
            description=f'{roles_list} \n\n Mention any of the Organizing Team members to get help with roles.',
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=f"{EMBED_THUMBNAIL}")
        await ctx.send(embed=embed)

    @commands.hybrid_command('count', description="Show the total member and bot count for the server.")
    async def member_counter(self, ctx):
        total_members = 0
        total_bots = 0

        # Iterate through all guilds and their members
        for guild in self.bot.guilds:
            for member in guild.members:
                if member.bot:
                    total_bots += 1
                else:
                    total_members += 1

        # Create an embed to display the count
        embed = discord.Embed(
            title="Server Member Count",
            description="",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=f"{EMBED_THUMBNAIL}")
        embed.add_field(name="Total Members (excluding bots)", value=str(total_members), inline=False)
        embed.add_field(name="Total Bots", value=str(total_bots), inline=False)
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url)

        # Send the embed
        await ctx.send(embed=embed)

    @commands.hybrid_command('about', description="Know about me!")
    async def about_bot(self, ctx):
        embed = discord.Embed(
            title = 'About', 
            description = f'{ABOUT_DESCRIPTION}',
            color = discord.Color.blue()
        )
        embed.set_footer(text = '-Created by Abhishrent for IdeaX')
        embed.set_thumbnail(url=f'{EMBED_THUMBNAIL}')
        await ctx.send(embed = embed)

async def setup(bot):
    await bot.add_cog(Info(bot))
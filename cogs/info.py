import discord
from config import *
from discord.ext import commands
from discord.ui import Button, View

class InfoView(View):
    def __init__(self, cog, ctx):
        super().__init__()
        self.cog = cog
        self.ctx = ctx

    @discord.ui.button(label="Commands List", style=discord.ButtonStyle.primary)
    async def commands_button(self, interaction: discord.Interaction, button: Button):
        await self.cog.listcommands(self.ctx)
        await interaction.response.defer()


    @discord.ui.button(label="Member Count", style=discord.ButtonStyle.green)
    async def count_button(self, interaction: discord.Interaction, button: Button):
        await self.cog.member_counter(self.ctx)
        await interaction.response.defer()

    @discord.ui.button(label="Socials", style=discord.ButtonStyle.green)
    async def socials_button(self, interaction: discord.Interaction, button: Button):
        await self.cog.social_media(self.ctx)
        await interaction.response.defer()

    @discord.ui.button(label="Server Roles", style=discord.ButtonStyle.blurple)
    async def roles_button(self, interaction: discord.Interaction, button: Button):
        await self.cog.categorize_roles(self.ctx)
        await interaction.response.defer()

    @discord.ui.button(label="My Roles", style=discord.ButtonStyle.gray)
    async def myroles_button(self, interaction: discord.Interaction, button: Button):
        await self.cog.myroles(self.ctx)
        await interaction.response.defer()

    @discord.ui.button(label="About Bot", style=discord.ButtonStyle.red)
    async def about_button(self, interaction: discord.Interaction, button: Button):
        await self.cog.about_bot(self.ctx)
        await interaction.response.defer()

class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command('info', description="Get information about us")
    async def info_command(self, ctx):
        embed = discord.Embed(
            title=f"{PREFIX[0]} Bot - Interactive Info",
            description="Click the buttons below to get more information!",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=f"{EMBED_THUMBNAIL}")
        embed.add_field(name="Quick Access", value="Use the buttons to quickly access different bot functionalities.", inline=False)
        
        view = InfoView(self, ctx)
        await ctx.send(embed=embed, view=view)


    @commands.hybrid_command('commands', description="List all available bot commands.")
    async def listcommands(self, ctx):
        # Create an embed for listing commands
        embed = discord.Embed(
            title = f"{PREFIX[0]} Bot Commands 📜",
            description=f"\n\n`Prefix: {PREFIX[0]}`\n\n",
            color=discord.Color.blue()
        )
        
        # Add each command with description as fields
        embed.add_field(name="🎟️ **Support & Tickets** (You might need this!)", value="", inline=False)
        embed.add_field(name="open", value="Creates a private support ticket.", inline=True)
        embed.add_field(name="close", value="Closes an existing support ticket.", inline=True)
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
        button_linkedin = Button(label="LinkedIn", style=discord.ButtonStyle.link, url="https://www.linkedin.com/company/mbmc-ideax/")
        button_instagram = Button(label="Instagram", style=discord.ButtonStyle.link, url="https://www.instagram.com/mbmc_ideax/")
        button_x = Button(label="X", style=discord.ButtonStyle.link, url="https://x.com/mbmc_ideax")
        button_facebook = Button(label="Facebook", style=discord.ButtonStyle.link, url="https://www.facebook.com/mbmcideax/")
        button_discord = Button(label="Discord", style=discord.ButtonStyle.link, url="https://discord.gg/FSFsaCVMqf")

        embed = discord.Embed(
            title="Follow us on Social Media!",
            description="Check out our profile on the following platforms:",
            color=discord.Color.blue()
        )

        # Add buttons to a view
        view = View()
        view.add_item(button_linkedin)
        view.add_item(button_instagram)
        view.add_item(button_x)
        view.add_item(button_facebook)
        view.add_item(button_discord)

        # Send the embed with the buttons
        await ctx.send(embed=embed, view=view)



    @commands.hybrid_command('roles', description="List server roles.")
    async def categorize_roles(self, ctx):
        guild = ctx.guild
        admin_roles = []
        mod_roles = []
        community_roles = []
        hobby_roles = []
        special_roles = []
        fun_roles = []

        for role in guild.roles:
            if role.permissions.administrator or role.permissions.manage_guild:
                admin_roles.append(role.name)
            elif role.permissions.kick_members or role.permissions.ban_members:
                mod_roles.append(role.name)
            elif "member" in role.name.lower() or "supporter" in role.name.lower():
                community_roles.append(role.name)
            elif "gamer" in role.name.lower() or "artist" in role.name.lower():
                hobby_roles.append(role.name)
            elif "vip" in role.name.lower() or "access" in role.name.lower():
                special_roles.append(role.name)
            else:
                fun_roles.append(role.name)

        # Create the embed
        embed = discord.Embed(title="Categorized Server Roles", color=discord.Color.blue())
        embed.add_field(name="Administrative Roles", value=", ".join(admin_roles) if admin_roles else "None", inline=False)
        embed.add_field(name="Moderation Roles", value=", ".join(mod_roles) if mod_roles else "None", inline=False)
        embed.add_field(name="Community Roles", value=", ".join(community_roles) if community_roles else "None", inline=False)
        embed.add_field(name="Hobby/Game Roles", value=", ".join(hobby_roles) if hobby_roles else "None", inline=False)
        embed.add_field(name="Special Access Roles", value=", ".join(special_roles) if special_roles else "None", inline=False)
        embed.add_field(name="Custom/Fun Roles", value=", ".join(fun_roles) if fun_roles else "None", inline=False)

        await ctx.send(embed=embed)

    @commands.hybrid_command('myroles', description="Show your current roles in the server.")
    async def myroles(self, ctx):
        roles = [role.mention for role in ctx.author.roles if role.name != "@everyone"]
        
        if roles:
            roles_list = "\n".join(roles)
        else:
            roles_list = "Currently लावारिस"

        embed = discord.Embed(
            title=f"Roles for {ctx.author.display_name}",
            description=f'{roles_list} \n\nHead to <#{ROLES_CHANNEL_ID}> to get roles',
            color=discord.Color.blue()
        )
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
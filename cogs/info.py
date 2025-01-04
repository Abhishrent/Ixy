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

    @commands.command('info')
    async def info_command(self, ctx):
        embed = discord.Embed(
            title=f"{PREFIX[0]} Bot - Interactive Info",
            description="Click the buttons below to get more information!",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=f"{IDEAX_LOGO}")
        embed.add_field(name="Quick Access", value="Use the buttons to quickly access different bot functionalities.", inline=False)
        
        view = InfoView(self, ctx)
        await ctx.send(embed=embed, view=view)


    @commands.command('commands')
    async def listcommands(self, ctx):
        # Create an embed for listing commands
        embed = discord.Embed(
            title = f"{PREFIX[0]} Bot Commands 📜",
            description=f"\n\n`Prefix: {PREFIX[0]}`\n\n",
            color=discord.Color.blue()
        )
        
        # Add each command with description as fields
        embed.add_field(name="💬 **Admin Commands**", value="", inline=False)
        embed.add_field(name="1. udau <amount>", value="Deletes a specified number of messages.", inline=True)
        embed.add_field(name="2. bhana <title>|<content>|<mentions>", value="Sends a custom message with a title and reactions.", inline=True)

        embed.add_field(name="🎟️ **Support & Tickets**", value="", inline=False)
        embed.add_field(name="ujuri", value="Creates a private support ticket.", inline=True)
        embed.add_field(name="bhayo", value="Closes an existing support ticket.", inline=True)

        embed.add_field(name="🔮 **Astrology & Fun**", value="", inline=False)
        embed.add_field(name="1. rashifal <sign>", value="Gets your daily horoscope. \n`(Remember that it shows your Nepali horoscope even though you type your star sign name in English)`", inline=True)
        embed.add_field(name="2. photo", value="Displays a random photo from the event.", inline=True)

        embed.add_field(name="📱 **Information**", value="", inline=False)
        embed.add_field(name="1. socials", value="Displays the social media accounts of IDEAX.", inline=True)
        embed.add_field(name="2. roles", value="Lists categorized roles available on the server.", inline=True)
        embed.add_field(name="3. myroles", value="Displays your current roles.", inline=True)
        embed.add_field(name="4. about", value="Displays information about me!", inline = True)

        embed.add_field(name="📅 **Calendar & Events**", value="", inline=False)
        embed.add_field(name="1. calendar", value="Displays a calendar.", inline=True)
        embed.add_field(name="2. events", value="Displays a list of upcoming events.", inline=True)

        embed.add_field(name="🔨 **Utilities**", value="", inline=False)
        embed.add_field(name="1. hightlight", value="Syntax Highlights your attached code file", inline=True)
        
        embed.add_field(name="📅 **Coming Soon...**", value="", inline=False)
        embed.add_field(name="1. convert <from> <to>", value="Converts file to different format", inline=True)
        embed.add_field(name="2. search <language/library> <keyword>", value="Fetches documentation on a particular function or keyword of popular languages and libraries", inline=True)
        embed.set_footer(text=f"Type {PREFIX[0]} <command> to use a command. Replace <command> with the actual command name.")
        await ctx.send(embed=embed)

    @commands.command('socials')
    async def social_media(self, ctx):
        # Create buttons for different social media links
        button_linkedin = Button(label="LinkedIn", style=discord.ButtonStyle.link, url="https://www.linkedin.com/company/mbmc-ideax/")
        button_instagram = Button(label="Instagram", style=discord.ButtonStyle.link, url="https://www.instagram.com/mbmc_ideax/")
        button_x = Button(label="X", style=discord.ButtonStyle.link, url="https://x.com/mbmc_ideax")
        button_discord = Button(label="Discord", style=discord.ButtonStyle.link, url="https://discord.gg/FSFsaCVMqf")

        # Create an embed
        embed = discord.Embed(
            title="Follow Me on Social Media!",
            description="Check out my profiles on the following platforms:",
            color=discord.Color.blue()
        )

        # Add buttons to a view
        view = View()
        view.add_item(button_linkedin)
        view.add_item(button_instagram)
        view.add_item(button_x)
        view.add_item(button_discord)

        # Send the embed with the buttons
        await ctx.send(embed=embed, view=view)



    @commands.command('roles')
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

    @commands.command('myroles')
    async def myroles(self, ctx):
        roles = [role.mention for role in ctx.author.roles if role.name != "@everyone"]
        
        if roles:
            roles_list = "\n".join(roles)
        else:
            roles_list = "Currently лावारिश्"

        embed = discord.Embed(
            title=f"Roles for {ctx.author.display_name}",
            description=f'{roles_list} \n\nHead to <#{ROLES_CHANNEL_ID}> to get roles',
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

    @commands.command('count')
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

    @commands.command('about')
    async def about_bot(self, ctx):
        embed = discord.Embed(
            title = 'About', 
            description = f'{ABOUT_DESCRIPTION}',
            color = discord.Color.blue()
        )
        embed.set_footer(text = '-Created by Abhishrent for IdeaX')
        embed.set_thumbnail(url=f'{IDEAX_LOGO}')
        await ctx.send(embed = embed)

async def setup(bot):
    await bot.add_cog(Info(bot))
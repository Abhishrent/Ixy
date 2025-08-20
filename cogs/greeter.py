import discord
from discord.ext import commands
from config import *
import random

class WelcomeDetailsSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="About MBM IdeaX", description="Learn about the event", emoji="📋"),
            discord.SelectOption(label="Themes", description="See all event themes", emoji="🎯"),
            discord.SelectOption(label="Timeline", description="Event schedule & timing", emoji="🗓️"),
            discord.SelectOption(label="Socials", description="Official links & contacts", emoji="🌐"),
        ]
        super().__init__(
            placeholder="Explore MBM IdeaX 2025...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="welcome_details_select"
        )

    async def callback(self, interaction: discord.Interaction):
        value = self.values[0]
        if value == "About MBM IdeaX":
            embed = discord.Embed(
                title="Welcome to MBM IdeaX 2025!",
                description=(
                    "MBM IdeaX 2025 is the third iteration of the flagship hackathon by the MBMC IT Club, "
                    "bringing together creative minds to develop impactful solutions using cutting-edge tech. "
                    "This year, the event focuses on sustainable, industry-aligned projects leveraging AI, blockchain, and decentralized systems. "
                    "The event aims to foster innovation, collaboration, and entrepreneurship in Nepal's tech ecosystem."
                ),
                color=discord.Color.blue()
            )
            embed.add_field(
                name="Mission",
                value="Drive positive change through financially viable, innovative solutions.",
                inline=False
            )
            embed.add_field(
                name="Who Can Join?",
                value="Students, tech enthusiasts, and interdisciplinary innovators.",
                inline=False
            )
            embed.set_thumbnail(url=EMBED_THUMBNAIL)
            embed.set_footer(text="MBM IdeaX 2025 • Organized by MBMC IT Club", icon_url=EMBED_FOOTER)
            embed.set_image(url=WELCOME_BANNER)
            view = WelcomeDetailsView()
        elif value == "Themes":
            embed = discord.Embed(
                title="Event Themes",
                description="Explore the official themes for MBM IdeaX 2025:",
                color=discord.Color.green()
            )
            embed.add_field(
                name="1. Travel and Tourism",
                value="Innovations for travel planning, sustainable tourism, and virtual experiences.",
                inline=False
            )
            embed.add_field(
                name="2. Healthcare and Accessibility",
                value="Solutions for telemedicine, assistive technologies, and health monitoring.",
                inline=False
            )
            embed.add_field(
                name="3. Fin-tech",
                value="Projects in mobile payments, financial literacy, and blockchain finance.",
                inline=False
            )
            embed.add_field(
                name="4. Agro-tech",
                value="Precision farming, smart irrigation, and agricultural drones.",
                inline=False
            )
            embed.add_field(
                name="5. Cultural Preservation",
                value="Tech for preserving, promoting, and sharing cultural heritage.",
                inline=False
            )
            embed.add_field(
                name="6. Open Category",
                value="Hybrid, experimental, or cross-disciplinary projects.",
                inline=False
            )
            embed.add_field(
                name="Note on AI",
                value="AI can be integrated into any theme for enhanced impact.",
                inline=False
            )
            embed.set_thumbnail(url=EMBED_THUMBNAIL)
            embed.set_footer(text="MBM IdeaX 2025 • Themes", icon_url=EMBED_FOOTER)
            embed.set_image(url=WELCOME_BANNER)
            view = WelcomeDetailsView()
        elif value == "Timeline":
            embed = discord.Embed(
                title="Event Timeline",
                description=(
                    "MBM IdeaX 2025 features a multi-stage program with workshops, registrations, and hackathon rounds.\n\n"
                    "📍 **ML Workshop:** July 21 to August 1\n"
                    "📍 **IdeaX Registration Opens:** July 21\n"
                    "📍 **Internal Ideathon Registration:** August 10 to August 26\n"
                    "📍 **Internal Ideathon:** August 29\n"
                    "📍 **IdeaX Registration Closes:** September 6\n"
                    "📍 **IdeaX Online Round:** September 11 to 16\n"
                    "📍 **IdeaX Final Hackathon:** October 31, November 1, November 2\n\n"
                    "The event is scheduled for October/November 2025, immediately after Tihar and Chhath holidays."
                ),
                color=discord.Color.orange()
            )
            embed.add_field(
                name="Why this timing?",
                value=(
                    "• Maximized participation (no academic conflicts)\n"
                    "• Festive spirit & positive atmosphere\n"
                    "• Stress-free, creative environment"
                ),
                inline=False
            )
            embed.add_field(
                name="Final Dates",
                value="All dates are coordinated with academic calendars. Stay tuned for updates!",
                inline=False
            )
            embed.set_thumbnail(url=EMBED_THUMBNAIL)
            embed.set_footer(text="MBM IdeaX 2025 • Timeline", icon_url=EMBED_FOOTER)
            embed.set_image(url=WELCOME_BANNER)
            view = WelcomeDetailsView()
        elif value == "Socials":
            embed = discord.Embed(
                title="Connect with MBM IdeaX",
                description="Follow us on our official platforms using the buttons below!",
                color=discord.Color.teal()
            )
            embed.set_thumbnail(url=EMBED_THUMBNAIL)
            embed.set_footer(text="MBM IdeaX 2025 • Socials", icon_url=EMBED_FOOTER)
            embed.set_image(url=WELCOME_BANNER)
            view = WelcomeDetailsView()
            view.add_item(discord.ui.Button(label="LinkedIn", style=discord.ButtonStyle.link, url="https://www.linkedin.com/company/mbmc-ideax/"))
            view.add_item(discord.ui.Button(label="Instagram", style=discord.ButtonStyle.link, url="https://www.instagram.com/mbmc_ideax/"))
            view.add_item(discord.ui.Button(label="Facebook", style=discord.ButtonStyle.link, url="https://www.facebook.com/mbmcideax/"))
            view.add_item(discord.ui.Button(label="X", style=discord.ButtonStyle.link, url="https://x.com/mbmc_ideax"))
            view.add_item(discord.ui.Button(label="Discord", style=discord.ButtonStyle.link, url="https://discord.gg/FSFsaCVMqf"))
        else:
            embed = discord.Embed(
                title="Unknown Selection",
                description="Please select a valid option.",
                color=discord.Color.red()
            )
            embed.set_image(url=WELCOME_BANNER)
            view = WelcomeDetailsView()
        await interaction.response.edit_message(embed=embed, view=view)

class WelcomeDetailsView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)
        self.add_item(WelcomeDetailsSelect())

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

# Sending a welcome dm when a new member joins the server
    @commands.Cog.listener()
    async def on_member_join(self, member):
        try:
            embed = discord.Embed(
                title=f'Welcome to MBM IdeaX 2025, {member.display_name}!',
                description=(
                    f'I am {BOT_NAME}, the official mascot of MBM IDEAX 🎉\n'
                    "We're glad to have you here! Use the dropdown below to explore event details, themes, tracks, timeline, and socials."
                ),
                color=discord.Color.teal()
            )
            embed.set_thumbnail(url=EMBED_THUMBNAIL)
            embed.set_footer(text="MBM IdeaX 2025 • Organized by MBMC IT Club", icon_url=EMBED_FOOTER)
            embed.set_image(url=WELCOME_BANNER)
            view = WelcomeDetailsView()
            await member.send(embed=embed, view=view)
            print(f'Sent DM to {member.display_name}')
        except discord.Forbidden:
            print(f'Could not send DM to {member.display_name}. They might have DMs disabled.')

# Sending a welcome message in the specified channel
        try:
            channel = member.guild.get_channel(WELCOME_CHANNEL_ID)
            welcome_messages = [
                f"Hey! {member.display_name} just landed! 🚀",
                f"Everyone, please welcome {member.display_name}! 🎉",
                f"{member.display_name} joined the party! 🥳",
                f"Look who's here! It's {member.display_name}! 👋",
                f"Give it up for our newest member, {member.display_name}! 🙌",
                f"{member.display_name} has entered the server! 🎊",
                f"Cheers! {member.display_name} is now with us! 🍻",
                f"Welcome aboard, {member.display_name}! ⛵",
                f"{member.display_name} just joined. Let's make some noise! 🔔",
                f"Glad to have you, {member.display_name}! 🌟",
                f"A wild {member.display_name} appeared! 🐾",
                f"{member.display_name} just teleported in! 🌀",
                f"Sound the trumpets! {member.display_name} is here! 🎺",
                f"{member.display_name} just unlocked a new achievement: Joined MBM IdeaX! 🏆",
                f"Welcome to the crew, {member.display_name}! 🚢",
                f"{member.display_name} just hopped on the MBM IdeaX train! 🚂",
                f"New challenger approaching: {member.display_name}! 🕹️",
                f"{member.display_name} just made the server cooler! ❄️",
                f"Let's roll out the red carpet for {member.display_name}! 🎬",
                f"{member.display_name} just boosted our awesomeness! 💯",
                f"MBM IdeaX just got better with {member.display_name} here! 🥇",
                f"Raise your glasses for {member.display_name}! 🥂",
                f"{member.display_name} is now part of the family! 🤗",
                f"Welcome, {member.display_name}! Adventure awaits! 🗺️",
                f"{member.display_name} just spawned in! 🕹️",
                f"Alert! {member.display_name} has joined the fun zone! 🚨",
                f"{member.display_name} just dropped in with style! 😎",
                f"Did someone order extra awesome? {member.display_name} is here! 🍕",
                f"{member.display_name} just leveled up our server! ⬆️",
                f"Yay! {member.display_name} just crossed the portal! 🌀",
                f"{member.display_name} just brought the party with them! 🎈",
                f"Server XP increased! Thanks, {member.display_name}! 📈",
                f"{member.display_name} just rolled a natural 20 on joining! 🎲",
                f"Give a warm MBM IdeaX welcome to {member.display_name}! 🔥",
                f"{member.display_name} just made this place legendary! 🏅",
                f"Confetti time! {member.display_name} is here! 🎊",
                f"{member.display_name} just joined the adventure guild! 🏰",
                f"Welcome, {member.display_name}! May your memes be ever dank. 😂",
                f"{member.display_name} just brought the sunshine! ☀️",
                f"Server population +1: {member.display_name} has arrived! 👤",
                f"{member.display_name} just entered the chat! 💬",
                f"Welcome, {member.display_name}! The cake is not a lie. 🎂",
                f"{member.display_name} just made the server sparkle! ✨",
                f"Let the games begin! {member.display_name} is here! 🏁",
                f"{member.display_name} just joined the squad! 🛡️",
                f"Welcome, {member.display_name}! May your code always compile. 💻",
                f"{member.display_name} just brought the good vibes! 🎵",
                f"Achievement unlocked: {member.display_name} joined the server! 🥳",
            ]
            chosen_message = random.choice(welcome_messages)
            embed = discord.Embed(
                title=chosen_message,
                color=discord.Color.blue()
            )
            embed.set_image(url=f'{WELCOME_GRAPHICS}')
            # current member count
            embed.set_footer(text=f"Member-count: {member.guild.member_count}", icon_url=EMBED_FOOTER)
            #embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
            await channel.send(embed=embed)
            print(f'Sent welcome message in {channel.name}')
        except Exception as e:
            print(f"Error sending welcome message: {e}")

# Adding the cog to the bot
async def setup(bot):
    await bot.add_cog(Welcome(bot))

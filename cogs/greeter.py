import discord
from discord.ext import commands
from config import *
import random
from utils.event_embeds import EventEmbeds

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
            embed = EventEmbeds.get_overview_embed(include_banner=True)
            embed.title = "Welcome to MBM IdeaX 2025!"
            view = WelcomeDetailsView()
        elif value == "Themes":
            embed = EventEmbeds.get_themes_embed(include_banner=True)
            view = WelcomeDetailsView()
        elif value == "Timeline":
            embed = EventEmbeds.get_timeline_embed(include_banner=True)
            view = WelcomeDetailsView()
        elif value == "Socials":
            embed = EventEmbeds.get_socials_embed(include_banner=True)
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

import discord
from discord.ext import commands
from config import *

class WelcomeDetailsSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="About MBM IdeaX", description="Learn about the event", emoji="📋"),
            discord.SelectOption(label="Themes", description="See all event themes", emoji="🎯"),
            discord.SelectOption(label="Tracks", description="Explore project tracks", emoji="🛤️"),
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
                    "This year, the event focuses on sustainable, industry-aligned projects leveraging AI, blockchain, and decentralized systems."
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
            view = WelcomeDetailsView()
        elif value == "Themes":
            embed = discord.Embed(
                title="Event Themes",
                description="Seven themes inspire participants to tackle real-world challenges:",
                color=discord.Color.green()
            )
            embed.add_field(
                name="1. Healthcare & Accessibility",
                value="Telemedicine, assistive tech, health monitoring.",
                inline=False
            )
            embed.add_field(
                name="2. Environment & Climate Action",
                value="Carbon tracking, renewable energy, waste management.",
                inline=False
            )
            embed.add_field(
                name="3. Cybersecurity",
                value="Authentication, encryption, threat detection.",
                inline=False
            )
            embed.add_field(
                name="4. Fintech",
                value="Mobile payments, financial literacy, blockchain finance.",
                inline=False
            )
            embed.add_field(
                name="5. Decentralization",
                value="dApps, blockchain identity, peer-to-peer networks.",
                inline=False
            )
            embed.add_field(
                name="6. Travel & Tourism",
                value="Virtual tours, sustainable tourism, travel planning.",
                inline=False
            )
            embed.add_field(
                name="7. Agro-tech",
                value="Precision farming, smart irrigation, crop drones.",
                inline=False
            )
            embed.add_field(
                name="Note on AI",
                value="AI can be integrated into any theme for enhanced impact.",
                inline=False
            )
            embed.set_thumbnail(url=EMBED_THUMBNAIL)
            embed.set_footer(text="MBM IdeaX 2025 • Themes", icon_url=EMBED_FOOTER)
            view = WelcomeDetailsView()
        elif value == "Tracks":
            embed = discord.Embed(
                title="Project Tracks",
                description="Six tracks for diverse, tech-driven projects:",
                color=discord.Color.purple()
            )
            embed.add_field(
                name="1. AR/VR",
                value="Immersive apps: education, tourism, healthcare.",
                inline=False
            )
            embed.add_field(
                name="2. Game Development",
                value="Games for social awareness, education, environment.",
                inline=False
            )
            embed.add_field(
                name="3. IoT",
                value="Smart homes, agri sensors, connected healthcare.",
                inline=False
            )
            embed.add_field(
                name="4. AI & Machine Learning",
                value="Predictive analytics, AI finance, ML for environment.",
                inline=False
            )
            embed.add_field(
                name="5. Blockchain & Decentralization",
                value="Voting, supply chain, cryptocurrency platforms.",
                inline=False
            )
            embed.add_field(
                name="6. Open Technology",
                value="Hybrid, experimental, or cross-disciplinary projects.",
                inline=False
            )
            embed.set_thumbnail(url=EMBED_THUMBNAIL)
            embed.set_footer(text="MBM IdeaX 2025 • Tracks", icon_url=EMBED_FOOTER)
            view = WelcomeDetailsView()
        elif value == "Timeline":
            embed = discord.Embed(
                title="Event Timeline",
                description=(
                    "MBM IdeaX 2025 is scheduled for Kartik (October/November 2025), "
                    "immediately after Tihar and Chhath holidays."
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
                value="To be announced, coordinated with academic calendars.",
                inline=False
            )
            embed.set_thumbnail(url=EMBED_THUMBNAIL)
            embed.set_footer(text="MBM IdeaX 2025 • Timeline", icon_url=EMBED_FOOTER)
            view = WelcomeDetailsView()
        elif value == "Socials":
            embed = discord.Embed(
                title="Connect with MBM IdeaX",
                description="Follow us on our official platforms using the buttons below!",
                color=discord.Color.teal()
            )
            embed.set_thumbnail(url=EMBED_THUMBNAIL)
            embed.set_footer(text="MBM IdeaX 2025 • Socials", icon_url=EMBED_FOOTER)
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
            view = WelcomeDetailsView()
        await interaction.response.edit_message(embed=embed, view=view)

class WelcomeDetailsView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)
        self.add_item(WelcomeDetailsSelect())

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        try:
            embed = discord.Embed(
                title=f'Welcome to MBM IdeaX 2025, {member.display_name}!',
                description=(
                    f'I am {BOT_NAME}, the official bot of MBMC IDEAX 🎉\n'
                    "We're glad to have you here! Use the dropdown below to explore event details, themes, tracks, timeline, and socials."
                ),
                color=discord.Color.teal()
            )
            embed.set_thumbnail(url=EMBED_THUMBNAIL)
            embed.set_footer(text="MBM IdeaX 2025 • Organized by MBMC IT Club", icon_url=EMBED_FOOTER)
            view = WelcomeDetailsView()
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

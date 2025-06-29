import discord
from discord.ext import commands
from config import EMBED_THUMBNAIL, EMBED_FOOTER, EMBED_IMAGE

class EventDetailsSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Overview", description="General event overview", emoji="📋"),
            discord.SelectOption(label="Themes", description="See all event themes", emoji="🎯"),
            discord.SelectOption(label="Tracks", description="Explore project tracks", emoji="🛤️"),
            discord.SelectOption(label="Timeline", description="Event schedule & timing", emoji="🗓️"),
        ]
        super().__init__(
            placeholder="Select event info to view...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="eventdetails_select"
        )

    async def callback(self, interaction: discord.Interaction):
        value = self.values[0]
        if value == "Overview":
            embed = discord.Embed(
                title="MBM IdeaX 2025: Overview",
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
        else:
            embed = discord.Embed(
                title="Unknown Selection",
                description="Please select a valid option.",
                color=discord.Color.red()
            )
        await interaction.response.edit_message(embed=embed, view=self.view)

class EventDetailsView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)
        self.add_item(EventDetailsSelect())

class EventDetails(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="eventdetails", description="Get detailed info about MBM IdeaX 2025 event.")
    async def event_details(self, ctx):
        embed = discord.Embed(
            title="MBM IdeaX 2025: Event Details",
            description=(
                "Welcome to MBM IdeaX 2025! Use the dropdown below to explore event overview, themes, tracks, and timeline."
            ),
            color=discord.Color.teal()
        )
        embed.set_thumbnail(url=EMBED_THUMBNAIL)
        embed.set_footer(text="MBM IdeaX 2025 • Organized by MBMC IT Club", icon_url=EMBED_FOOTER)
        view = EventDetailsView()
        await ctx.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(EventDetails(bot))

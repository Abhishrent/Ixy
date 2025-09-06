import discord
from discord.ext import commands
from config import EMBED_THUMBNAIL, EMBED_FOOTER, EMBED_IMAGE

class EventDetailsSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Overview", description="General event overview", emoji="📋"),
            discord.SelectOption(label="Themes", description="See all event themes", emoji="🎯"),
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

        elif value == "Timeline":
            embed = discord.Embed(
                title="Event Timeline",
                description=(
                    "MBM IdeaX 2025 features a multi-stage program with workshops, registrations, and hackathon rounds.\n\n"
                    "📍 **ML Workshop:** July 21 to August 1\n"
                    "📍 **IdeaX Registration Opens:** July 21\n"
                    "📍 **Internal Ideathon Registration:** August 10 to August 26\n"
                    "📍 **Internal Ideathon:** August 29\n"
                    "📍 **IdeaX Registration Closes:** September 16\n"
                    "📍 **IdeaX Online Round:** September 19 to 21\n"
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
                "Welcome to MBM IdeaX 2025! Use the dropdown below to explore event overview, themes, and timeline."
            ),
            color=discord.Color.teal()
        )
        embed.set_thumbnail(url=EMBED_THUMBNAIL)
        embed.set_footer(text="MBM IdeaX 2025 • Organized by MBMC IT Club", icon_url=EMBED_FOOTER)
        view = EventDetailsView()
        await ctx.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(EventDetails(bot))

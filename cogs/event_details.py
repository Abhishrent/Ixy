import discord
from discord.ext import commands
from config import EMBED_THUMBNAIL, EMBED_FOOTER, EMBED_IMAGE
from utils.event_embeds import EventEmbeds

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
            embed = EventEmbeds.get_overview_embed()
        elif value == "Themes":
            embed = EventEmbeds.get_themes_embed()
        elif value == "Timeline":
            embed = EventEmbeds.get_timeline_embed()
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

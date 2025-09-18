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
            discord.SelectOption(label="Event Format", description="Competition format & rounds", emoji="🏆"),
            discord.SelectOption(label="Prize Pool", description="Cash prizes & rewards", emoji="💰"),
            discord.SelectOption(label="Participation Details", description="Teams, accommodation & perks", emoji="🧑‍🤝‍🧑"),
            discord.SelectOption(label="Organizing Team", description="Meet the team behind IdeaX", emoji="👥"),
            discord.SelectOption(label="Socials", description="Official links & contacts", emoji="🌐"),
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
            view = EventDetailsView()
        elif value == "Themes":
            embed = EventEmbeds.get_themes_embed()
            view = EventDetailsView()
        elif value == "Timeline":
            embed = EventEmbeds.get_timeline_embed()
            view = EventDetailsView()
        elif value == "Event Format":
            embed = EventEmbeds.get_event_format_embed()
            view = EventDetailsView()
        elif value == "Prize Pool":
            embed = EventEmbeds.get_prize_pool_embed()
            view = EventDetailsView()
        elif value == "Participation Details":
            embed = EventEmbeds.get_participation_details_embed()
            view = EventDetailsView()
        elif value == "Organizing Team":
            embed = EventEmbeds.get_organizing_team_embed()
            view = EventDetailsView()
        elif value == "Socials":
            embed = EventEmbeds.get_socials_embed()
            view = EventDetailsView()
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
            view = EventDetailsView()

        await interaction.response.edit_message(embed=embed, view=view)

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

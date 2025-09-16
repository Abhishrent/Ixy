# filepath: /home/abhishrent/Projects/ixyBot/utils/event_embeds.py
import discord
from config import EMBED_THUMBNAIL, EMBED_FOOTER, WELCOME_BANNER

class EventEmbeds:
    @staticmethod
    def get_overview_embed(include_banner=False):
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
        
        if include_banner:
            embed.set_image(url=WELCOME_BANNER)
        
        return embed

    @staticmethod
    def get_themes_embed(include_banner=False):
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
        
        if include_banner:
            embed.set_image(url=WELCOME_BANNER)
        
        return embed

    @staticmethod
    def get_timeline_embed(include_banner=False):
        embed = discord.Embed(
            title="Event Timeline",
            description=(
                "MBM IdeaX 2025 features a multi-stage program with workshops, registrations, and hackathon rounds.\n\n"
                "📍 **ML Workshop:** July 21 to August 1\n"
                "📍 **IdeaX Registration Opens:** July 21\n"
                "📍 **Internal Ideathon Registration:** August 10 to August 26\n"
                "📍 **Internal Ideathon:** August 29\n"
                "📍 **IdeaX Registration Closes:** September 16\n"
                "📍 **IdeaX Online Round:** After Dashain - Dates To be Announced\n"
                "📍 **IdeaX Final Hackathon:** To be Announced\n\n"
            ),
            color=discord.Color.orange()
        )
        # embed.add_field(
        #     name="Why this timing?",
        #     value=(
        #         "• Maximized participation (no academic conflicts)\n"
        #         "• Festive spirit & positive atmosphere\n"
        #         "• Stress-free, creative environment"
        #     ),
        #     inline=False
        # )
        embed.add_field(
            name="Final Dates",
            value="All dates to be coordinated with academic calendars. Stay tuned for updates!",
            inline=False
        )
        embed.set_thumbnail(url=EMBED_THUMBNAIL)
        embed.set_footer(text="MBM IdeaX 2025 • Timeline", icon_url=EMBED_FOOTER)
        
        if include_banner:
            embed.set_image(url=WELCOME_BANNER)
        
        return embed

    @staticmethod
    def get_socials_embed(include_banner=False):
        embed = discord.Embed(
            title="Connect with MBM IdeaX",
            description="Follow us on our official platforms using the buttons below!",
            color=discord.Color.teal()
        )
        embed.set_thumbnail(url=EMBED_THUMBNAIL)
        embed.set_footer(text="MBM IdeaX 2025 • Socials", icon_url=EMBED_FOOTER)
        
        if include_banner:
            embed.set_image(url=WELCOME_BANNER)
        
        return embed
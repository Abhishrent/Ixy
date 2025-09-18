import discord
import json
import os
from datetime import datetime
from config import EMBED_THUMBNAIL, EMBED_FOOTER, WELCOME_BANNER

# Path to the editable config
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "../config/event_config.json")

class EventEmbeds:
    _last_modified = None
    _cached_config = None
    
    @staticmethod
    def _load_config():
        """Load configuration with caching and hot reload"""
        try:
            if os.path.exists(CONFIG_PATH):
                # Check if file was modified
                current_modified = os.path.getmtime(CONFIG_PATH)
                if (EventEmbeds._last_modified is None or 
                    current_modified > EventEmbeds._last_modified):
                    
                    with open(CONFIG_PATH, 'r') as f:
                        EventEmbeds._cached_config = json.load(f)
                    EventEmbeds._last_modified = current_modified
                    print(f"[{datetime.now()}] Event config reloaded!")
                
                return EventEmbeds._cached_config
        except Exception as e:
            print(f"Error loading config: {e}")
        
        # Fallback to default config
        return EventEmbeds._get_default_config()
    
    @staticmethod
    def _get_default_config():
        """Default configuration as fallback"""
        return {
            "overview": {
                "title": "MBM IdeaX 2025: Overview",
                "description": "MBM IdeaX 2025 is the third iteration of the flagship hackathon by the MBMC IT Club, bringing together creative minds to develop impactful solutions using cutting-edge tech. This year, the event focuses on sustainable, industry-aligned projects leveraging AI, blockchain, and decentralized systems. The event aims to foster innovation, collaboration, and entrepreneurship in Nepal's tech ecosystem.",
                "color": "blue",
                "fields": [
                    {
                        "name": "Mission",
                        "value": "Drive positive change through financially viable, innovative solutions.",
                        "inline": False
                    },
                    {
                        "name": "Who Can Join?",
                        "value": "Students, tech enthusiasts, and interdisciplinary innovators.",
                        "inline": False
                    }
                ]
            },
            "themes": {
                "title": "Event Themes",
                "description": "Explore the official themes for MBM IdeaX 2025:",
                "color": "green",
                "fields": [
                    {
                        "name": "1. Travel and Tourism",
                        "value": "Innovations for travel planning, sustainable tourism, and virtual experiences.",
                        "inline": False
                    },
                    {
                        "name": "2. Healthcare and Accessibility",
                        "value": "Solutions for telemedicine, assistive technologies, and health monitoring.",
                        "inline": False
                    },
                    {
                        "name": "3. Fin-tech",
                        "value": "Projects in mobile payments, financial literacy, and blockchain finance.",
                        "inline": False
                    },
                    {
                        "name": "4. Agro-tech",
                        "value": "Precision farming, smart irrigation, and agricultural drones.",
                        "inline": False
                    },
                    {
                        "name": "5. Cultural Preservation",
                        "value": "Tech for preserving, promoting, and sharing cultural heritage.",
                        "inline": False
                    },
                    {
                        "name": "6. Open Category",
                        "value": "Hybrid, experimental, or cross-disciplinary projects.",
                        "inline": False
                    },
                    {
                        "name": "Note on AI",
                        "value": "AI can be integrated into any theme for enhanced impact.",
                        "inline": False
                    }
                ]
            },
            "timeline": {
                "title": "Event Timeline",
                "description": "MBM IdeaX 2025 features a multi-stage program with workshops, registrations, and hackathon rounds.\n\n📍 **ML Workshop:** Jul 21 to Aug 1\n📍 **IdeaX Registration Opens:** Jul 21\n📍 **Internal Ideathon Registration:** Aug 10 to Aug 26\n📍 **Internal Ideathon:** Aug 29\n📍 **IdeaX Registration Closes:** ~~Sep 16~~ Oct 4\n📍 **IdeaX Online Round:** After Dashain - Dates to be announced\n📍 **IdeaX Final Hackathon:** To be Announced\n\n",
                "color": "orange",
                "fields": [
                    {
                        "name": "Final Dates",
                        "value": "All dates to be coordinated with academic calendars. Stay tuned for updates!",
                        "inline": False
                    }
                ]
            },
            "socials": {
                "title": "Connect with MBM IdeaX",
                "description": "Follow us on our official platforms using the buttons below!",
                "color": "teal",
                "fields": []
            }
        }
    
    @staticmethod
    def _get_color(color_name):
        """Convert color name to discord.Color"""
        colors = {
            "blue": discord.Color.blue(),
            "green": discord.Color.green(),
            "orange": discord.Color.orange(),
            "teal": discord.Color.teal(),
            "red": discord.Color.red(),
            "purple": discord.Color.purple(),
            "gold": discord.Color.gold()
        }
        return colors.get(color_name.lower(), discord.Color.blue())
    
    @staticmethod
    def _build_embed(embed_type, include_banner=False):
        """Build embed from config"""
        config = EventEmbeds._load_config()
        embed_config = config.get(embed_type, {})
        
        embed = discord.Embed(
            title=embed_config.get("title", "Event Info"),
            description=embed_config.get("description", ""),
            color=EventEmbeds._get_color(embed_config.get("color", "blue"))
        )
        
        # Add fields
        for field in embed_config.get("fields", []):
            embed.add_field(
                name=field.get("name", ""),
                value=field.get("value", ""),
                inline=field.get("inline", False)
            )
        
        embed.set_thumbnail(url=EMBED_THUMBNAIL)
        embed.set_footer(
            text=f"MBM IdeaX 2025 • {embed_config.get('title', 'Event Info')}", 
            icon_url=EMBED_FOOTER
        )
        
        if include_banner:
            embed.set_image(url=WELCOME_BANNER)
        
        return embed
    
    @staticmethod
    def get_overview_embed(include_banner=False):
        return EventEmbeds._build_embed("overview", include_banner)
    
    @staticmethod
    def get_themes_embed(include_banner=False):
        return EventEmbeds._build_embed("themes", include_banner)
    
    @staticmethod
    def get_timeline_embed(include_banner=False):
        return EventEmbeds._build_embed("timeline", include_banner)
    
    @staticmethod
    def get_socials_embed(include_banner=False):
        return EventEmbeds._build_embed("socials", include_banner)
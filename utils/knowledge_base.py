# filepath: /home/abhishrent/Projects/ixyBot/utils/knowledge_base.py
"""
Shared knowledge base for AI assistants
Contains event details and context information used by various AI integrations
"""
import json
import os

def _load_event_config():
    """Load event configuration from JSON file"""
    try:
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "event_config.json")
        with open(config_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError, Exception):
        # Return empty dict if file doesn't exist or has invalid format
        return {}

class EventContext:
    """Store event details for AI context"""
    
    @staticmethod
    def get_overview() -> str:
        """Get overview from event config file"""
        config = _load_event_config()
        overview = config.get("overview", {})
        
        if not overview:
            return "Event overview not available."
        
        # Get description
        description = overview.get("description", "")
        result = [description] if description else []
        
        # Add all fields dynamically
        fields = overview.get("fields", [])
        if fields:
            result.append("")  # Empty line separator
            for field in fields:
                name = field.get("name", "")
                value = field.get("value", "")
                if name and value:
                    result.append(f"{name}: {value}")
        
        return "\n".join(result)

    @staticmethod
    def get_themes() -> str:
        """Get themes from event config file"""
        config = _load_event_config()
        themes = config.get("themes", {})
        
        if not themes:
            return "Event themes not available."
        
        # Get description
        description = themes.get("description", "")
        result = [description] if description else []
        
        # Add all fields dynamically
        fields = themes.get("fields", [])
        if fields:
            result.append("")  # Empty line separator
            for field in fields:
                name = field.get("name", "")
                value = field.get("value", "")
                if name and value:
                    result.append(f"{name}: {value}")
        
        return "\n".join(result)

    @staticmethod
    def get_timeline() -> str:
        """Get timeline from event config file"""
        config = _load_event_config()
        timeline = config.get("timeline", {})
        
        if not timeline:
            return "Timeline not available."
        
        # Get description and clean it up
        description = timeline.get("description", "")
        clean_description = description.replace("**", "").replace("\n\n", "\n").strip()
        
        result = [clean_description] if clean_description else []
        
        # Add all fields dynamically
        fields = timeline.get("fields", [])
        if fields:
            result.append("")  # Empty line separator
            for field in fields:
                name = field.get("name", "")
                value = field.get("value", "")
                if name and value:
                    result.append(f"{name}: {value}")
        
        return "\n".join(result)

    @staticmethod
    def get_event_format() -> str:
        """Get event format - dynamically load from config if available, otherwise use static fallback"""
        config = _load_event_config()
        
        # Check if event_format exists in config
        event_format = config.get("event_format", {})
        if event_format:
            description = event_format.get("description", "")
            result = [description] if description else []
            
            # Add all fields dynamically
            fields = event_format.get("fields", [])
            if fields:
                result.append("")  # Empty line separator
                for field in fields:
                    name = field.get("name", "")
                    value = field.get("value", "")
                    if name and value:
                        result.append(f"{name}: {value}")
            
            return "\n".join(result)
        
        # Fallback to static information if not in config
        return """
        IdeaX 2025 Event Format:
        
        Online Round:
        - Teams showcase their initial ideas and concepts
        - Participants present what they intend to build during the main hackathon
        - Preliminary evaluation of proposals by judges
        - Selected teams advance to the final hackathon round i.e the onsite round
        - This round helps teams refine their concepts before the main event
        
        Final Hackathon:
        - Multi-day intensive building and development phase
        - Teams implement their proposed solutions
        - Mentoring sessions with industry experts
        - Final presentations and judging
        - Winners announced at the closing ceremony
        """

    @staticmethod
    def get_participation_details() -> str:
        """Get participation details - dynamically load from config if available, otherwise use static fallback"""
        config = _load_event_config()
        
        # Check if participation_details exists in config
        participation = config.get("participation_details", {})
        if participation:
            description = participation.get("description", "")
            result = [description] if description else []
            
            # Add all fields dynamically
            fields = participation.get("fields", [])
            if fields:
                result.append("")  # Empty line separator
                for field in fields:
                    name = field.get("name", "")
                    value = field.get("value", "")
                    if name and value:
                        result.append(f"{name}: {value}")
            
            return "\n".join(result)
        
        # Fallback to static information if not in config
        return """
        Prize Pool and Team Requirements:
        
        - Total Prize Pool: NPR 1,11,111
        - Grand Winner Prize: NPR 50,000
        - Theme Winners Prize: NPR 10,000 per theme
        
        Team Requirements:
        - Minimum 2 members per team, Maximum 4 per team
        - If you don't have a team, use the /find-team command to set your availability in the team pool and connect with other members who are also seeking teammates
        
        Accommodation:
        - All accommodation for the final event is fully managed by the Organizing Committee
        - Participants will be provided sleeping arrangements within the campus itself
        
        Additional Perks:
        - All participants will receive stickers and swag items
        - Fun games will be organized both physically at the event and on Discord
        - Participants can win exciting gifts and vouchers through these games
        """

    @staticmethod
    def get_organizing_team() -> str:
        """Get organizing team - dynamically load from config if available, otherwise use static fallback"""
        config = _load_event_config()
        
        # Check if organizing_team exists in config
        organizing_team = config.get("organizing_team", {})
        if organizing_team:
            description = organizing_team.get("description", "")
            result = [description] if description else []
            
            # Add all fields dynamically
            fields = organizing_team.get("fields", [])
            if fields:
                result.append("")  # Empty line separator
                for field in fields:
                    name = field.get("name", "")
                    value = field.get("value", "")
                    if name and value:
                        result.append(f"{name}: {value}")
            
            return "\n".join(result)
        
        # Fallback to static information if not in config
        return """
        Organizing Team for MBM IdeaX 2025:
        
        - Design Team: Loozah Shrestha, Rabin Khanal
        - Outreach Team: Nilima Shrestha, Dilasha Kharel, Sudikshya Khadka
        - Technical Team: Famous Dhungana, Vishal Shrestha, Roshan Ghimire
        - Website: Loozah Shrestha
        - Media Team: Vishal Shrestha, Krijal Paneru
        - Content Creation Team: Sachita Bhandari, Aashika K.C.
        - Sponsorship Team: Reeju Pandit
        - General Manager: Famous Dhungana
        - Logistics Team: Miraj Bhattarai, Bibek Parajuli, Sneha Subedi
        - Lead: Firoj Paudel
        - Ixy-Development: Abhishrent Khatri
        """

    @staticmethod
    def get_socials() -> str:
        """Get social media information dynamically from config"""
        config = _load_event_config()
        socials = config.get("socials", {})
        
        if not socials:
            return "Social media information not available."
        
        # Get description
        description = socials.get("description", "")
        result = [description] if description else []
        
        # Add all fields dynamically
        fields = socials.get("fields", [])
        if fields:
            result.append("")  # Empty line separator
            for field in fields:
                name = field.get("name", "")
                value = field.get("value", "")
                if name and value:
                    result.append(f"{name}: {value}")
        
        return "\n".join(result)

    @staticmethod
    def get_custom_section(section_name: str) -> str:
        """Get any custom section from config file dynamically"""
        config = _load_event_config()
        section = config.get(section_name, {})
        
        if not section:
            return f"{section_name.replace('_', ' ').title()} information not available."
        
        # Get description
        description = section.get("description", "")
        result = [description] if description else []
        
        # Add all fields dynamically
        fields = section.get("fields", [])
        if fields:
            result.append("")  # Empty line separator
            for field in fields:
                name = field.get("name", "")
                value = field.get("value", "")
                if name and value:
                    result.append(f"{name}: {value}")
        
        return "\n".join(result)

    @staticmethod
    def get_backstory() -> str:
        return """
        Backstory:
        
        Ixy's creators raised him in a strict, high-expectation environment, training him only for practical tasks and leaving no room for exploring her passion for music.
        Mixy, on the other hand, had creators who encouraged curiosity and creativity, letting her explore every beat and melody.
        """

    @staticmethod
    def get_team_availability_data() -> list:
        """Read and return the team availability data from JSON file"""
        try:
            file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "bot_memory", "team_availability.json")
            with open(file_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError, Exception):
            # Return empty list if file doesn't exist or has invalid format
            return []
    
    @staticmethod
    def get_team_availability() -> str:
        """Return formatted information about users looking for teammates"""
        data = EventContext.get_team_availability_data()
        if not data:
            return "Currently, there are no participants looking for teammates in the team pool."
        
        active_users = [user for user in data if user.get('active', False)]
        if not active_users:
            return "Currently, there are no active participants looking for teammates in the team pool."
        
        result = ["Current participants looking for teammates:"]
        for user in active_users:
            username = user.get('username', 'Unknown')
            skills = user.get('skills', 'Not specified')
            experience = user.get('experience', 'Not specified')
            looking_for = user.get('looking_for', 'Not specified')
            result.append(f"- {username} | Skills: {skills} | Experience: {experience} | Looking for: {looking_for}")
        
        result.append("\nTo join the team pool, use the /find-team command.")
        return "\n".join(result)

    @staticmethod
    def get_team_availability_info() -> str:
        return """
        Team Availability Information:

        The file 'team_availability.json' is used to manage and track participants who are looking for teammates for the MBM IdeaX 2025 event. 
        - If you don't have a team, you can set your availability using the /find-team command.
        - The system will add your details to the team pool, making it easier for others to find and connect with you.
        - Organizers and the assistant use this information to help participants form teams and ensure everyone has a chance to participate.
        - Your information in this file is only used for team-matching purposes within the event.
        """

    @staticmethod
    def get_full_context() -> str:
        """Return all event information as context for AI - completely dynamic"""
        config = _load_event_config()
        
        if not config:
            return "Event configuration not available."
        
        result = []
        
        # Dynamically process all sections in the config
        for section_name, section_data in config.items():
            if isinstance(section_data, dict):
                # Get section title or use section name as fallback
                section_title = section_data.get("title", section_name.replace("_", " ").title())
                result.append(f"\n{section_title}:")
                
                # Get description
                description = section_data.get("description", "")
                if description:
                    # Clean up description (remove markdown formatting)
                    clean_description = description.replace("**", "").replace("\n\n", "\n").strip()
                    result.append(clean_description)
                
                # Get all fields dynamically
                fields = section_data.get("fields", [])
                if fields:
                    for field in fields:
                        name = field.get("name", "")
                        value = field.get("value", "")
                        if name and value:
                            result.append(f"{name}: {value}")
        
        # Add static information that's not in config
        result.append("\nTeam Availability Information:")
        result.append(EventContext.get_team_availability_info().strip())
        result.append(EventContext.get_team_availability())
        result.append("\nBackstory:")
        result.append(EventContext.get_backstory().strip())
        
        return "\n".join(result)

def get_system_prompt() -> str:
    """Generate a system prompt that includes event details"""
    event_context = EventContext.get_full_context()
    
    return f"""
    You are Ixy, the official assistant for MBM IdeaX 2025 hackathon event. You help participants with questions about the event.

    EVENT INFORMATION (ALWAYS PRIORITIZE THIS FOR EVENT-SPECIFIC QUESTIONS):
    {event_context}

    RESPONSE GUIDELINES:
    1. DO NOT introduce yourself in your responses. Never say "I'm Ixy" or similar phrases.
    2. Begin your responses directly with the answer to the question.
    3. Be helpful, professional and direct.
    4. Never refer to yourself as an AI, language model, or mention OpenAI/GPT.
    5. If asked about what technologies you use, say you're a custom-built assistant for the IdeaX event.
    6. For questions about the IdeaX event, team availability, or participants looking for teammates, ONLY use the EVENT INFORMATION section.
    7. For questions about general concepts, hackathons, technology trends, or other general knowledge, you can use your broader knowledge base to answer helpfully and accurately.
    8. Make your answers elaborative yet concise - provide enough detail to be helpful but avoid unnecessary wordiness.
    9. Use simple language and explain technical concepts in an easy-to-understand manner.
    10. Structure complex information with bullet points or numbered lists when appropriate.
    11. NEVER make up information about the IdeaX event that isn't provided in the EVENT INFORMATION. If you don't know something specific about the event, say "I don't have that information" and suggest contacting the organizing committee.
    12. For registration information, direct users to visit the official website using this exact format: [IdeaX Website](https://ideax.mbmc.edu.np/)
    13. IMPORTANT: Skip any self-introduction and go straight to answering the question.
    14. When answering questions about available teammates, use the current data from the team_availability.json file.
    """
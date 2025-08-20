import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from datetime import datetime

class TeamAvailabilityModal(discord.ui.Modal, title='Team Availability Form'):
    def __init__(self):
        super().__init__()

    skills = discord.ui.TextInput(
        label='Your Skills',
        placeholder='e.g., Python, JavaScript, UI/UX Design, Project Management...',
        required=True,
        max_length=200
    )

    experience = discord.ui.TextInput(
        label='Experience Level',
        placeholder='e.g., Beginner, Intermediate, Advanced',
        required=True,
        max_length=50
    )

    looking_for = discord.ui.TextInput(
        label='Looking For',
        placeholder='e.g., Frontend Developer, Backend Developer, Designer...',
        required=False,
        max_length=200
    )

    additional_info = discord.ui.TextInput(
        label='Additional Information',
        placeholder='Any other details about yourself or what you want to work on...',
        style=discord.TextStyle.paragraph,
        required=False,
        max_length=500
    )

    async def on_submit(self, interaction: discord.Interaction):
        # Get the cog instance to access save_availability method
        cog = interaction.client.get_cog('TeamPairing')
        if cog:
            await cog.save_availability(interaction, self)

class MembersPaginator(discord.ui.View):
    def __init__(self, embeds: list[discord.Embed], owner_id: int, timeout: float = 300):
        super().__init__(timeout=timeout)
        self.embeds = embeds
        self.index = 0
        self.owner_id = owner_id
        self._update_states()

    def _update_states(self):
        first_last = self.index == 0
        last_last = self.index >= len(self.embeds) - 1
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                if child.custom_id == "first":
                    child.disabled = first_last
                elif child.custom_id == "prev":
                    child.disabled = first_last
                elif child.custom_id == "next":
                    child.disabled = last_last
                elif child.custom_id == "last":
                    child.disabled = last_last

    async def _check_owner(self, interaction: discord.Interaction) -> bool:
        # Ephemeral message is only visible to the requester, but keep a safety check.
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("Not your paginator.", ephemeral=True, delete_after=3)
            return False
        return True

    @discord.ui.button(label="First", style=discord.ButtonStyle.secondary, custom_id="first")
    async def first(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_owner(interaction):
            return
        self.index = 0
        self._update_states()
        await interaction.response.edit_message(embed=self.embeds[self.index], view=self)

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.secondary, custom_id="prev")
    async def prev(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_owner(interaction):
            return
        if self.index > 0:
            self.index -= 1
        self._update_states()
        await interaction.response.edit_message(embed=self.embeds[self.index], view=self)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.secondary, custom_id="next")
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_owner(interaction):
            return
        if self.index < len(self.embeds) - 1:
            self.index += 1
        self._update_states()
        await interaction.response.edit_message(embed=self.embeds[self.index], view=self)

    @discord.ui.button(label="Last", style=discord.ButtonStyle.secondary, custom_id="last")
    async def last(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_owner(interaction):
            return
        self.index = len(self.embeds) - 1
        self._update_states()
        await interaction.response.edit_message(embed=self.embeds[self.index], view=self)

class TeamPairing(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_file = 'bot_memory/team_availability.json'
        self.ensure_data_file()

    def ensure_data_file(self):
        """Ensure the data file exists"""
        os.makedirs('bot_memory', exist_ok=True)
        if not os.path.exists(self.data_file):
            with open(self.data_file, 'w') as f:
                json.dump([], f)

    def load_data(self):
        """Load availability data from JSON file"""
        try:
            with open(self.data_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def save_data(self, data):
        """Save availability data to JSON file"""
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=2)

    def create_teammate_notification_embed(self, requester_name, requester_data, requester_mention, is_new_user=False):
        """Create a standardized embed for teammate notifications"""
        if is_new_user:
            title = "🤝 Someone New is Looking for Teammates!"
            description = f"**{requester_name}** just joined the teammate pool and is looking for teammates!"
        else:
            title = "🤝 Someone is Looking for Teammates!"
            description = f"**{requester_name}** is looking for teammates for the hackathon!"
        
        embed = discord.Embed(
            title=title,
            description=description,
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="Their Profile",
            value=f"**Skills:** {requester_data['skills']}\n"
                  f"**Experience:** {requester_data['experience']}\n"
                  f"**Looking for:** {requester_data['looking_for']}",
            inline=False
        )

        if requester_data['additional_info'] != "None":
            embed.add_field(
                name="Additional Info",
                value=requester_data['additional_info'],
                inline=False
            )

        embed.add_field(
            name="Contact",
            value=f"Reach out to {requester_mention} in the server if you're interested!",
            inline=False
        )

        embed.set_footer(text="Good luck with your hackathon team formation! 🚀")
        return embed

    @app_commands.command(name="find-team", description="Team formation commands")
    @app_commands.describe(
        action="Choose what you want to do"
    )
    @app_commands.choices(action=[
        app_commands.Choice(name="Set Availability", value="set-availability"),
        app_commands.Choice(name="DM Your Details", value="find-teammates"),
        app_commands.Choice(name="View Status", value="view-status"),
        app_commands.Choice(name="Remove Availability", value="remove-availability"),
        app_commands.Choice(name="View Available Members", value="view-all-members")
    ])
    async def find_team(self, interaction: discord.Interaction, action: str):
        if action == "set-availability":
            await self.set_availability_action(interaction)
        elif action == "find-teammates":
            await self.find_teammates_action(interaction)
        elif action == "view-status":
            await self.team_status_action(interaction)
        elif action == "remove-availability":
            await self.remove_availability_action(interaction)
        elif action == "view-all-members":
            await self.view_all_members_action(interaction)

    async def set_availability_action(self, interaction: discord.Interaction):
        modal = TeamAvailabilityModal()
        await interaction.response.send_modal(modal)

    async def save_availability(self, interaction: discord.Interaction, modal: TeamAvailabilityModal):
        """Save user availability data"""
        user_data = {
            "user_id": interaction.user.id,
            "username": interaction.user.display_name,
            "skills": modal.skills.value,
            "experience": modal.experience.value,
            "looking_for": modal.looking_for.value or "Any role",
            "additional_info": modal.additional_info.value or "None",
            "timestamp": datetime.now().isoformat(),
            "active": True
        }

        data = self.load_data()
        
        # Get existing available members before updating
        existing_members = [entry for entry in data if entry['active'] and entry['user_id'] != interaction.user.id]
        
        # Remove existing entry for this user if it exists
        data = [entry for entry in data if entry['user_id'] != interaction.user.id]
        
        # Add new entry
        data.append(user_data)
        self.save_data(data)

        # Send DMs to all existing available members
        successful_dms = 0
        failed_dms = 0

        for member_data in existing_members:
            try:
                user = await self.bot.fetch_user(member_data['user_id'])
                embed = self.create_teammate_notification_embed(
                    interaction.user.display_name, 
                    user_data,
                    interaction.user.mention,
                    is_new_user=True
                )
                await user.send(embed=embed)
                successful_dms += 1
                
            except discord.Forbidden:
                failed_dms += 1
            except Exception as e:
                failed_dms += 1
                print(f"Error sending DM to {member_data['username']}: {e}")

        embed = discord.Embed(
            title="✅ Availability Set!",
            description="Your team availability has been saved. Others can now find you when looking for teammates!",
            color=discord.Color.green()
        )
        embed.add_field(name="Your Profile", 
                       value=f"**Skills:** {user_data['skills']}\n"
                             f"**Experience:** {user_data['experience']}\n"
                             f"**Looking for:** {user_data['looking_for']}")
        
        if user_data['additional_info'] != "None":
            embed.add_field(name="Additional Info", value=user_data['additional_info'], inline=False)
        
        if existing_members:
            embed.add_field(
                name="Notifications Sent",
                value=f"Notified {successful_dms} existing teammates about your availability!",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def find_teammates_action(self, interaction: discord.Interaction):
        data = self.load_data()
        available_members = [entry for entry in data if entry['active'] and entry['user_id'] != interaction.user.id]

        if not available_members:
            await interaction.response.send_message("❌ No teammates are currently available!", ephemeral=True)
            return

        # Create requester profile
        requester_data = next((entry for entry in data if entry['user_id'] == interaction.user.id), None)
        
        if not requester_data:
            await interaction.response.send_message("❌ Please set your availability first using `/find-team set-availability`!", ephemeral=True)
            return

        # Send DMs to all available members
        successful_dms = 0
        failed_dms = 0

        for member_data in available_members:
            try:
                user = await self.bot.fetch_user(member_data['user_id'])
                embed = self.create_teammate_notification_embed(
                    interaction.user.display_name, 
                    requester_data,
                    interaction.user.mention,
                    is_new_user=False
                )
                await user.send(embed=embed)
                successful_dms += 1
                
            except discord.Forbidden:
                failed_dms += 1
            except Exception as e:
                failed_dms += 1
                print(f"Error sending DM to {member_data['username']}: {e}")

        # Send confirmation to requester
        embed = discord.Embed(
            title="📤 Teammate Search Sent!",
            description=f"Your teammate request has been sent to {successful_dms} available members.",
            color=discord.Color.green()
        )
        
        if failed_dms > 0:
            embed.add_field(
                name="Note",
                value=f"Could not send DMs to {failed_dms} members (they may have DMs disabled).",
                inline=False
            )

        embed.add_field(
            name="Next Steps",
            value="Wait for interested members to contact you in the server, or reach out to them directly!",
            inline=False
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def team_status_action(self, interaction: discord.Interaction):
        data = self.load_data()
        user_data = next((entry for entry in data if entry['user_id'] == interaction.user.id), None)

        if not user_data:
            await interaction.response.send_message("❌ You haven't set your availability yet! Use `/find-team set-availability` to get started.", ephemeral=True)
            return

        embed = discord.Embed(
            title="📋 Your Team Availability Status",
            color=discord.Color.blue()
        )
        
        embed.add_field(name="Skills", value=user_data['skills'], inline=False)
        embed.add_field(name="Experience", value=user_data['experience'], inline=True)
        embed.add_field(name="Looking For", value=user_data['looking_for'], inline=False)
        
        if user_data['additional_info'] != "None":
            embed.add_field(name="Additional Info", value=user_data['additional_info'], inline=False)
        
        embed.add_field(name="Status", value="🟢 Active" if user_data['active'] else "🔴 Inactive", inline=True)
        embed.set_footer(text=f"Last updated: {user_data['timestamp'][:19].replace('T', ' ')}")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def remove_availability_action(self, interaction: discord.Interaction):
        data = self.load_data()
        original_length = len(data)
        
        # Remove user's entry
        data = [entry for entry in data if entry['user_id'] != interaction.user.id]
        
        if len(data) == original_length:
            await interaction.response.send_message("❌ You weren't in the teammate pool!", ephemeral=True)
            return
        
        self.save_data(data)
        
        embed = discord.Embed(
            title="✅ Removed from Teammate Pool",
            description="You've been removed from the teammate availability list.",
            color=discord.Color.orange()
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def view_all_members_action(self, interaction: discord.Interaction):
        data = self.load_data()
        # Exclude requester to mirror existing behavior in find_teammates_action
        available_members = [e for e in data if e.get('active') and e.get('user_id') != interaction.user.id]

        if not available_members:
            embed = discord.Embed(
                title="👥 Available Team Members",
                description="❌ No members are currently available for team formation.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Chunk members into pages to respect embed field limits
        page_size = 10  # safe below the 25-field limit
        pages = [available_members[i:i + page_size] for i in range(0, len(available_members), page_size)]
        embeds = []

        total = len(available_members)
        for page_index, members in enumerate(pages, start=1):
            embed = discord.Embed(
                title="👥 Available Team Members",
                description=f"Page {page_index}/{len(pages)} • Showing {len(members)} of {total} members",
                color=discord.Color.blue()
            )

            base_index = (page_index - 1) * page_size
            for i, member in enumerate(members, start=1):
                # Build member info with safe defaults and truncation
                additional = member.get('additional_info', 'None') or 'None'
                if additional != "None" and len(additional) > 150:
                    additional = additional[:147] + "..."

                lines = [
                    f"**Skills:** {member.get('skills', 'N/A')}",
                    f"**Experience:** {member.get('experience', 'N/A')}",
                    f"**Looking for:** {member.get('looking_for', 'Any role')}",
                ]
                if additional != "None":
                    lines.append(f"**Info:** {additional}")
                lines.append(f"**Contact:** <@{member.get('user_id')}>")

                embed.add_field(
                    name=f"{base_index + i}. {member.get('username', 'Unknown')}",
                    value="\n".join(lines),
                    inline=False
                )

            embeds.append(embed)

        # Always attach paginator view, even if there's only one page (buttons will be disabled)
        view = MembersPaginator(embeds, interaction.user.id)
        await interaction.response.send_message(embed=embeds[0], view=view, ephemeral=True)

async def setup(bot):
    await bot.add_cog(TeamPairing(bot))
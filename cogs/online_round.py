import discord
from discord.ext import commands
from discord import app_commands
from config import EMBED_THUMBNAIL
import json
import os
import io

class OnlineRoundCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.teams = {}  # {team_name: [member_ids]}
        self.pitch_queue = []  # [team_names] in order
        self.current_presenting_team = None
        self.presenter_role_id = None
        self.pitching_active = False
        self.pitching_stage_channel_id = None  # Voice channel for presenting team
        self.waiting_room_channel_id = None    # Voice channel for waiting teams
        
        # Make path absolute based on the project directory
        project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_file = os.path.join(project_dir, "bot_memory", "online_round_data.json")
        
        # Ensure bot_memory directory exists
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        self.load_data()

    def save_data(self):
        """Save teams and queue data to file"""
        data = {
            "teams": self.teams,
            "pitch_queue": self.pitch_queue,
            "current_presenting_team": self.current_presenting_team,
            "presenter_role_id": self.presenter_role_id,
            "pitching_active": self.pitching_active,
            "pitching_stage_channel_id": self.pitching_stage_channel_id,
            "waiting_room_channel_id": self.waiting_room_channel_id,
            "last_updated": int(discord.utils.utcnow().timestamp())  # Track when data was last saved
        }
        try:
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving online round data: {e}")

    def load_data(self):
        """Load teams and queue data from file"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.teams = data.get("teams", {})
                    self.pitch_queue = data.get("pitch_queue", [])
                    self.current_presenting_team = data.get("current_presenting_team")
                    self.presenter_role_id = data.get("presenter_role_id")
                    self.pitching_active = data.get("pitching_active", False)
                    self.pitching_stage_channel_id = data.get("pitching_stage_channel_id")
                    self.waiting_room_channel_id = data.get("waiting_room_channel_id")
                    
                    # Log successful load with timestamp if available
                    last_updated = data.get("last_updated")
                    if last_updated:
                        print(f"Online round data loaded from {discord.utils.format_dt(discord.utils.utcnow().replace(timestamp=last_updated))}")
                    
                    # Validate loaded data
                    self._validate_loaded_data()
            except Exception as e:
                print(f"Error loading online round data: {e}")
                # Reset to defaults if loading fails
                self._reset_to_defaults()

    def _validate_loaded_data(self):
        """Validate and clean up loaded data"""
        # Ensure teams is a dict with list values
        if not isinstance(self.teams, dict):
            self.teams = {}
        else:
            for team_name, members in list(self.teams.items()):
                if not isinstance(members, list):
                    self.teams[team_name] = []
        
        # Ensure pitch_queue is a list
        if not isinstance(self.pitch_queue, list):
            self.pitch_queue = []
        
        # Remove teams from queue that no longer exist
        self.pitch_queue = [team for team in self.pitch_queue if team in self.teams]
        
        # Reset current presenting team if it's not in teams
        if self.current_presenting_team and self.current_presenting_team not in self.teams:
            self.current_presenting_team = None
        
        # Reset pitching_active if no current team or queue
        if self.pitching_active and not self.current_presenting_team and not self.pitch_queue:
            self.pitching_active = False

    def _reset_to_defaults(self):
        """Reset all data to default values"""
        self.teams = {}
        self.pitch_queue = []
        self.current_presenting_team = None
        self.presenter_role_id = None
        self.pitching_active = False
        self.pitching_stage_channel_id = None
        self.waiting_room_channel_id = None

    @commands.hybrid_group(name="online", description="Online round management commands.")
    async def online(self, ctx):
        """Online round management commands."""
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(
                title="📊 Online Round Commands",
                description="Use a subcommand to manage the online round system.",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="Setup Commands",
                value="`setup_role`, `setup_channels`, `quick_setup_channels`",
                inline=False
            )
            embed.add_field(
                name="Team Management",
                value="`register_team`, `add_member`, `remove_member`, `delete_team`, `list_teams`",
                inline=False
            )
            embed.add_field(
                name="Pitching Control",
                value="`set_queue`, `start`, `next`, `stop`, `status`",
                inline=False
            )
            embed.add_field(
                name="Data Management",
                value="`backup`, `clear_all`",
                inline=False
            )
            embed.set_thumbnail(url=EMBED_THUMBNAIL)
            await ctx.send(embed=embed)

    @online.command(name="setup_role", description="Set up the presenter role for the pitching session.")
    async def setup_pitching(self, ctx, presenter_role: discord.Role):
        interaction = ctx.interaction if hasattr(ctx, 'interaction') else ctx
        if not await self.check_permissions(interaction, "manage_roles"):
            return
        
        self.presenter_role_id = presenter_role.id
        self.save_data()
        
        embed = discord.Embed(
            title="🎯 Pitching Setup Complete",
            description=f"Presenter role set to: {presenter_role.mention}",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=EMBED_THUMBNAIL)
        await ctx.send(embed=embed)

    @online.command(name="register_team", description="Register a new team for the hackathon.")
    async def register_team(self, ctx, team_name: str, member1: discord.Member = None, member2: discord.Member = None, member3: discord.Member = None, member4: discord.Member = None, member5: discord.Member = None):
        interaction = ctx.interaction if hasattr(ctx, 'interaction') else ctx
        if not await self.check_permissions(interaction, "manage_roles"):
            return
        
        if team_name in self.teams:
            embed = discord.Embed(
                title="❌ Team Already Exists",
                description=f"Team '{team_name}' is already registered.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Collect provided members
        members = [member for member in [member1, member2, member3, member4, member5] if member is not None]
        member_ids = [member.id for member in members]
        self.teams[team_name] = member_ids
        self.save_data()
        
        # Create response embed
        embed = discord.Embed(
            title="✅ Team Registered",
            description=f"Team '{team_name}' has been registered successfully!",
            color=discord.Color.green()
        )
        
        if members:
            member_mentions = [member.mention for member in members]
            embed.add_field(
                name="Team Members",
                value="\n".join(member_mentions),
                inline=False
            )
            embed.add_field(
                name="Members Added",
                value=f"{len(members)} member(s) added to the team.",
                inline=False
            )
        else:
            embed.add_field(
                name="Next Step",
                value="Use `online add_member` to add members to this team.",
                inline=False
            )
        
        embed.set_thumbnail(url=EMBED_THUMBNAIL)
        await ctx.send(embed=embed)

    @online.command(name="add_member", description="Add a member to a team.")
    async def add_member(self, ctx, member: discord.Member, *, team_name: str):
        interaction = ctx.interaction if hasattr(ctx, 'interaction') else ctx
        if not await self.check_permissions(interaction, "manage_roles"):
            return
        
        if team_name not in self.teams:
            embed = discord.Embed(
                title="❌ Team Not Found",
                description=f"Team '{team_name}' is not registered. Use `online register_team` first.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        if member.id in self.teams[team_name]:
            embed = discord.Embed(
                title="❌ Member Already in Team",
                description=f"{member.mention} is already in team '{team_name}'.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        self.teams[team_name].append(member.id)
        self.save_data()
        
        embed = discord.Embed(
            title="✅ Member Added",
            description=f"{member.mention} has been added to team '{team_name}'.",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=EMBED_THUMBNAIL)
        await ctx.send(embed=embed)

    @online.command(name="remove_member", description="Remove a member from a team.")
    async def remove_member(self, ctx, member: discord.Member, *, team_name: str):
        interaction = ctx.interaction if hasattr(ctx, 'interaction') else ctx
        if not await self.check_permissions(interaction, "manage_roles"):
            return
        
        if team_name not in self.teams:
            embed = discord.Embed(
                title="❌ Team Not Found",
                description=f"Team '{team_name}' is not registered.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        if member.id not in self.teams[team_name]:
            embed = discord.Embed(
                title="❌ Member Not in Team",
                description=f"{member.mention} is not in team '{team_name}'.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        self.teams[team_name].remove(member.id)
        self.save_data()
        
        embed = discord.Embed(
            title="✅ Member Removed",
            description=f"{member.mention} has been removed from team '{team_name}'.",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=EMBED_THUMBNAIL)
        await ctx.send(embed=embed)

    @online.command(name="list_teams", description="List all registered teams and their members.")
    async def list_teams(self, ctx):
        interaction = ctx.interaction if hasattr(ctx, 'interaction') else ctx
        if not await self.check_permissions(interaction, "manage_roles"):
            return
        
        if not self.teams:
            embed = discord.Embed(
                title="📋 No Teams Registered",
                description="No teams have been registered yet.",
                color=discord.Color.blue()
            )
            await ctx.send(embed=embed)
            return
        
        embed = discord.Embed(
            title="📋 Registered Teams",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=EMBED_THUMBNAIL)
        
        for team_name, member_ids in self.teams.items():
            members = []
            for member_id in member_ids:
                member = ctx.guild.get_member(member_id)
                if member:
                    members.append(member.mention)
                else:
                    members.append(f"<@{member_id}> (Not found)")
            
            member_list = "\n".join(members) if members else "No members"
            embed.add_field(name=f"🏆 {team_name}", value=member_list, inline=False)
        
        await ctx.send(embed=embed)

    @online.command(name="set_queue", description="Set the order of teams for pitching.")
    async def set_pitch_queue(self, ctx, *, team_order: str):
        interaction = ctx.interaction if hasattr(ctx, 'interaction') else ctx
        if not await self.check_permissions(interaction, "manage_roles"):
            return
        
        teams = [team.strip() for team in team_order.split(',')]
        invalid_teams = [team for team in teams if team not in self.teams]
        
        if invalid_teams:
            embed = discord.Embed(
                title="❌ Invalid Teams",
                description=f"The following teams are not registered: {', '.join(invalid_teams)}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        self.pitch_queue = teams
        self.save_data()
        
        queue_list = "\n".join(f"{i+1}. {team}" for i, team in enumerate(teams))
        embed = discord.Embed(
            title="✅ Pitch Queue Set",
            description=f"Pitching order:\n{queue_list}",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=EMBED_THUMBNAIL)
        await ctx.send(embed=embed)

    @online.command(name="setup_channels", description="Set up the pitching stage and waiting room channels.")
    async def setup_channels(self, ctx, pitching_stage: discord.VoiceChannel, waiting_room: discord.VoiceChannel):
        interaction = ctx.interaction if hasattr(ctx, 'interaction') else ctx
        if not await self.check_permissions(interaction, "manage_channels"):
            return
        
        self.pitching_stage_channel_id = pitching_stage.id
        self.waiting_room_channel_id = waiting_room.id
        self.save_data()
        
        embed = discord.Embed(
            title="🔊 Channels Setup Complete",
            description=f"**Pitching Stage:** {pitching_stage.mention}\n**Waiting Room:** {waiting_room.mention}",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=EMBED_THUMBNAIL)
        await ctx.send(embed=embed)

    @online.command(name="quick_setup_channels", description="Quick setup with predefined channels for this server.")
    async def quick_setup_channels(self, ctx):
        interaction = ctx.interaction if hasattr(ctx, 'interaction') else ctx
        if not await self.check_permissions(interaction, "manage_channels"):
            return
        
        # Predefined channel IDs for this server
        pitching_stage_id = 1426397296609853481
        waiting_room_id = 1426397347989946398
        
        # Verify channels exist
        pitching_stage = ctx.guild.get_channel(pitching_stage_id)
        waiting_room = ctx.guild.get_channel(waiting_room_id)
        
        if not pitching_stage:
            embed = discord.Embed(
                title="❌ Pitching Stage Not Found",
                description=f"Channel with ID {pitching_stage_id} not found in this server.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        if not waiting_room:
            embed = discord.Embed(
                title="❌ Waiting Room Not Found", 
                description=f"Channel with ID {waiting_room_id} not found in this server.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Set the channels
        self.pitching_stage_channel_id = pitching_stage_id
        self.waiting_room_channel_id = waiting_room_id
        self.save_data()
        
        embed = discord.Embed(
            title="🔊 Quick Channels Setup Complete",
            description=f"**Pitching Stage:** {pitching_stage.mention}\n**Waiting Room:** {waiting_room.mention}",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=EMBED_THUMBNAIL)
        await ctx.send(embed=embed)

    @online.command(name="start", description="Start the pitching session.")
    async def start_pitching(self, ctx):
        interaction = ctx.interaction if hasattr(ctx, 'interaction') else ctx
        if not await self.check_permissions(interaction, "manage_roles"):
            return
        
        if not self.presenter_role_id:
            embed = discord.Embed(
                title="❌ Setup Required",
                description="Please set up the presenter role first using `online setup_role`.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        if not self.pitch_queue:
            embed = discord.Embed(
                title="❌ No Queue Set",
                description="Please set the pitch queue first using `online set_queue`.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Move all team members to waiting room before starting
        if self.waiting_room_channel_id:
            waiting_room = ctx.guild.get_channel(self.waiting_room_channel_id)
            if waiting_room:
                for team_name, member_ids in self.teams.items():
                    for member_id in member_ids:
                        member = ctx.guild.get_member(member_id)
                        if member and member.voice:
                            try:
                                await member.move_to(waiting_room)
                            except discord.HTTPException:
                                pass
        
        self.pitching_active = True
        next_team, dm_failures = await self.advance_to_next_team(ctx.guild)
        self.save_data()
        
        embed = discord.Embed(
            title="🎯 Pitching Session Started",
            description=f"First team: **{self.current_presenting_team}**",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=EMBED_THUMBNAIL)
        
        # Add DM failure warning if any
        if dm_failures:
            failure_list = "\n".join([f"• {member.mention}" for member in dm_failures])
            embed.add_field(
                name="⚠️ DM Notifications Failed",
                value=f"Could not send DM to:\n{failure_list}",
                inline=False
            )
        
        await ctx.send(embed=embed)

    @online.command(name="next", description="Advance to the next team in the queue.")
    async def next_team(self, ctx):
        interaction = ctx.interaction if hasattr(ctx, 'interaction') else ctx
        if not await self.check_permissions(interaction, "manage_roles"):
            return
        
        if not self.pitching_active:
            embed = discord.Embed(
                title="❌ Pitching Not Active",
                description="Start the pitching session first using `online start`.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        next_team, dm_failures = await self.advance_to_next_team(ctx.guild)
        self.save_data()
        
        if next_team:
            embed = discord.Embed(
                title="➡️ Next Team",
                description=f"Now presenting: **{next_team}**",
                color=discord.Color.blue()
            )
            
            # Add DM failure warning if any
            if dm_failures:
                failure_list = "\n".join([f"• {member.mention}" for member in dm_failures])
                embed.add_field(
                    name="⚠️ DM Notifications Failed",
                    value=f"Could not send DM to:\n{failure_list}",
                    inline=False
                )
        else:
            embed = discord.Embed(
                title="🏁 Pitching Complete",
                description="All teams have completed their presentations!",
                color=discord.Color.gold()
            )
            self.pitching_active = False
            self.save_data()
        
        embed.set_thumbnail(url=EMBED_THUMBNAIL)
        await ctx.send(embed=embed)

    async def advance_to_next_team(self, guild):
        """Remove presenter role from current team and give it to next team"""
        presenter_role = guild.get_role(self.presenter_role_id)
        if not presenter_role:
            return None, []
        
        # Get channel objects
        pitching_stage = guild.get_channel(self.pitching_stage_channel_id) if self.pitching_stage_channel_id else None
        waiting_room = guild.get_channel(self.waiting_room_channel_id) if self.waiting_room_channel_id else None
        
        # Remove role from current team and move to waiting room
        if self.current_presenting_team and self.current_presenting_team in self.teams:
            for member_id in self.teams[self.current_presenting_team]:
                member = guild.get_member(member_id)
                if member:
                    # Remove presenter role
                    if presenter_role in member.roles:
                        await member.remove_roles(presenter_role)
                    # Move to waiting room if they're in pitching stage
                    if waiting_room and member.voice and member.voice.channel == pitching_stage:
                        try:
                            await member.move_to(waiting_room)
                        except discord.HTTPException:
                            pass  # Member might have disconnected
        
        # Find next team
        if not self.pitch_queue:
            self.current_presenting_team = None
            return None, []
        
        # Get the first team in queue and remove it
        next_team = self.pitch_queue.pop(0)
        self.current_presenting_team = next_team
        
        # Track DM failures
        dm_failures = []
        
        # Give role to next team and move to pitching stage
        if next_team in self.teams:
            for member_id in self.teams[next_team]:
                member = guild.get_member(member_id)
                if member:
                    # Add presenter role
                    await member.add_roles(presenter_role)
                    # Move to pitching stage if they're in waiting room
                    if pitching_stage and member.voice and member.voice.channel == waiting_room:
                        try:
                            await member.move_to(pitching_stage)
                        except discord.HTTPException:
                            pass  # Member might have disconnected
                    
                    # Send DM notification
                    try:
                        dm_embed = discord.Embed(
                            title="🎯 Your Turn to Present!",
                            description=f"It's time for team **{next_team}** to present!",
                            color=discord.Color.green()
                        )
                        dm_embed.add_field(
                            name="What to do:",
                            value="Join the pitching stage voice channel and start your presentation.",
                            inline=False
                        )
                        if pitching_stage:
                            dm_embed.add_field(
                                name="Pitching Stage:",
                                value=f"#{pitching_stage.name}",
                                inline=False
                            )
                        dm_embed.set_thumbnail(url=EMBED_THUMBNAIL)
                        dm_embed.set_footer(text=f"Good luck from {guild.name}!")
                        
                        await member.send(embed=dm_embed)
                    except discord.HTTPException:
                        # User has DMs disabled, is a bot, or other error
                        dm_failures.append(member)
        
        return next_team, dm_failures

    @online.command(name="stop", description="Stop the current pitching session.")
    async def stop_pitching(self, ctx):
        interaction = ctx.interaction if hasattr(ctx, 'interaction') else ctx
        if not await self.check_permissions(interaction, "manage_roles"):
            return
        
        # Get channel objects
        pitching_stage = ctx.guild.get_channel(self.pitching_stage_channel_id) if self.pitching_stage_channel_id else None
        waiting_room = ctx.guild.get_channel(self.waiting_room_channel_id) if self.waiting_room_channel_id else None
        
        # Remove presenter role from current team and move to waiting room
        if self.current_presenting_team and self.presenter_role_id:
            presenter_role = ctx.guild.get_role(self.presenter_role_id)
            if presenter_role and self.current_presenting_team in self.teams:
                for member_id in self.teams[self.current_presenting_team]:
                    member = ctx.guild.get_member(member_id)
                    if member:
                        # Remove presenter role
                        if presenter_role in member.roles:
                            await member.remove_roles(presenter_role)
                        # Move to waiting room if they're in pitching stage
                        if waiting_room and member.voice and member.voice.channel == pitching_stage:
                            try:
                                await member.move_to(waiting_room)
                            except discord.HTTPException:
                                pass  # Member might have disconnected
        
        # Clear the queue and reset state
        self.pitch_queue.clear()
        self.pitching_active = False
        self.current_presenting_team = None
        self.save_data()
        
        embed = discord.Embed(
            title="⏹️ Pitching Session Stopped",
            description="The pitching session has been stopped, queue cleared, and all presenter roles have been removed.",
            color=discord.Color.red()
        )
        embed.set_thumbnail(url=EMBED_THUMBNAIL)
        await ctx.send(embed=embed)

    @online.command(name="status", description="Check the current pitching status.")
    async def pitching_status(self, ctx):
        embed = discord.Embed(
            title="📊 Pitching Status",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=EMBED_THUMBNAIL)
        
        if not self.pitching_active:
            embed.add_field(name="Status", value="❌ Not Active", inline=False)
        else:
            embed.add_field(name="Status", value="✅ Active", inline=False)
            if self.current_presenting_team:
                embed.add_field(name="Current Team", value=self.current_presenting_team, inline=False)
        
        if self.pitch_queue:
            queue_list = "\n".join(f"{i+1}. {team}" for i, team in enumerate(self.pitch_queue))
            embed.add_field(name="Remaining Queue", value=queue_list, inline=False)
        else:
            embed.add_field(name="Remaining Queue", value="Empty", inline=False)
        
        await ctx.send(embed=embed)

    @online.command(name="delete_team", description="Delete a team and remove all its members.")
    async def delete_team(self, ctx, *, team_name: str):
        interaction = ctx.interaction if hasattr(ctx, 'interaction') else ctx
        if not await self.check_permissions(interaction, "manage_roles"):
            return
        
        if team_name not in self.teams:
            embed = discord.Embed(
                title="❌ Team Not Found",
                description=f"Team '{team_name}' is not registered.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Remove from queue if present
        if team_name in self.pitch_queue:
            self.pitch_queue.remove(team_name)
        
        # Reset current presenting team if it's this team
        if self.current_presenting_team == team_name:
            self.current_presenting_team = None
        
        # Delete the team
        del self.teams[team_name]
        self.save_data()
        
        embed = discord.Embed(
            title="✅ Team Deleted",
            description=f"Team '{team_name}' has been deleted successfully!",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=EMBED_THUMBNAIL)
        await ctx.send(embed=embed)

    @online.command(name="clear_all", description="Clear all team data and reset the system.")
    async def clear_all_data(self, ctx):
        interaction = ctx.interaction if hasattr(ctx, 'interaction') else ctx
        if not await self.check_permissions(interaction, "administrator"):
            return
        
        # Create confirmation view
        view = discord.ui.View(timeout=30)
        
        async def confirm_callback(confirm_interaction):
            self._reset_to_defaults()
            self.save_data()
            
            embed = discord.Embed(
                title="✅ All Data Cleared",
                description="All teams, queues, and settings have been reset.",
                color=discord.Color.green()
            )
            embed.set_thumbnail(url=EMBED_THUMBNAIL)
            await confirm_interaction.response.edit_message(embed=embed, view=None)
        
        async def cancel_callback(cancel_interaction):
            embed = discord.Embed(
                title="❌ Operation Cancelled",
                description="No data was cleared.",
                color=discord.Color.red()
            )
            await cancel_interaction.response.edit_message(embed=embed, view=None)
        
        confirm_button = discord.ui.Button(label="Confirm Clear", style=discord.ButtonStyle.danger)
        cancel_button = discord.ui.Button(label="Cancel", style=discord.ButtonStyle.secondary)
        
        confirm_button.callback = confirm_callback
        cancel_button.callback = cancel_callback
        
        view.add_item(confirm_button)
        view.add_item(cancel_button)
        
        embed = discord.Embed(
            title="⚠️ Confirm Data Clear",
            description="This will delete ALL teams, queues, and settings. Are you sure?",
            color=discord.Color.orange()
        )
        await ctx.send(embed=embed, view=view)

    @online.command(name="backup", description="Get a backup of all current data.")
    async def backup_data(self, ctx):
        interaction = ctx.interaction if hasattr(ctx, 'interaction') else ctx
        if not await self.check_permissions(interaction, "manage_roles"):
            return
        
        # Create a comprehensive backup
        backup_data = {
            "teams": self.teams,
            "pitch_queue": self.pitch_queue,
            "current_presenting_team": self.current_presenting_team,
            "presenter_role_id": self.presenter_role_id,
            "pitching_active": self.pitching_active,
            "pitching_stage_channel_id": self.pitching_stage_channel_id,
            "waiting_room_channel_id": self.waiting_room_channel_id,
            "backup_timestamp": int(discord.utils.utcnow().timestamp())
        }
        
        # Convert to pretty JSON string
        json_str = json.dumps(backup_data, indent=2)
        
        # Create file and send
        file = discord.File(
            fp=io.StringIO(json_str),
            filename=f"online_round_backup_{int(discord.utils.utcnow().timestamp())}.json"
        )
        
        embed = discord.Embed(
            title="📁 Data Backup",
            description="Here's your backup file with all current data.",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=EMBED_THUMBNAIL)
        
        await ctx.send(embed=embed, file=file)

    async def check_permissions(self, ctx, permission: str):
        """Check if user has the required permission - updated for hybrid commands"""
        user = ctx.author if hasattr(ctx, 'author') else ctx.user
        guild = ctx.guild
        
        # Check for specific role ID: 1130051976189722680
        required_role_id = 1130051976189722680
        has_required_role = any(role.id == required_role_id for role in user.roles)
        
        if not has_required_role:
            embed = discord.Embed(
                title="❌ Insufficient Permissions",
                description="You need the required role to use online round commands.",
                color=discord.Color.red()
            )
            if hasattr(ctx, 'send'):
                await ctx.send(embed=embed, ephemeral=True)
            else:
                await ctx.response.send_message(embed=embed, ephemeral=True)
            return False
        
        # Also check the original permission if role check passes
        if not getattr(user.guild_permissions, permission, False):
            embed = discord.Embed(
                title="❌ Insufficient Permissions",
                description="That's for the moderator only twin.",
                color=discord.Color.red()
            )
            if hasattr(ctx, 'send'):
                await ctx.send(embed=embed, ephemeral=True)
            else:
                await ctx.response.send_message(embed=embed, ephemeral=True)
            return False
        return True

async def setup(bot):
    await bot.add_cog(OnlineRoundCog(bot))
"""
Online Round Management Cog for Discord Bot
Handles team registration, pitching queue management, and presentation flow
"""

import discord
from discord.ext import commands
from discord import app_commands
from config import EMBED_THUMBNAIL
import json
import os
import io
import asyncio
from typing import Optional, List, Dict, Tuple, Union
from datetime import datetime
from enum import Enum


class ErrorMessages(Enum):
    """Centralized error messages"""
    TEAM_EXISTS = "Team '{team_name}' is already registered."
    TEAM_NOT_FOUND = "Team '{team_name}' is not registered."
    MEMBER_IN_TEAM = "{member} is already in team '{team_name}'."
    MEMBER_NOT_IN_TEAM = "{member} is not in team '{team_name}'."
    NO_TEAMS = "No teams have been registered yet."
    NO_QUEUE = "Please set the pitch queue first using `online set_queue`."
    NO_PRESENTER_ROLE = "Please set up the presenter role first using `online setup_role`."
    NOT_ACTIVE = "Start the pitching session first using `online start`."
    INSUFFICIENT_PERMISSIONS = "You need the required role to use online round commands."
    CHANNEL_NOT_FOUND = "Channel with ID {channel_id} not found in this server."
    ROLE_NOT_FOUND = "Role with ID {role_id} not found in this server."
    DATA_SAVE_ERROR = "Failed to save data: {error}"
    DATA_LOAD_ERROR = "Failed to load data: {error}"


class SuccessMessages(Enum):
    """Centralized success messages"""
    TEAM_REGISTERED = "Team '{team_name}' has been registered successfully!"
    MEMBER_ADDED = "{member} has been added to team '{team_name}'."
    MEMBER_REMOVED = "{member} has been removed from team '{team_name}'."
    TEAM_DELETED = "Team '{team_name}' has been deleted successfully!"
    QUEUE_SET = "Pitching order has been set successfully."
    SESSION_STARTED = "Pitching session started with team: **{team_name}**"
    SESSION_STOPPED = "The pitching session has been stopped."
    ALL_CLEARED = "All teams, queues, and settings have been reset."
    CHANNELS_SETUP = "Channels setup completed successfully."
    ROLE_SETUP = "Presenter role setup completed successfully."


class DataValidator:
    """Validates and sanitizes data"""
    
    @staticmethod
    def validate_team_name(team_name: str) -> str:
        """Validate and sanitize team name"""
        if not team_name or not team_name.strip():
            raise ValueError("Team name cannot be empty")
        
        # Remove excessive whitespace and limit length
        sanitized = " ".join(team_name.strip().split())
        if len(sanitized) > 100:
            raise ValueError("Team name is too long (max 100 characters)")
        
        return sanitized
    
    @staticmethod
    def validate_teams_dict(teams: Dict) -> Dict:
        """Validate teams dictionary structure"""
        if not isinstance(teams, dict):
            return {}
        
        validated = {}
        for team_name, member_ids in teams.items():
            if isinstance(team_name, str) and isinstance(member_ids, list):
                # Ensure all member IDs are integers
                validated[team_name] = [
                    int(mid) for mid in member_ids 
                    if isinstance(mid, (int, str)) and str(mid).isdigit()
                ]
        
        return validated
    
    @staticmethod
    def validate_queue(queue: List, valid_teams: set) -> List:
        """Validate pitch queue"""
        if not isinstance(queue, list):
            return []
        
        # Only keep teams that exist in valid_teams
        return [team for team in queue if isinstance(team, str) and team in valid_teams]


class DataManager:
    """Handles all data persistence operations"""
    
    def __init__(self, data_file_path: str):
        self.data_file = data_file_path
        self._ensure_directory_exists()
    
    def _ensure_directory_exists(self):
        """Ensure the data directory exists"""
        try:
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        except Exception as e:
            print(f"Error creating data directory: {e}")
    
    def save(self, data: Dict) -> Tuple[bool, Optional[str]]:
        """
        Save data to file
        Returns: (success: bool, error_message: Optional[str])
        """
        try:
            # Add metadata
            data['last_updated'] = int(datetime.utcnow().timestamp())
            data['version'] = '2.0'
            
            # Write to temporary file first
            temp_file = f"{self.data_file}.tmp"
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # Atomic rename
            os.replace(temp_file, self.data_file)
            return True, None
            
        except Exception as e:
            error_msg = f"Error saving data: {type(e).__name__}: {str(e)}"
            print(error_msg)
            return False, error_msg
    
    def load(self) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Load data from file
        Returns: (data: Optional[Dict], error_message: Optional[str])
        """
        if not os.path.exists(self.data_file):
            return None, "No existing data file found"
        
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Log successful load
            last_updated = data.get('last_updated')
            if last_updated:
                timestamp_str = datetime.fromtimestamp(last_updated).strftime('%Y-%m-%d %H:%M:%S UTC')
                print(f"✓ Data loaded successfully (last updated: {timestamp_str})")
            
            return data, None
            
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON in data file: {e}"
            print(error_msg)
            return None, error_msg
        except Exception as e:
            error_msg = f"Error loading data: {type(e).__name__}: {str(e)}"
            print(error_msg)
            return None, error_msg
    
    def create_backup(self, data: Dict) -> str:
        """Create a JSON backup string"""
        backup_data = data.copy()
        backup_data['backup_timestamp'] = int(datetime.utcnow().timestamp())
        return json.dumps(backup_data, indent=2, ensure_ascii=False)


class EmbedFactory:
    """Factory for creating standardized embeds"""
    
    @staticmethod
    def create_error(title: str, description: str) -> discord.Embed:
        embed = discord.Embed(title=f"❌ {title}", description=description, color=discord.Color.red())
        embed.set_thumbnail(url=EMBED_THUMBNAIL)
        return embed
    
    @staticmethod
    def create_success(title: str, description: str) -> discord.Embed:
        embed = discord.Embed(title=f"✅ {title}", description=description, color=discord.Color.green())
        embed.set_thumbnail(url=EMBED_THUMBNAIL)
        return embed
    
    @staticmethod
    def create_info(title: str, description: str, color=discord.Color.blue()) -> discord.Embed:
        embed = discord.Embed(title=title, description=description, color=color)
        embed.set_thumbnail(url=EMBED_THUMBNAIL)
        return embed
    
    @staticmethod
    def create_warning(title: str, description: str) -> discord.Embed:
        embed = discord.Embed(title=f"⚠️ {title}", description=description, color=discord.Color.orange())
        embed.set_thumbnail(url=EMBED_THUMBNAIL)
        return embed


class OnlineRoundCog(commands.Cog):
    """Main cog for online round management"""
    
    # Configuration constants
    REQUIRED_ROLE_ID = 1130051976189722680
    DEFAULT_PITCHING_STAGE_ID = 1426397296609853481
    DEFAULT_WAITING_ROOM_ID = 1426397347989946398
    DEFAULT_PRESENTER_ROLE_ID = 1426401193110016152
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
        # Initialize data manager
        project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_file_path = os.path.join(project_dir, "bot_memory", "online_round_data.json")
        self.data_manager = DataManager(data_file_path)
        
        # Initialize state variables
        self._reset_state()
        
        # Load persisted data
        self._load_data()
        
        print(f"✓ OnlineRoundCog initialized: {len(self.teams)} teams, "
              f"{len(self.pitch_queue)} in queue, active: {self.pitching_active}")
    
    def _reset_state(self):
        """Reset all state variables to defaults"""
        self.teams: Dict[str, List[int]] = {}
        self.pitch_queue: List[str] = []
        self.current_presenting_team: Optional[str] = None
        self.presenter_role_id: Optional[int] = None
        self.pitching_active: bool = False
        self.pitching_stage_channel_id: Optional[int] = None
        self.waiting_room_channel_id: Optional[int] = None
    
    def _load_data(self):
        """Load data from persistence"""
        data, error = self.data_manager.load()
        
        if error:
            print(f"⚠ {error} - Starting with clean state")
            return
        
        if not data:
            return
        
        try:
            # Load and validate data
            self.teams = DataValidator.validate_teams_dict(data.get("teams", {}))
            self.presenter_role_id = data.get("presenter_role_id")
            self.pitching_stage_channel_id = data.get("pitching_stage_channel_id")
            self.waiting_room_channel_id = data.get("waiting_room_channel_id")
            self.pitching_active = bool(data.get("pitching_active", False))
            
            # Validate queue against loaded teams
            valid_teams = set(self.teams.keys())
            self.pitch_queue = DataValidator.validate_queue(
                data.get("pitch_queue", []), 
                valid_teams
            )
            
            # Validate current presenting team
            current_team = data.get("current_presenting_team")
            if current_team and current_team in self.teams:
                self.current_presenting_team = current_team
            else:
                self.current_presenting_team = None
            
            # Auto-fix inconsistent state
            if self.pitching_active and not self.current_presenting_team and not self.pitch_queue:
                self.pitching_active = False
                self._save_data()
                print("⚠ Auto-fixed: Disabled pitching_active due to empty queue")
            
        except Exception as e:
            print(f"⚠ Error processing loaded data: {e}")
            self._reset_state()
    
    def _save_data(self) -> bool:
        """Save current state to persistence"""
        data = {
            "teams": self.teams,
            "pitch_queue": self.pitch_queue,
            "current_presenting_team": self.current_presenting_team,
            "presenter_role_id": self.presenter_role_id,
            "pitching_active": self.pitching_active,
            "pitching_stage_channel_id": self.pitching_stage_channel_id,
            "waiting_room_channel_id": self.waiting_room_channel_id
        }
        
        success, error = self.data_manager.save(data)
        if not success:
            print(f"⚠ {error}")
        return success
    
    async def _check_permissions(self, ctx) -> bool:
        """Check if user has required permissions"""
        user = ctx.author if hasattr(ctx, 'author') else ctx.user
        
        has_required_role = any(role.id == self.REQUIRED_ROLE_ID for role in user.roles)
        
        if not has_required_role:
            embed = EmbedFactory.create_error(
                "Insufficient Permissions",
                ErrorMessages.INSUFFICIENT_PERMISSIONS.value
            )
            
            if hasattr(ctx, 'send'):
                await ctx.send(embed=embed, ephemeral=True)
            else:
                await ctx.response.send_message(embed=embed, ephemeral=True)
            
            return False
        
        return True
    
    async def _safe_move_member(self, member: discord.Member, channel: Union[discord.VoiceChannel, discord.StageChannel]) -> bool:
        """Safely move a member to a voice channel"""
        if not member.voice:
            return False
        
        try:
            await member.move_to(channel)
            return True
        except discord.HTTPException as e:
            print(f"⚠ Failed to move {member.name} to {channel.name}: {e}")
            return False
        except Exception as e:
            print(f"⚠ Unexpected error moving {member.name}: {e}")
            return False
    
    async def _safe_add_role(self, member: discord.Member, role: discord.Role) -> bool:
        """Safely add a role to a member"""
        try:
            await member.add_roles(role, reason="Online round presenter")
            return True
        except discord.HTTPException as e:
            print(f"⚠ Failed to add role to {member.name}: {e}")
            return False
        except Exception as e:
            print(f"⚠ Unexpected error adding role to {member.name}: {e}")
            return False
    
    async def _safe_remove_role(self, member: discord.Member, role: discord.Role) -> bool:
        """Safely remove a role from a member"""
        if role not in member.roles:
            return True
        
        try:
            await member.remove_roles(role, reason="Online round presenter finished")
            return True
        except discord.HTTPException as e:
            print(f"⚠ Failed to remove role from {member.name}: {e}")
            return False
        except Exception as e:
            print(f"⚠ Unexpected error removing role from {member.name}: {e}")
            return False
    
    async def _send_dm_notification(self, member: discord.Member, team_name: str, guild: discord.Guild, 
                                   pitching_stage: Optional[Union[discord.VoiceChannel, discord.StageChannel]]) -> bool:
        """Send DM notification to a member"""
        try:
            embed = discord.Embed(
                title="🎯 Your Turn to Present!",
                description=f"It's time for team **{team_name}** to present!",
                color=discord.Color.green()
            )
            embed.add_field(
                name="What to do:",
                value="Join the pitching stage voice channel and start your presentation.",
                inline=False
            )
            
            if pitching_stage:
                embed.add_field(
                    name="Pitching Stage:",
                    value=f"#{pitching_stage.name}",
                    inline=False
                )
            
            embed.set_thumbnail(url=EMBED_THUMBNAIL)
            embed.set_footer(text=f"Good luck from {guild.name}!")
            
            await member.send(embed=embed)
            return True
            
        except discord.Forbidden:
            # User has DMs disabled
            return False
        except discord.HTTPException as e:
            print(f"⚠ Failed to send DM to {member.name}: {e}")
            return False
        except Exception as e:
            print(f"⚠ Unexpected error sending DM to {member.name}: {e}")
            return False
    
    async def _move_team_to_channel(self, guild: discord.Guild, team_name: str, 
                                   target_channel: Union[discord.VoiceChannel, discord.StageChannel],
                                   source_channel: Optional[Union[discord.VoiceChannel, discord.StageChannel]] = None) -> int:
        """Move all team members to a channel. Returns count of members moved."""
        if team_name not in self.teams:
            return 0
        
        moved_count = 0
        for member_id in self.teams[team_name]:
            member = guild.get_member(member_id)
            if not member or not member.voice:
                continue
            
            # If source channel specified, only move if member is in that channel
            if source_channel and member.voice.channel and member.voice.channel.id != source_channel.id:
                continue
            
            if await self._safe_move_member(member, target_channel):
                moved_count += 1
        
        return moved_count
    
    async def _handle_team_role_changes(self, guild: discord.Guild, team_name: str, 
                                       add_role: bool, presenter_role: discord.Role) -> Tuple[int, int]:
        """Add or remove presenter role from team members. Returns (success_count, total_count)"""
        if team_name not in self.teams:
            return 0, 0
        
        success_count = 0
        total_count = 0
        
        for member_id in self.teams[team_name]:
            member = guild.get_member(member_id)
            if not member:
                continue
            
            total_count += 1
            if add_role:
                if await self._safe_add_role(member, presenter_role):
                    success_count += 1
            else:
                if await self._safe_remove_role(member, presenter_role):
                    success_count += 1
        
        return success_count, total_count
    
    async def _advance_to_next_team(self, guild: discord.Guild) -> Tuple[Optional[str], List[discord.Member]]:
        """
        Advance to the next team in queue
        Returns: (next_team_name, list of members who couldn't receive DM)
        """
        presenter_role = guild.get_role(self.presenter_role_id) if self.presenter_role_id else None
        if not presenter_role:
            print("⚠ Presenter role not found")
            return None, []
        
        # Get channel objects
        pitching_stage = guild.get_channel(self.pitching_stage_channel_id) if self.pitching_stage_channel_id else None
        waiting_room = guild.get_channel(self.waiting_room_channel_id) if self.waiting_room_channel_id else None
        
        # Handle current team cleanup
        if self.current_presenting_team and self.current_presenting_team in self.teams:
            # Remove presenter role
            await self._handle_team_role_changes(guild, self.current_presenting_team, False, presenter_role)
            
            # Move to waiting room if both channels exist
            if pitching_stage and waiting_room:
                await self._move_team_to_channel(guild, self.current_presenting_team, waiting_room, pitching_stage)
        
        # Check if queue is empty
        if not self.pitch_queue:
            self.current_presenting_team = None
            self._save_data()
            return None, []
        
        # Get next team
        next_team = self.pitch_queue.pop(0)
        self.current_presenting_team = next_team
        
        dm_failures = []
        
        # Setup next team
        if next_team in self.teams:
            # Add presenter role
            await self._handle_team_role_changes(guild, next_team, True, presenter_role)
            
            # Move to pitching stage if both channels exist
            if pitching_stage and waiting_room:
                await self._move_team_to_channel(guild, next_team, pitching_stage, waiting_room)
            
            # Send DM notifications
            for member_id in self.teams[next_team]:
                member = guild.get_member(member_id)
                if member:
                    dm_sent = await self._send_dm_notification(member, next_team, guild, pitching_stage)
                    if not dm_sent:
                        dm_failures.append(member)
        
        self._save_data()
        return next_team, dm_failures
    
    # ========== COMMAND GROUPS ==========
    
    @commands.hybrid_group(name="online", description="Online round management commands")
    async def online(self, ctx):
        """Online round management commands"""
        if ctx.invoked_subcommand is None:
            embed = EmbedFactory.create_info(
                "📊 Online Round Commands",
                "Use a subcommand to manage the online round system."
            )
            embed.add_field(
                name="Setup Commands",
                value="`setup_role`, `setup_channels`, `quick_setup`",
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
            await ctx.send(embed=embed)
    
    # ========== SETUP COMMANDS ==========
    
    @online.command(name="setup_role", description="Set up the presenter role for the pitching session")
    async def setup_role(self, ctx, presenter_role: discord.Role):
        """Set the presenter role"""
        await ctx.defer()
        
        if not await self._check_permissions(ctx):
            return
        
        self.presenter_role_id = presenter_role.id
        self._save_data()
        
        embed = EmbedFactory.create_success(
            "Presenter Role Setup",
            f"Presenter role set to: {presenter_role.mention}"
        )
        await ctx.send(embed=embed)
    
    @online.command(name="setup_channels", description="Set up the pitching stage and waiting room channels")
    async def setup_channels(self, ctx, 
                           pitching_stage: Union[discord.VoiceChannel, discord.StageChannel],
                           waiting_room: Union[discord.VoiceChannel, discord.StageChannel]):
        """Set up voice channels for pitching"""
        await ctx.defer()
        
        if not await self._check_permissions(ctx):
            return
        
        self.pitching_stage_channel_id = pitching_stage.id
        self.waiting_room_channel_id = waiting_room.id
        self._save_data()
        
        embed = EmbedFactory.create_success(
            "Channels Setup",
            f"**Pitching Stage:** {pitching_stage.mention}\n**Waiting Room:** {waiting_room.mention}"
        )
        await ctx.send(embed=embed)
    
    @online.command(name="quick_setup", description="Quick setup with predefined channels and role")
    async def quick_setup(self, ctx):
        """Quick setup using predefined IDs"""
        await ctx.defer()
        
        if not await self._check_permissions(ctx):
            return
        
        # Verify all resources exist
        pitching_stage = ctx.guild.get_channel(self.DEFAULT_PITCHING_STAGE_ID)
        waiting_room = ctx.guild.get_channel(self.DEFAULT_WAITING_ROOM_ID)
        presenter_role = ctx.guild.get_role(self.DEFAULT_PRESENTER_ROLE_ID)
        
        errors = []
        if not pitching_stage:
            errors.append(f"• Pitching stage (ID: {self.DEFAULT_PITCHING_STAGE_ID})")
        if not waiting_room:
            errors.append(f"• Waiting room (ID: {self.DEFAULT_WAITING_ROOM_ID})")
        if not presenter_role:
            errors.append(f"• Presenter role (ID: {self.DEFAULT_PRESENTER_ROLE_ID})")
        
        if errors:
            embed = EmbedFactory.create_error(
                "Quick Setup Failed",
                "The following resources were not found:\n" + "\n".join(errors)
            )
            await ctx.send(embed=embed)
            return
        
        # Apply configuration
        self.pitching_stage_channel_id = self.DEFAULT_PITCHING_STAGE_ID
        self.waiting_room_channel_id = self.DEFAULT_WAITING_ROOM_ID
        self.presenter_role_id = self.DEFAULT_PRESENTER_ROLE_ID
        self._save_data()
        
        embed = EmbedFactory.create_success(
            "Quick Setup Complete",
            f"**Pitching Stage:** {pitching_stage.mention}\n"
            f"**Waiting Room:** {waiting_room.mention}\n"
            f"**Presenter Role:** {presenter_role.mention}"
        )
        await ctx.send(embed=embed)
    
    # ========== TEAM MANAGEMENT COMMANDS ==========
    
    @online.command(name="register_team", description="Register a new team for the hackathon")
    async def register_team(self, ctx, team_name: str, 
                          member1: Optional[discord.Member] = None,
                          member2: Optional[discord.Member] = None,
                          member3: Optional[discord.Member] = None,
                          member4: Optional[discord.Member] = None,
                          member5: Optional[discord.Member] = None):
        """Register a new team"""
        await ctx.defer()
        
        if not await self._check_permissions(ctx):
            return
        
        # Validate team name
        try:
            team_name = DataValidator.validate_team_name(team_name)
        except ValueError as e:
            embed = EmbedFactory.create_error("Invalid Team Name", str(e))
            await ctx.send(embed=embed)
            return
        
        # Check if team already exists
        if team_name in self.teams:
            embed = EmbedFactory.create_error(
                "Team Already Exists",
                ErrorMessages.TEAM_EXISTS.value.format(team_name=team_name)
            )
            await ctx.send(embed=embed)
            return
        
        # Collect members
        members = [m for m in [member1, member2, member3, member4, member5] if m is not None]
        member_ids = [m.id for m in members]
        
        # Register team
        self.teams[team_name] = member_ids
        self._save_data()
        
        # Create response
        embed = EmbedFactory.create_success(
            "Team Registered",
            f"Team '{team_name}' has been registered successfully!"
        )
        
        if members:
            member_mentions = "\n".join([f"• {m.mention}" for m in members])
            embed.add_field(
                name=f"Team Members ({len(members)})",
                value=member_mentions,
                inline=False
            )
        else:
            embed.add_field(
                name="Next Step",
                value="Use `/online add_member` to add members to this team.",
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @online.command(name="add_member", description="Add a member to a team")
    async def add_member(self, ctx, member: discord.Member, *, team_name: str):
        """Add a member to an existing team"""
        await ctx.defer()
        
        if not await self._check_permissions(ctx):
            return
        
        # Validate team name
        try:
            team_name = DataValidator.validate_team_name(team_name)
        except ValueError as e:
            embed = EmbedFactory.create_error("Invalid Team Name", str(e))
            await ctx.send(embed=embed)
            return
        
        # Check if team exists
        if team_name not in self.teams:
            embed = EmbedFactory.create_error(
                "Team Not Found",
                ErrorMessages.TEAM_NOT_FOUND.value.format(team_name=team_name)
            )
            await ctx.send(embed=embed)
            return
        
        # Check if member already in team
        if member.id in self.teams[team_name]:
            embed = EmbedFactory.create_error(
                "Member Already in Team",
                ErrorMessages.MEMBER_IN_TEAM.value.format(member=member.mention, team_name=team_name)
            )
            await ctx.send(embed=embed)
            return
        
        # Add member
        self.teams[team_name].append(member.id)
        self._save_data()
        
        embed = EmbedFactory.create_success(
            "Member Added",
            SuccessMessages.MEMBER_ADDED.value.format(member=member.mention, team_name=team_name)
        )
        await ctx.send(embed=embed)
    
    @online.command(name="remove_member", description="Remove a member from a team")
    async def remove_member(self, ctx, member: discord.Member, *, team_name: str):
        """Remove a member from a team"""
        await ctx.defer()
        
        if not await self._check_permissions(ctx):
            return
        
        # Validate team name
        try:
            team_name = DataValidator.validate_team_name(team_name)
        except ValueError as e:
            embed = EmbedFactory.create_error("Invalid Team Name", str(e))
            await ctx.send(embed=embed)
            return
        
        # Check if team exists
        if team_name not in self.teams:
            embed = EmbedFactory.create_error(
                "Team Not Found",
                ErrorMessages.TEAM_NOT_FOUND.value.format(team_name=team_name)
            )
            await ctx.send(embed=embed)
            return
        
        # Check if member in team
        if member.id not in self.teams[team_name]:
            embed = EmbedFactory.create_error(
                "Member Not in Team",
                ErrorMessages.MEMBER_NOT_IN_TEAM.value.format(member=member.mention, team_name=team_name)
            )
            await ctx.send(embed=embed)
            return
        
        # Remove member
        self.teams[team_name].remove(member.id)
        self._save_data()
        
        embed = EmbedFactory.create_success(
            "Member Removed",
            SuccessMessages.MEMBER_REMOVED.value.format(member=member.mention, team_name=team_name)
        )
        await ctx.send(embed=embed)
    
    @online.command(name="delete_team", description="Delete a team and remove all its members")
    async def delete_team(self, ctx, *, team_name: str):
        """Delete a team completely"""
        await ctx.defer()
        
        if not await self._check_permissions(ctx):
            return
        
        # Validate team name
        try:
            team_name = DataValidator.validate_team_name(team_name)
        except ValueError as e:
            embed = EmbedFactory.create_error("Invalid Team Name", str(e))
            await ctx.send(embed=embed)
            return
        
        # Check if team exists
        if team_name not in self.teams:
            embed = EmbedFactory.create_error(
                "Team Not Found",
                ErrorMessages.TEAM_NOT_FOUND.value.format(team_name=team_name)
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
        self._save_data()
        
        embed = EmbedFactory.create_success(
            "Team Deleted",
            SuccessMessages.TEAM_DELETED.value.format(team_name=team_name)
        )
        await ctx.send(embed=embed)
    
    @online.command(name="list_teams", description="List all registered teams and their members")
    async def list_teams(self, ctx):
        """List all registered teams"""
        await ctx.defer()
        
        if not await self._check_permissions(ctx):
            return
        
        if not self.teams:
            embed = EmbedFactory.create_info(
                "📋 No Teams Registered",
                ErrorMessages.NO_TEAMS.value
            )
            await ctx.send(embed=embed)
            return
        
        embed = EmbedFactory.create_info(
            f"📋 Registered Teams ({len(self.teams)})",
            f"Total teams registered for the online round."
        )
        
        for team_name, member_ids in sorted(self.teams.items()):
            members = []
            for member_id in member_ids:
                member = ctx.guild.get_member(member_id)
                if member:
                    members.append(f"• {member.mention}")
                else:
                    members.append(f"• <@{member_id}> *(Left server)*")
            
            member_list = "\n".join(members) if members else "*No members*"
            
            # Add queue indicator
            queue_info = ""
            if team_name == self.current_presenting_team:
                queue_info = " 🎤"
            elif team_name in self.pitch_queue:
                position = self.pitch_queue.index(team_name) + 1
                queue_info = f" ⏳ (Queue #{position})"
            
            embed.add_field(
                name=f"🏆 {team_name}{queue_info}",
                value=member_list,
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    # ========== PITCHING CONTROL COMMANDS ==========
    
    @online.command(name="set_queue", description="Set the order of teams for pitching")
    async def set_queue(self, ctx, *, team_order: str):
        """Set the pitching order"""
        await ctx.defer()
        
        if not await self._check_permissions(ctx):
            return
        
        # Parse team names
        teams = [team.strip() for team in team_order.split(',') if team.strip()]
        
        if not teams:
            embed = EmbedFactory.create_error(
                "Invalid Input",
                "Please provide team names separated by commas."
            )
            await ctx.send(embed=embed)
            return
        
        # Validate all teams exist
        invalid_teams = [team for team in teams if team not in self.teams]
        
        if invalid_teams:
            embed = EmbedFactory.create_error(
                "Invalid Teams",
                f"The following teams are not registered:\n" + 
                "\n".join([f"• {team}" for team in invalid_teams])
            )
            await ctx.send(embed=embed)
            return
        
        # Check for duplicates
        duplicates = [team for team in teams if teams.count(team) > 1]
        if duplicates:
            unique_duplicates = list(set(duplicates))
            embed = EmbedFactory.create_error(
                "Duplicate Teams",
                f"The following teams appear multiple times:\n" + 
                "\n".join([f"• {team}" for team in unique_duplicates])
            )
            await ctx.send(embed=embed)
            return
        
        # Set the queue
        self.pitch_queue = teams
        self._save_data()
        
        queue_list = "\n".join([f"{i+1}. **{team}**" for i, team in enumerate(teams)])
        embed = EmbedFactory.create_success(
            "Pitch Queue Set",
            f"Pitching order ({len(teams)} teams):\n\n{queue_list}"
        )
        await ctx.send(embed=embed)
    
    @online.command(name="start", description="Start the pitching session")
    async def start_pitching(self, ctx):
        """Start the pitching session"""
        await ctx.defer()
        
        if not await self._check_permissions(ctx):
            return
        
        # Validation checks
        if not self.presenter_role_id:
            embed = EmbedFactory.create_error(
                "Setup Required",
                ErrorMessages.NO_PRESENTER_ROLE.value
            )
            await ctx.send(embed=embed)
            return
        
        if not self.pitch_queue:
            embed = EmbedFactory.create_error(
                "No Queue Set",
                ErrorMessages.NO_QUEUE.value
            )
            await ctx.send(embed=embed)
            return
        
        if self.pitching_active:
            embed = EmbedFactory.create_warning(
                "Already Active",
                f"Pitching session is already active.\nCurrent team: **{self.current_presenting_team}**"
            )
            await ctx.send(embed=embed)
            return
        
        # Move all team members to waiting room before starting
        waiting_room = ctx.guild.get_channel(self.waiting_room_channel_id) if self.waiting_room_channel_id else None
        
        if waiting_room:
            total_moved = 0
            for team_name in self.teams:
                moved = await self._move_team_to_channel(ctx.guild, team_name, waiting_room)
                total_moved += moved
            
            if total_moved > 0:
                print(f"✓ Moved {total_moved} members to waiting room")
        
        # Start the session
        self.pitching_active = True
        next_team, dm_failures = await self._advance_to_next_team(ctx.guild)
        
        if not next_team:
            self.pitching_active = False
            self._save_data()
            embed = EmbedFactory.create_error(
                "Start Failed",
                "Could not start pitching session. Queue may be empty."
            )
            await ctx.send(embed=embed)
            return
        
        embed = EmbedFactory.create_success(
            "Pitching Session Started",
            SuccessMessages.SESSION_STARTED.value.format(team_name=next_team)
        )
        
        # Add queue preview
        if self.pitch_queue:
            next_teams = self.pitch_queue[:3]
            preview = "\n".join([f"{i+1}. {team}" for i, team in enumerate(next_teams)])
            if len(self.pitch_queue) > 3:
                preview += f"\n... and {len(self.pitch_queue) - 3} more"
            embed.add_field(name="📋 Next Up", value=preview, inline=False)
        
        # Add DM failure warning if any
        if dm_failures:
            failure_list = "\n".join([f"• {member.mention}" for member in dm_failures])
            embed.add_field(
                name="⚠️ DM Notifications Failed",
                value=f"Could not send DM to:\n{failure_list}\nThey may have DMs disabled.",
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @online.command(name="next", description="Advance to the next team in the queue")
    async def next_team(self, ctx):
        """Move to the next team"""
        await ctx.defer()
        
        if not await self._check_permissions(ctx):
            return
        
        if not self.pitching_active:
            embed = EmbedFactory.create_error(
                "Pitching Not Active",
                ErrorMessages.NOT_ACTIVE.value
            )
            await ctx.send(embed=embed)
            return
        
        next_team, dm_failures = await self._advance_to_next_team(ctx.guild)
        
        if next_team:
            embed = EmbedFactory.create_info(
                "➡️ Next Team",
                f"Now presenting: **{next_team}**",
                color=discord.Color.blue()
            )
            
            # Add team members info
            if next_team in self.teams:
                members = []
                for member_id in self.teams[next_team]:
                    member = ctx.guild.get_member(member_id)
                    if member:
                        members.append(f"• {member.mention}")
                    else:
                        members.append(f"• <@{member_id}> *(Left server)*")
                
                if members:
                    embed.add_field(
                        name="👥 Team Members",
                        value="\n".join(members),
                        inline=False
                    )
            
            # Add queue preview
            if self.pitch_queue:
                next_teams = self.pitch_queue[:3]
                preview = "\n".join([f"{i+1}. {team}" for i, team in enumerate(next_teams)])
                if len(self.pitch_queue) > 3:
                    preview += f"\n... and {len(self.pitch_queue) - 3} more"
                embed.add_field(name="📋 Next Up", value=preview, inline=False)
            else:
                embed.add_field(
                    name="📋 Next Up", 
                    value="*This is the last team!*", 
                    inline=False
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
            # All teams finished
            embed = EmbedFactory.create_info(
                "🏁 Pitching Complete",
                "All teams have completed their presentations!",
                color=discord.Color.gold()
            )
            self.pitching_active = False
            self._save_data()
        
        await ctx.send(embed=embed)
    
    @online.command(name="stop", description="Stop the current pitching session")
    async def stop_pitching(self, ctx):
        """Stop the pitching session"""
        await ctx.defer()
        
        if not await self._check_permissions(ctx):
            return
        
        if not self.pitching_active and not self.current_presenting_team:
            embed = EmbedFactory.create_warning(
                "No Active Session",
                "There is no active pitching session to stop."
            )
            await ctx.send(embed=embed)
            return
        
        # Get channel objects
        pitching_stage = ctx.guild.get_channel(self.pitching_stage_channel_id) if self.pitching_stage_channel_id else None
        waiting_room = ctx.guild.get_channel(self.waiting_room_channel_id) if self.waiting_room_channel_id else None
        
        # Remove presenter role from current team and move to waiting room
        if self.current_presenting_team and self.presenter_role_id:
            presenter_role = ctx.guild.get_role(self.presenter_role_id)
            if presenter_role:
                await self._handle_team_role_changes(ctx.guild, self.current_presenting_team, False, presenter_role)
                
                if pitching_stage and waiting_room:
                    await self._move_team_to_channel(ctx.guild, self.current_presenting_team, waiting_room, pitching_stage)
        
        # Clear session data
        self.teams.clear()
        self.pitch_queue.clear()
        self.pitching_active = False
        self.current_presenting_team = None
        self._save_data()
        
        embed = EmbedFactory.create_info(
            "⏹️ Session Stopped",
            SuccessMessages.SESSION_STOPPED.value + "\n\nAll teams and queue have been cleared.\n\n"
            "**Preserved:** Channel and presenter role configuration.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
    
    @online.command(name="status", description="Check the current pitching status")
    async def status(self, ctx):
        """Display current status"""
        await ctx.defer()
        
        embed = EmbedFactory.create_info("📊 Pitching Status", "Current system status")
        
        # Session status
        if self.pitching_active:
            embed.add_field(name="Status", value="✅ **Active**", inline=True)
        else:
            embed.add_field(name="Status", value="❌ **Inactive**", inline=True)
        
        # Team count
        embed.add_field(name="Total Teams", value=str(len(self.teams)), inline=True)
        
        # Current team
        if self.current_presenting_team:
            embed.add_field(
                name="Current Team",
                value=f"🎤 **{self.current_presenting_team}**",
                inline=True
            )
        
        # Queue
        if self.pitch_queue:
            queue_preview = "\n".join([f"{i+1}. {team}" for i, team in enumerate(self.pitch_queue[:5])])
            if len(self.pitch_queue) > 5:
                queue_preview += f"\n... and {len(self.pitch_queue) - 5} more"
            embed.add_field(
                name=f"📋 Remaining Queue ({len(self.pitch_queue)})",
                value=queue_preview,
                inline=False
            )
        else:
            embed.add_field(name="📋 Queue", value="*Empty*", inline=False)
        
        # Configuration status
        config_items = []
        if self.presenter_role_id:
            role = ctx.guild.get_role(self.presenter_role_id)
            config_items.append(f"✅ Presenter Role: {role.mention if role else '*(Role deleted)*'}")
        else:
            config_items.append("❌ Presenter Role: *Not set*")
        
        if self.pitching_stage_channel_id:
            channel = ctx.guild.get_channel(self.pitching_stage_channel_id)
            config_items.append(f"✅ Pitching Stage: {channel.mention if channel else '*(Channel deleted)*'}")
        else:
            config_items.append("❌ Pitching Stage: *Not set*")
        
        if self.waiting_room_channel_id:
            channel = ctx.guild.get_channel(self.waiting_room_channel_id)
            config_items.append(f"✅ Waiting Room: {channel.mention if channel else '*(Channel deleted)*'}")
        else:
            config_items.append("❌ Waiting Room: *Not set*")
        
        embed.add_field(
            name="⚙️ Configuration",
            value="\n".join(config_items),
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    # ========== DATA MANAGEMENT COMMANDS ==========
    
    @online.command(name="backup", description="Get a backup of all current data")
    async def backup(self, ctx):
        """Create and send a data backup"""
        await ctx.defer()
        
        if not await self._check_permissions(ctx):
            return
        
        # Create backup data
        backup_data = {
            "teams": self.teams,
            "pitch_queue": self.pitch_queue,
            "current_presenting_team": self.current_presenting_team,
            "presenter_role_id": self.presenter_role_id,
            "pitching_active": self.pitching_active,
            "pitching_stage_channel_id": self.pitching_stage_channel_id,
            "waiting_room_channel_id": self.waiting_room_channel_id
        }
        
        json_str = self.data_manager.create_backup(backup_data)
        
        # Create file
        timestamp = int(datetime.utcnow().timestamp())
        filename = f"online_round_backup_{timestamp}.json"
        file = discord.File(fp=io.StringIO(json_str), filename=filename)
        
        embed = EmbedFactory.create_info(
            "📁 Data Backup",
            f"Backup created successfully!\n\n"
            f"**Teams:** {len(self.teams)}\n"
            f"**Queue Length:** {len(self.pitch_queue)}\n"
            f"**Active:** {'Yes' if self.pitching_active else 'No'}"
        )
        
        await ctx.send(embed=embed, file=file)
    
    @online.command(name="clear_all", description="Clear all team data and reset the system")
    async def clear_all(self, ctx):
        """Clear all data with confirmation"""
        await ctx.defer()
        
        if not await self._check_permissions(ctx):
            return
        
        # Create confirmation view
        class ConfirmView(discord.ui.View):
            def __init__(self, cog_instance, timeout=30):
                super().__init__(timeout=timeout)
                self.cog = cog_instance
                self.confirmed = False
            
            @discord.ui.button(label="Confirm Clear All", style=discord.ButtonStyle.danger)
            async def confirm_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                if interaction.user.id != ctx.author.id:
                    await interaction.response.send_message(
                        "❌ Only the command user can confirm this action.",
                        ephemeral=True
                    )
                    return
                
                self.confirmed = True
                self.cog._reset_state()
                self.cog._save_data()
                
                embed = EmbedFactory.create_success(
                    "All Data Cleared",
                    SuccessMessages.ALL_CLEARED.value
                )
                await interaction.response.edit_message(embed=embed, view=None)
                self.stop()
            
            @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
            async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                if interaction.user.id != ctx.author.id:
                    await interaction.response.send_message(
                        "❌ Only the command user can cancel this action.",
                        ephemeral=True
                    )
                    return
                
                embed = EmbedFactory.create_info(
                    "❌ Operation Cancelled",
                    "No data was cleared.",
                    color=discord.Color.red()
                )
                await interaction.response.edit_message(embed=embed, view=None)
                self.stop()
        
        view = ConfirmView(self)
        
        embed = EmbedFactory.create_warning(
            "Confirm Data Clear",
            "⚠️ **This action cannot be undone!**\n\n"
            f"This will permanently delete:\n"
            f"• All {len(self.teams)} registered teams\n"
            f"• The entire pitch queue\n"
            f"• All configuration settings\n\n"
            "Are you absolutely sure?"
        )
        
        await ctx.send(embed=embed, view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(OnlineRoundCog(bot))
import discord
from discord.ext import commands
import asyncio
import time
from collections import defaultdict, deque
import re
from datetime import timedelta
from config import EMBED_THUMBNAIL

class AntiSpam(commands.Cog):
    """Anti-spam and anti-mention moderation system."""
    
    def __init__(self, bot):
        self.bot = bot
        
        # Rate limiting - tracks messages per user
        self.user_message_times = defaultdict(deque)
        self.user_warnings = defaultdict(int)
        
        # Duplicate message detection
        self.user_recent_messages = defaultdict(deque)
        
        # Mention tracking
        self.user_mention_times = defaultdict(deque)
        
        # Track all user messages for bulk deletion
        self.user_messages = defaultdict(deque)
        
        # Cross-channel spam detection (for hacked accounts)
        self.user_channel_activity = defaultdict(lambda: defaultdict(deque))  # user_id -> channel_id -> timestamps
        self.user_global_messages = defaultdict(deque)  # Global message tracking across all channels
        
        # Configuration
        self.config = {
            'message_limit': 5,  # Max messages per time window
            'time_window': 10,   # Time window in seconds
            'duplicate_limit': 3,  # Max duplicate messages
            'mention_limit': 5,   # Max mentions per message
            'mass_mention_limit': 2,  # Max mentions per time window
            'mute_duration': 86400,  # Mute duration in seconds (1 day)
            'warning_threshold': 3,  # Warnings before action
            'cross_channel_limit': 3,  # Max channels user can post in during time window
            'global_message_limit': 8,  # Max messages across all channels in time window
            'cross_channel_time_window': 15,  # Time window for cross-channel detection
            'enabled': True
        }
        
        # Exempt roles and channels
        self.exempt_roles = {'Admin', 'Moderator', 'Staff'}
        self.exempt_channels = {1393576065427046621}  # Add channel IDs as needed
        self.exempt_users = set()     # Add user IDs to exempt
        self.exempt_role_ids = set()  # Add role IDs to exempt

    def is_exempt(self, member, channel):
        """Check if user or channel is exempt from anti-spam."""
        if not self.config['enabled']:
            return True
            
        # Check channel exemption
        if channel.id in self.exempt_channels:
            return True
            
        # Check user ID exemption
        if member.id in self.exempt_users:
            return True
            
        # Check role exemption (by name)
        user_roles = {role.name for role in member.roles}
        if user_roles.intersection(self.exempt_roles):
            return True
            
        # Check role exemption (by ID)
        user_role_ids = {role.id for role in member.roles}
        if user_role_ids.intersection(self.exempt_role_ids):
            return True
            
        return False

    def clean_old_entries(self, user_id, timestamp):
        """Clean old entries from tracking dictionaries."""
        time_window = self.config['time_window']
        cross_channel_window = self.config['cross_channel_time_window']
        
        # Clean message times
        while (self.user_message_times[user_id] and 
               timestamp - self.user_message_times[user_id][0] > time_window):
            self.user_message_times[user_id].popleft()
            
        # Clean mention times
        while (self.user_mention_times[user_id] and 
               timestamp - self.user_mention_times[user_id][0] > time_window):
            self.user_mention_times[user_id].popleft()
            
        # Clean recent messages (keep last 10)
        while len(self.user_recent_messages[user_id]) > 10:
            self.user_recent_messages[user_id].popleft()
            
        # Clean tracked messages (keep last 20 for potential bulk deletion)
        while len(self.user_messages[user_id]) > 20:
            self.user_messages[user_id].popleft()
            
        # Clean cross-channel activity
        for channel_id in list(self.user_channel_activity[user_id].keys()):
            while (self.user_channel_activity[user_id][channel_id] and 
                   timestamp - self.user_channel_activity[user_id][channel_id][0] > cross_channel_window):
                self.user_channel_activity[user_id][channel_id].popleft()
            # Remove empty channel entries
            if not self.user_channel_activity[user_id][channel_id]:
                del self.user_channel_activity[user_id][channel_id]
                
        # Clean global messages
        while (self.user_global_messages[user_id] and 
               timestamp - self.user_global_messages[user_id][0] > cross_channel_window):
            self.user_global_messages[user_id].popleft()

    async def delete_user_messages(self, user_id):
        """Delete all tracked messages from a user."""
        messages_to_delete = list(self.user_messages[user_id])
        deleted_count = 0
        
        for message in messages_to_delete:
            try:
                await message.delete()
                deleted_count += 1
            except (discord.NotFound, discord.Forbidden):
                pass  # Message already deleted or no permission
            except Exception as e:
                print(f"Error deleting message: {e}")
        
        # Clear the tracked messages for this user
        self.user_messages[user_id].clear()
        
        return deleted_count

    async def mute_user(self, member, reason):
        """Timeout a user using Discord's built-in timeout feature."""
        try:
            # Calculate timeout duration (Discord uses timedelta)
            timeout_duration = timedelta(seconds=self.config['mute_duration'])
            
            # Apply timeout
            await member.timeout(timeout_duration, reason=reason)
            
            print(f"Timed out {member.display_name} for {self.config['mute_duration']} seconds")
                
        except discord.Forbidden:
            print(f"Failed to timeout {member.display_name}: Missing permissions")
        except Exception as e:
            print(f"Error timing out {member.display_name}: {e}")

    # Modify warn_user to send ephemeral messages in the channel
    async def warn_user(self, message, reason):
        """Send a warning to the user."""
        try:
            embed = discord.Embed(
                title="⚠️ Moderation Warning",
                description=f"**Reason:** {reason}\n**Server:** {message.guild.name}",
                color=discord.Color.orange()
            )
            # Add thumbnail to all embeds
            embed.set_thumbnail(url=EMBED_THUMBNAIL)
            # Send ephemeral warning in the channel
            await message.channel.send(embed=embed)
        except discord.Forbidden:
            print("Failed to send ephemeral warning due to missing permissions.")

    @commands.Cog.listener()
    async def on_message(self, message):
        """Main anti-spam detection."""
        if message.author.bot:
            return
            
        if self.is_exempt(message.author, message.channel):
            return
            
        user_id = message.author.id
        timestamp = time.time()
        
        # Clean old entries
        self.clean_old_entries(user_id, timestamp)
        
        # Track this message for potential bulk deletion
        self.user_messages[user_id].append(message)
        
        # Track this message for rate limiting and duplicate detection
        self.user_message_times[user_id].append(timestamp)
        self.user_recent_messages[user_id].append(message.content.lower())
        
        # Track cross-channel activity for hacked account detection
        self.user_channel_activity[user_id][message.channel.id].append(timestamp)
        self.user_global_messages[user_id].append(timestamp)
        
        violations = []
        
        # Check message rate limiting
        if len(self.user_message_times[user_id]) > self.config['message_limit']:
            violations.append("sending messages too quickly")
            
        # Check for duplicate messages
        recent_content = list(self.user_recent_messages[user_id])
        if recent_content.count(message.content.lower()) >= self.config['duplicate_limit']:
            violations.append("sending duplicate messages")
            
        # Check mention limits
        total_mentions = len(message.mentions) + len(message.role_mentions)
        if "@everyone" in message.content:
            total_mentions += 1
        if "@here" in message.content:
            total_mentions += 1
            
        if total_mentions > self.config['mention_limit']:
            violations.append(f"mentioning too many users ({total_mentions} mentions)")
            
        # Track mentions for mass mention detection
        if total_mentions > 0:
            self.user_mention_times[user_id].append(timestamp)
            
        # Check mass mentions over time
        if len(self.user_mention_times[user_id]) > self.config['mass_mention_limit']:
            violations.append("mass mentioning users")
            
        # Check for excessive caps
        if len(message.content) > 10 and sum(1 for c in message.content if c.isupper()) / len(message.content) > 0.7:
            violations.append("excessive caps lock")
            
        # Check for excessive repetition of characters
        if re.search(r'(.)\1{5,}', message.content):
            violations.append("excessive character repetition")
            
        # Check for cross-channel spam (hacked account detection)
        active_channels = len(self.user_channel_activity[user_id])
        if active_channels > self.config['cross_channel_limit']:
            violations.append(f"posting in too many channels simultaneously ({active_channels} channels)")
            
        # Check global message rate (across all channels)
        if len(self.user_global_messages[user_id]) > self.config['global_message_limit']:
            violations.append(f"sending too many messages across server ({len(self.user_global_messages[user_id])} messages)")
        
        # Immediate timeout for suspected hacked accounts (cross-channel spam)
        if active_channels > self.config['cross_channel_limit'] or len(self.user_global_messages[user_id]) > self.config['global_message_limit']:
            # Skip warning system - immediate timeout for suspected hack
            deleted_count = await self.delete_user_messages(user_id)
            
            reason = f"Suspected compromised account: {', '.join(violations)}"
            await self.mute_user(message.author, reason)
            
            # Send urgent notification
            embed = discord.Embed(
                title="🚨 Suspected Compromised Account",
                description=f"{message.author.mention} has been immediately timed out\n**Reason:** {reason}\n**Messages deleted:** {deleted_count}\n**Alert:** This user may be compromised!",
                color=discord.Color.dark_red()
            )
            # Add thumbnail to all embeds
            embed.set_thumbnail(url=EMBED_THUMBNAIL)
            await message.channel.send(embed=embed)
            
            # Reset all tracking for this user
            self.user_warnings[user_id] = 0
            self.user_channel_activity[user_id].clear()
            self.user_global_messages[user_id].clear()
            return  # Skip normal warning system
            
        # Take action if violations found
        if violations:
            # Don't delete individual messages here - we'll bulk delete on timeout
            
            # Increment warnings
            self.user_warnings[user_id] += len(violations)
            
            # Determine action based on warning count
            if self.user_warnings[user_id] >= self.config['warning_threshold']:
                # Delete all tracked messages from this user
                deleted_count = await self.delete_user_messages(user_id)
                
                # Timeout user
                reason = f"Anti-spam: {', '.join(violations)}"
                await self.mute_user(message.author, reason)
                
                # Send timeout notification
                embed = discord.Embed(
                    title="⏰ User Timed Out",
                    description=f"{message.author.mention} has been timed out for {self.config['mute_duration']}s\n**Reason:** {reason}\n**Messages deleted:** {deleted_count}",
                    color=discord.Color.red()
                )
                # Add thumbnail to all embeds
                embed.set_thumbnail(url=EMBED_THUMBNAIL)
                await message.channel.send(embed=embed)
                
                # Reset warnings after timeout
                self.user_warnings[user_id] = 0
            else:
                # For warnings, still delete the current violating message
                try:
                    await message.delete()
                except discord.NotFound:
                    pass
                except discord.Forbidden:
                    pass
                
                # Send warning
                reason = f"Please stop {', '.join(violations)}. Warning {self.user_warnings[user_id]}/{self.config['warning_threshold']}"
                await self.warn_user(message, reason)

    @commands.hybrid_command(name="antispam")
    @commands.has_permissions(manage_messages=True)
    async def antispam_config(self, ctx, setting: str = None, value: int = None):
        """Configure anti-spam settings."""
        if setting is None:
            # Show current config
            embed = discord.Embed(title="Anti-Spam Configuration", color=discord.Color.blue())
            for key, val in self.config.items():
                embed.add_field(name=key.replace('_', ' ').title(), value=str(val), inline=True)
            # Add thumbnail to all embeds
            embed.set_thumbnail(url=EMBED_THUMBNAIL)
            await ctx.send(embed=embed)
            return
            
        if setting.lower() == "toggle":
            self.config['enabled'] = not self.config['enabled']
            status = "enabled" if self.config['enabled'] else "disabled"
            await ctx.send(f"Anti-spam system {status}")
            return
            
        if setting in self.config and value is not None:
            if setting == 'enabled':
                self.config[setting] = bool(value)
            else:
                self.config[setting] = value
            await ctx.send(f"Set {setting} to {value}")
        else:
            await ctx.send("Invalid setting or value")

    @commands.hybrid_command(name="warnings")
    @commands.has_permissions(manage_messages=True)
    async def check_warnings(self, ctx, member: discord.Member = None):
        """Check warning count for a user."""
        if member is None:
            member = ctx.author
            
        warnings = self.user_warnings[member.id]
        embed = discord.Embed(
            title="Warning Status",
            description=f"{member.display_name} has {warnings}/{self.config['warning_threshold']} warnings",
            color=discord.Color.orange() if warnings > 0 else discord.Color.green()
        )
        # Add thumbnail to all embeds
        embed.set_thumbnail(url=EMBED_THUMBNAIL)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="clearwarnings")
    @commands.has_permissions(manage_messages=True)
    async def clear_warnings(self, ctx, member: discord.Member):
        """Clear warnings for a user."""
        self.user_warnings[member.id] = 0
        await ctx.send(f"Cleared warnings for {member.display_name}")

async def setup(bot):
    await bot.add_cog(AntiSpam(bot))
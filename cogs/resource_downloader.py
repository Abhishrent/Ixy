import discord
from discord.ext import commands
import os
import json
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, List, Dict
from config import EMBED_THUMBNAIL

# Configure logging
logger = logging.getLogger(__name__)

# Constants
DOWNLOAD_CHANNEL_ID = 1435520035568226365  # Replace with your actual channel ID
COG_DIR = Path(__file__).parent
DOWNLOADABLE_DIR = (COG_DIR / ".." / "downloadable").resolve()
BOT_MEMORY_DIR = COG_DIR / ".." / "bot_memory"
STATE_FILE = BOT_MEMORY_DIR / "downloader_state.json"

# File size limit (25MB for regular uploads)
MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB in bytes

# Ensure directories exist
DOWNLOADABLE_DIR.mkdir(parents=True, exist_ok=True)
BOT_MEMORY_DIR.mkdir(parents=True, exist_ok=True)


class StateManager:
    """Handles persistent state for the downloader GUI"""
    
    @staticmethod
    def load() -> Dict:
        """Load state from disk"""
        if STATE_FILE.exists():
            try:
                with open(STATE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data if isinstance(data, dict) else {"message_id": None, "channel_id": None}
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Failed to load state: {e}")
        return {"message_id": None, "channel_id": None}
    
    @staticmethod
    def save(data: Dict) -> bool:
        """Save state to disk"""
        try:
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            return True
        except (IOError, TypeError) as e:
            logger.error(f"Failed to save state: {e}")
            return False


def safe_path_join(base_path: Path, *parts) -> Path:
    """
    Safely join paths and ensure the result is within base_path.
    Prevents directory traversal attacks.
    """
    try:
        # Handle empty or None parts
        filtered_parts = [str(p) for p in parts if p and str(p) not in ["", "."]]
        if not filtered_parts:
            return base_path.resolve()
        
        # Join and resolve
        result = (base_path / Path(*filtered_parts)).resolve()
        
        # Ensure result is still within base_path
        result.relative_to(base_path.resolve())
        return result
    except (ValueError, OSError) as e:
        logger.error(f"Path validation failed: {e}")
        raise ValueError("Invalid path: directory traversal detected")


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format"""
    if size_bytes < 0:
        return "0 B"
    
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


class FileBrowserView(discord.ui.View):
    """Interactive file browser with pagination and selection"""
    
    def __init__(self, bot: commands.Bot, initial_path: str = ".", page: int = 0, selected_item: Optional[Tuple[str, str]] = None):
        super().__init__(timeout=None)  # Persistent view
        self.bot = bot
        self.current_path = Path(initial_path) if initial_path and initial_path != "" else Path(".")
        self.page = max(0, page)
        self.selected_item: Optional[Tuple[str, str]] = selected_item  # (type, path) tuple
        self.items_per_page = 25
        
        # Create an index mapping for dropdown values
        self._item_map: Dict[int, Tuple[str, str]] = {}
        
        # Build the UI
        self._build_ui()
    
    def _get_directory_contents(self) -> List[Tuple[str, str, int]]:
        """Get sorted list of files and folders in current directory"""
        try:
            real_path = safe_path_join(DOWNLOADABLE_DIR, str(self.current_path))
            
            if not real_path.exists() or not real_path.is_dir():
                return []
            
            entries = []
            for item in real_path.iterdir():
                # Skip hidden files and special files
                if item.name.startswith('.') or item.name.startswith('__'):
                    continue
                
                try:
                    if item.is_dir():
                        entries.append(('dir', item.name, 0))
                    elif item.is_file():
                        size = item.stat().st_size
                        entries.append(('file', item.name, size))
                except (OSError, PermissionError) as e:
                    logger.warning(f"Could not access {item.name}: {e}")
                    continue
            
            # Sort: folders first, then files, alphabetically (case-insensitive)
            entries.sort(key=lambda x: (x[0] != 'dir', x[1].lower()))
            return entries
            
        except (ValueError, OSError, PermissionError) as e:
            logger.error(f"Error reading directory: {e}")
            return []
    
    def _build_ui(self):
        """Build all UI components"""
        self.clear_items()
        
        entries = self._get_directory_contents()
        total_items = len(entries)
        
        # Pagination
        start_idx = self.page * self.items_per_page
        end_idx = min(start_idx + self.items_per_page, total_items)
        page_entries = entries[start_idx:end_idx]
        
        # Clear and rebuild item map
        self._item_map = {}
        
        # Select menu - ONLY if we have items
        if page_entries:
            options = []
            for idx, (item_type, name, size) in enumerate(page_entries):
                # Truncate long names for display (Discord limit is 100 chars for label)
                display_name = name if len(name) <= 90 else name[:87] + "..."
                emoji = "📁" if item_type == "dir" else "📄"
                
                # Create relative path for this item
                if str(self.current_path) == ".":
                    item_path = name
                else:
                    item_path = str(Path(self.current_path) / name)
                
                # Use short index as value
                short_value = str(idx)
                self._item_map[idx] = (item_type, item_path)
                
                # Description shows file size for files
                desc = "Folder" if item_type == "dir" else format_file_size(size)
                
                options.append(
                    discord.SelectOption(
                        label=display_name,
                        value=short_value,
                        description=desc[:100],  # Discord limit
                        emoji=emoji
                    )
                )
            
            select = discord.ui.Select(
                placeholder="Select a file or folder...",
                options=options,
                custom_id="file_select",
                row=0
            )
            select.callback = self._select_callback
            self.add_item(select)
        
        # Row 1: Navigation and Download
        current_is_root = str(self.current_path) in [".", ""]
        
        back_btn = discord.ui.Button(
            label="Up",
            style=discord.ButtonStyle.secondary,
            custom_id="btn_back",
            disabled=current_is_root,
            emoji="⬆️",
            row=1
        )
        back_btn.callback = self._back_callback
        self.add_item(back_btn)
        
        refresh_btn = discord.ui.Button(
            label="Refresh",
            style=discord.ButtonStyle.secondary,
            custom_id="btn_refresh",
            emoji="🔄",
            row=1
        )
        refresh_btn.callback = self._refresh_callback
        self.add_item(refresh_btn)
        
        download_enabled = (self.selected_item is not None and 
                           self.selected_item[0] == 'file')
        
        download_btn = discord.ui.Button(
            label="Download",
            style=discord.ButtonStyle.success,
            custom_id="btn_download",
            disabled=not download_enabled,
            emoji="📥",
            row=1
        )
        download_btn.callback = self._download_callback
        self.add_item(download_btn)
        
        # Row 2: Pagination (only show if needed)
        has_prev = self.page > 0
        has_next = end_idx < total_items
        
        if has_prev or has_next:
            prev_btn = discord.ui.Button(
                label="Previous",
                style=discord.ButtonStyle.secondary,
                custom_id="btn_prev",
                disabled=not has_prev,
                emoji="◀️",
                row=2
            )
            prev_btn.callback = self._prev_callback
            self.add_item(prev_btn)
            
            page_info_btn = discord.ui.Button(
                label=f"Page {self.page + 1}",
                style=discord.ButtonStyle.secondary,
                custom_id="btn_page_info",
                disabled=True,
                row=2
            )
            self.add_item(page_info_btn)
            
            next_btn = discord.ui.Button(
                label="Next",
                style=discord.ButtonStyle.secondary,
                custom_id="btn_next",
                disabled=not has_next,
                emoji="▶️",
                row=2
            )
            next_btn.callback = self._next_callback
            self.add_item(next_btn)
    
    def _create_embed(self) -> discord.Embed:
        """Create the main embed display"""
        embed = discord.Embed(
            title="📥 Resource Downloader",
            description="Browse and download files.\n"
                       "• Select a file and click **Download** to receive it via DM",
            color=discord.Color.blue(),
            timestamp=discord.utils.utcnow()
        )
        
        if EMBED_THUMBNAIL:
            embed.set_thumbnail(url=EMBED_THUMBNAIL)
        
        # Current location
        current_display = str(self.current_path) if str(self.current_path) != "." else "Root"
        embed.add_field(
            name="path:",
            value=f"`{current_display}`",
            inline=False
        )
        
        # Selected item
        if self.selected_item:
            item_type, item_path = self.selected_item
            emoji = "📁" if item_type == "dir" else "📄"
            item_name = Path(item_path).name
            
            # Add file size if it's a file
            display_text = f"{emoji} `{item_name}`"
            if item_type == 'file':
                try:
                    real_path = safe_path_join(DOWNLOADABLE_DIR, item_path)
                    if real_path.exists():
                        size = real_path.stat().st_size
                        display_text += f" ({format_file_size(size)})"
                except:
                    pass
            
            embed.add_field(
                name="✅ Selected",
                value=display_text,
                inline=False
            )
        
        # Directory contents preview
        entries = self._get_directory_contents()
        
        if entries:
            start_idx = self.page * self.items_per_page
            page_entries = entries[start_idx:start_idx + self.items_per_page]
            
            preview_lines = []
            for item_type, name, size in page_entries[:10]:
                emoji = "📁" if item_type == "dir" else "📄"
                if item_type == "file":
                    size_str = f"({format_file_size(size)})"
                    line = f"{emoji} {name} {size_str}"
                else:
                    line = f"{emoji} {name}/"
                
                # Truncate if too long
                if len(line) > 80:
                    line = line[:77] + "..."
                preview_lines.append(line)
            
            preview_text = "\n".join(preview_lines)
            if len(page_entries) > 10:
                preview_text += f"\n... and {len(page_entries) - 10} more"
            
            embed.add_field(
                name=f"📂 Contents (Page {self.page + 1})",
                value=f"```\n{preview_text}\n```",
                inline=False
            )
        else:
            embed.add_field(
                name="📂 Contents",
                value="*This folder is empty*",
                inline=False
            )
        
        total_count = len(entries)
        total_pages = max(1, (total_count + self.items_per_page - 1) // self.items_per_page)
        embed.set_footer(text=f"Total items: {total_count} | Page {self.page + 1}/{total_pages}")
        
        return embed
    
    async def _update_message(self, interaction: discord.Interaction):
        """Update the message with new embed and view"""
        try:
            # Create new view with current state
            new_view = FileBrowserView(
                self.bot, 
                str(self.current_path), 
                self.page,
                self.selected_item
            )
            
            embed = new_view._create_embed()
            await interaction.response.edit_message(embed=embed, view=new_view)
            
        except discord.HTTPException as e:
            logger.error(f"Failed to update message: {e}")
    
    # Callbacks
    async def _select_callback(self, interaction: discord.Interaction):
        """Handle item selection"""
        try:
            selected_idx = int(interaction.data['values'][0])
            
            # Look up the actual item from our map
            if selected_idx not in self._item_map:
                await interaction.response.send_message("❌ Invalid selection.", ephemeral=True)
                return
            
            item_type, item_path = self._item_map[selected_idx]
            
            if item_type == 'dir':
                # Navigate into folder
                self.current_path = Path(item_path)
                self.page = 0
                self.selected_item = None
            else:
                # File selected - just update the selection
                self.selected_item = (item_type, item_path)
            
            await self._update_message(interaction)
            
        except Exception as e:
            logger.error(f"Selection error: {e}", exc_info=True)
            try:
                await interaction.response.send_message("❌ An error occurred.", ephemeral=True)
            except:
                pass
    
    async def _back_callback(self, interaction: discord.Interaction):
        """Go up one directory"""
        if str(self.current_path) in [".", ""]:
            await interaction.response.send_message("ℹ️ Already at root directory.", ephemeral=True)
            return
        
        self.current_path = self.current_path.parent
        if str(self.current_path) == ".":
            self.current_path = Path(".")
        
        self.page = 0
        self.selected_item = None
        
        await self._update_message(interaction)
    
    async def _refresh_callback(self, interaction: discord.Interaction):
        """Refresh the current view"""
        self.selected_item = None
        await self._update_message(interaction)
    
    async def _prev_callback(self, interaction: discord.Interaction):
        """Go to previous page"""
        if self.page > 0:
            self.page -= 1
            self.selected_item = None
            await self._update_message(interaction)
    
    async def _next_callback(self, interaction: discord.Interaction):
        """Go to next page"""
        entries = self._get_directory_contents()
        max_page = max(0, (len(entries) - 1) // self.items_per_page)
        
        if self.page < max_page:
            self.page += 1
            self.selected_item = None
            await self._update_message(interaction)
    
    async def _download_callback(self, interaction: discord.Interaction):
        """Handle file download request"""
        # Defer the response immediately
        await interaction.response.defer(ephemeral=True)
        
        if not self.selected_item or self.selected_item[0] != 'file':
            await interaction.followup.send("❌ Please select a file first.", ephemeral=True)
            return
        
        item_type, item_path = self.selected_item
        file_name = Path(item_path).name
        
        try:
            # Validate path
            real_path = safe_path_join(DOWNLOADABLE_DIR, item_path)
            
            if not real_path.exists() or not real_path.is_file():
                await interaction.followup.send("❌ File not found. It may have been deleted.", ephemeral=True)
                return
            
            # Check file size
            file_size = real_path.stat().st_size
            
            if file_size > MAX_FILE_SIZE:
                await interaction.followup.send(
                    f"❌ File is too large ({format_file_size(file_size)}). "
                    f"Discord's limit is 25MB for regular uploads.",
                    ephemeral=True
                )
                return
            
            if file_size == 0:
                await interaction.followup.send("❌ Cannot send empty file.", ephemeral=True)
                return
            
            # Create DM embed
            dm_embed = discord.Embed(
                title="📥 Requested File",
                description=f"Here's your requested file: **{file_name}**",
                color=discord.Color.green(),
                timestamp=discord.utils.utcnow()
            )
            
            if EMBED_THUMBNAIL:
                dm_embed.set_thumbnail(url=EMBED_THUMBNAIL)
            
            dm_embed.add_field(name="File Size", value=format_file_size(file_size), inline=True)
            guild_name = interaction.guild.name if interaction.guild else "Direct Message"
            dm_embed.add_field(name="Requested From", value=guild_name, inline=True)
            dm_embed.set_footer(
                text=f"Requested by {interaction.user.name}",
                icon_url=interaction.user.display_avatar.url
            )
            
            # Send file via DM - send embed first, then attachment
            try:
                # Send the embed first
                await interaction.user.send(embed=dm_embed)
            except discord.Forbidden:
                error_embed = discord.Embed(
                    title="❌ Cannot Send DM",
                    description="I couldn't send you a DM. Please check that:\n"
                               "• You have DMs enabled for this server\n"
                               "• You haven't blocked the bot\n"
                               "• Your privacy settings allow DMs",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=error_embed, ephemeral=True)
                return
            except discord.HTTPException as e:
                logger.error(f"HTTP error sending DM embed: {e}")
                await interaction.followup.send(f"❌ Failed to send DM: {str(e)}", ephemeral=True)
                return
            
            # Now send the file attachment separately
            try:
                with open(real_path, 'rb') as f:
                    discord_file = discord.File(f, filename=file_name)
                    await interaction.user.send(file=discord_file)
                
                # Success confirmation
                success_embed = discord.Embed(
                    title="✅ File Sent Successfully",
                    description=f"I've sent **{file_name}** to your DMs!",
                    color=discord.Color.green()
                )
                await interaction.followup.send(embed=success_embed, ephemeral=True)
                
            except discord.Forbidden:
                # Unlikely if embed succeeded, but handle just in case
                logger.error("Forbidden when sending file after embed succeeded")
                await interaction.followup.send(
                    "❌ I was able to send the message but could not attach the file. "
                    "Please check your DM settings.", ephemeral=True
                )
            except discord.HTTPException as e:
                logger.error(f"HTTP error sending file: {e}")
                await interaction.followup.send(f"❌ Failed to send file attachment: {str(e)}", ephemeral=True)
            except Exception as e:
                logger.error(f"Unexpected error sending file attachment: {e}", exc_info=True)
                await interaction.followup.send("❌ An unexpected error occurred while sending the file.", ephemeral=True)
        
        except ValueError:
            await interaction.followup.send("❌ Invalid file path detected.", ephemeral=True)
        
        except (OSError, IOError) as e:
            logger.error(f"File system error: {e}")
            await interaction.followup.send("❌ Error reading the file. Please contact an administrator.", ephemeral=True)
        
        except Exception as e:
            logger.error(f"Unexpected error in download: {e}", exc_info=True)
            await interaction.followup.send("❌ An unexpected error occurred. Please try again later.", ephemeral=True)


class ResourceDownloader(commands.Cog):
    """Persistent file browser and downloader for Discord"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.state = StateManager.load()
        self.gui_message: Optional[discord.Message] = None
        self.view: Optional[FileBrowserView] = None
        self._lock = asyncio.Lock()
        self._initialized = False
    
    async def _ensure_gui_exists(self, channel: discord.TextChannel) -> Optional[discord.Message]:
        """Ensure the GUI message exists and is up to date"""
        async with self._lock:
            logger.info(f"Ensuring GUI exists in channel {channel.id}")
            
            # Try to fetch existing message
            if self.state.get("message_id") and self.state.get("channel_id") == channel.id:
                try:
                    logger.info(f"Attempting to fetch existing message {self.state['message_id']}")
                    msg = await channel.fetch_message(self.state["message_id"])
                    
                    # Re-attach view
                    logger.info("Message found, reattaching view...")
                    self.view = FileBrowserView(self.bot)
                    embed = self.view._create_embed()
                    
                    await msg.edit(embed=embed, view=self.view)
                    self.gui_message = msg
                    
                    logger.info(f"Successfully reattached to existing GUI message: {msg.id}")
                    return msg
                    
                except (discord.NotFound, discord.HTTPException) as e:
                    logger.warning(f"Could not fetch existing message: {e}")
                    # Message was deleted, will create new one
            
            # Create new GUI message
            logger.info("Creating new GUI message...")
            try:
                self.view = FileBrowserView(self.bot)
                embed = self.view._create_embed()
                
                msg = await channel.send(embed=embed, view=self.view)
                self.gui_message = msg
                
                # Save state
                self.state["message_id"] = msg.id
                self.state["channel_id"] = channel.id
                StateManager.save(self.state)
                
                logger.info(f"Successfully created new GUI message: {msg.id}")
                return msg
                
            except discord.HTTPException as e:
                logger.error(f"Failed to create GUI message: {e}", exc_info=True)
                raise
            except Exception as e:
                logger.error(f"Unexpected error creating GUI: {e}", exc_info=True)
                raise
    
    async def _check_gui_exists_in_channel(self, channel: discord.TextChannel) -> bool:
        """Check if the GUI message still exists in the channel"""
        if not self.state.get("message_id") or self.state.get("channel_id") != channel.id:
            return False
        
        try:
            await channel.fetch_message(self.state["message_id"])
            return True
        except (discord.NotFound, discord.HTTPException):
            return False
    
    @commands.Cog.listener()
    async def on_ready(self):
        """Initialize the GUI when bot is ready"""
        if self._initialized:
            return
        
        logger.info("ResourceDownloader cog on_ready triggered")
        await self.bot.wait_until_ready()
        logger.info("Bot is ready, proceeding with GUI initialization")
        
        channel = self.bot.get_channel(DOWNLOAD_CHANNEL_ID)
        if not channel:
            logger.error(f"Download channel {DOWNLOAD_CHANNEL_ID} not found!")
            return
        
        logger.info(f"Found download channel: {channel.name} ({channel.id})")
        
        try:
            await self._ensure_gui_exists(channel)
            self._initialized = True
            logger.info("Resource Downloader GUI initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize GUI: {e}", exc_info=True)
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Recreate GUI if it's missing from the download channel"""
        # Ignore bot messages
        if message.author.bot:
            return
        
        # Only watch the download channel
        if message.channel.id != DOWNLOAD_CHANNEL_ID:
            return
        
        # Don't check on every message, only if initialized
        if not self._initialized:
            return
        
        # Check if GUI exists
        if not await self._check_gui_exists_in_channel(message.channel):
            logger.info("GUI missing from channel, recreating...")
            try:
                await self._ensure_gui_exists(message.channel)
            except Exception as e:
                logger.error(f"Failed to recreate GUI: {e}", exc_info=True)
    
    @commands.hybrid_command(name="open_resources")
    @commands.has_permissions(manage_messages=True)
    async def open_resources(self, ctx: commands.Context):
        """
        (Admin) Create or refresh the resource downloader GUI in this channel
        
        Requires: Manage Messages permission
        """
        try:
            await ctx.defer(ephemeral=True)
            
            logger.info(f"open_resources command invoked by {ctx.author} in channel {ctx.channel.id}")
            
            msg = await self._ensure_gui_exists(ctx.channel)
            
            if msg:
                embed = discord.Embed(
                    title="✅ Resource Downloader Ready",
                    description=f"The GUI has been initialized in this channel.\n[Jump to Message]({msg.jump_url})",
                    color=discord.Color.green()
                )
                await ctx.send(embed=embed, ephemeral=True)
            else:
                raise Exception("Failed to create GUI message")
            
        except discord.Forbidden:
            error_embed = discord.Embed(
                title="❌ Permission Error",
                description="I don't have permission to send messages in this channel.",
                color=discord.Color.red()
            )
            await ctx.send(embed=error_embed, ephemeral=True)
        
        except discord.HTTPException as e:
            logger.error(f"HTTPException in open_resources: {e}", exc_info=True)
            error_embed = discord.Embed(
                title="❌ Error",
                description=f"Failed to create GUI: {str(e)}",
                color=discord.Color.red()
            )
            await ctx.send(embed=error_embed, ephemeral=True)
        
        except Exception as e:
            logger.error(f"Error in open_resources command: {e}", exc_info=True)
            await ctx.send(
                f"❌ An unexpected error occurred: {str(e)}\nCheck bot logs for details.",
                ephemeral=True
            )
    
    @commands.command(name="force_gui")
    @commands.has_permissions(manage_messages=True)
    async def force_gui(self, ctx: commands.Context):
        """Force recreate the GUI (debug command)"""
        try:
            logger.info(f"force_gui command invoked by {ctx.author}")
            
            # Clear state to force recreation
            self.state["message_id"] = None
            self.state["channel_id"] = None
            StateManager.save(self.state)
            
            msg = await self._ensure_gui_exists(ctx.channel)
            if msg:
                await ctx.send(f"✅ GUI force-created: {msg.jump_url}", delete_after=10)
            else:
                await ctx.send("❌ Failed to create GUI", delete_after=10)
            
        except Exception as e:
            logger.error(f"Error in force_gui: {e}", exc_info=True)
            await ctx.send(f"❌ Error: {str(e)}", delete_after=10)
    
    @open_resources.error
    async def open_resources_error(self, ctx: commands.Context, error):
        """Handle command errors"""
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="❌ Permission Denied",
                description="You need the **Manage Messages** permission to use this command.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, ephemeral=True)
        else:
            logger.error(f"Command error: {error}", exc_info=True)
            try:
                await ctx.send(
                    "❌ An error occurred while executing the command.",
                    ephemeral=True
                )
            except:
                pass


async def setup(bot: commands.Bot):
    """Load the cog"""
    await bot.add_cog(ResourceDownloader(bot))
import discord
from discord.ext import commands, tasks
import json
import os
from datetime import datetime, timedelta
from config import EMBED_THUMBNAIL

# Configuration
COMPETITION_CHANNEL_ID = 1406953423382773854  # Replace with your competition channel ID
FORUM_CHANNEL_ID = 1418965668937601066  # Replace with your forum channel ID
BOT_MEMORY_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../bot_memory")
COMPETITION_FILE = os.path.join(BOT_MEMORY_DIR, "dp_competition.json")
VOTE_EMOJI = "🏆"

# Helper functions for persistence
def load_competition():
    if os.path.exists(COMPETITION_FILE):
        try:
            with open(COMPETITION_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_competition(data):
    os.makedirs(BOT_MEMORY_DIR, exist_ok=True)
    with open(COMPETITION_FILE, "w") as f:
        json.dump(data, f, indent=2)

class ParticipantPages(discord.ui.View):
    def __init__(self, pages, timeout=None):
        super().__init__(timeout=timeout)
        self.pages = pages
        self.current = 0
        self.message = None
        self.update_buttons()

    def update_buttons(self):
        """Update button states and labels based on current page"""
        # Update button states
        self.prev.disabled = (self.current == 0)
        self.next.disabled = (self.current >= len(self.pages) - 1)
        
        # Update page indicator
        self.page_indicator.label = f"Page {self.current + 1}/{len(self.pages)}"

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return True

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.secondary, row=0)
    async def prev(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current > 0:
            self.current -= 1
            self.update_buttons()
            embed = self.pages[self.current]
            await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Page 1/1", style=discord.ButtonStyle.gray, disabled=True, row=0)
    async def page_indicator(self, interaction: discord.Interaction, button: discord.ui.Button):
        # This button is just for display, defer the interaction
        await interaction.response.defer()

    @discord.ui.button(label="Next", style=discord.ButtonStyle.secondary, row=0)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current < len(self.pages) - 1:
            self.current += 1
            self.update_buttons()
            embed = self.pages[self.current]
            await interaction.response.edit_message(embed=embed, view=self)

    async def on_timeout(self):
        # Disable all buttons on timeout
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except discord.NotFound:
                pass  # Message was deleted

class DPCompetition(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data = load_competition()
        self.embed_message = None
        self.competition_task = None
        if self.data.get("active"):
            self.start_competition_task()

    def create_embed(self):
        embed = discord.Embed(
            title="🏆 Best pp flex Competition",
            description="React by sending any message to join!",
            color=discord.Color.gold()
        )
        embed.set_thumbnail(url=EMBED_THUMBNAIL)
        participants = self.data.get("participants", [])
        if not participants:
            embed.add_field(name="Participants", value="No entries yet.", inline=False)
        else:
            names = [p["name"] for p in participants]
            embed.add_field(name="Participants", value="\n".join(names), inline=False)
        if self.data.get("end_time"):
            end_time = self.data["end_time"]
            embed.set_footer(text=f"Competition ends at: {end_time}")
        embed.timestamp = discord.utils.utcnow()
        return embed

    def create_participant_pages(self):
        participants = self.data.get("participants", [])
        names = [p["name"] for p in participants]
        pages = []
        max_chars = 1024
        page_size = 40  # Adjust for average name length
        for i in range(0, len(names), page_size):
            chunk = names[i:i+page_size]
            field_value = "\n".join(chunk)
            embed = discord.Embed(
                title="🏆 Best pp flex Competition",
                description="React by sending any message to join!",
                color=discord.Color.gold()
            )
            embed.set_thumbnail(url=EMBED_THUMBNAIL)
            embed.add_field(name="Participants", value=field_value, inline=False)
            if self.data.get("end_time"):
                end_time = self.data["end_time"]
                embed.set_footer(text=f"Competition ends at: {end_time}")
            embed.timestamp = discord.utils.utcnow()
            pages.append(embed)
        if not pages:
            embed = discord.Embed(
                title="🏆 Best pp flex Competition",
                description="React by sending any message to join!",
                color=discord.Color.gold()
            )
            embed.set_thumbnail(url=EMBED_THUMBNAIL)
            embed.add_field(name="Participants", value="No entries yet.", inline=False)
            if self.data.get("end_time"):
                end_time = self.data["end_time"]
                embed.set_footer(text=f"Competition ends at: {end_time}")
            embed.timestamp = discord.utils.utcnow()
            pages = [embed]
        return pages

    async def get_or_create_embed_message(self, channel):
        pages = self.create_participant_pages()
        view = ParticipantPages(pages)
        view.message = None  # Will be set after message creation
        
        if self.data.get("embed_id"):
            try:
                message = await channel.fetch_message(self.data["embed_id"])
                view.message = message
                await message.edit(embed=pages[0], view=view)
                self.embed_message = message
                return message
            except discord.NotFound:
                pass
        
        message = await channel.send(embed=pages[0], view=view)
        view.message = message
        self.embed_message = message
        self.data["embed_id"] = message.id
        save_competition(self.data)
        return message

    async def update_embed(self, channel):
        try:
            await self.get_or_create_embed_message(channel)
        except Exception as e:
            print(f"Error updating competition embed: {e}")

    async def clear_forum_threads(self, ctx):
        """Clear all existing threads in the forum channel"""
        forum = self.bot.get_channel(FORUM_CHANNEL_ID)
        if not forum:
            print(f"Error: Forum channel {FORUM_CHANNEL_ID} not found")
            return
        
        deleted_count = 0
        try:
            # Get all active threads
            active_threads = forum.threads
            for thread in active_threads:
                try:
                    await thread.delete()
                    deleted_count += 1
                    print(f"Deleted active thread: {thread.name}")
                except Exception as e:
                    print(f"Error deleting active thread {thread.name}: {e}")
            
            # Get archived threads (if any)
            try:
                async for thread in forum.archived_threads():
                    try:
                        await thread.delete()
                        deleted_count += 1
                        print(f"Deleted archived thread: {thread.name}")
                    except Exception as e:
                        print(f"Error deleting archived thread {thread.name}: {e}")
            except Exception as e:
                print(f"Error fetching archived threads: {e}")
                
        except Exception as e:
            print(f"Error clearing forum threads: {e}")
        
        print(f"Cleared {deleted_count} threads from forum channel")
        return deleted_count

    @commands.hybrid_command(name="start_dp_competition", with_app_command=True)
    @commands.has_permissions(manage_messages=True)
    async def start_dp_competition(self, ctx, duration_minutes: int):
        """Start a new DP competition with a duration in minutes"""
        if self.data.get("active"):
            await ctx.send("❌ A competition is already running.", ephemeral=True)
            return
        
        # Send initial response
        await ctx.send("🔄 Starting PP competition and clearing previous entries...", ephemeral=True)
        
        # Clear all existing forum threads
        deleted_count = await self.clear_forum_threads(ctx)
        
        end_time = (datetime.utcnow() + timedelta(minutes=duration_minutes)).strftime("%Y-%m-%d %H:%M UTC")
        self.data = {
            "active": True,
            "participants": [],
            "forum_threads": {},
            "forum_messages": {},  # Store message IDs for voting
            "embed_id": None,
            "end_time": end_time,
            "end_timestamp": (datetime.utcnow() + timedelta(minutes=duration_minutes)).timestamp()
        }
        save_competition(self.data)
        channel = self.bot.get_channel(COMPETITION_CHANNEL_ID)
        await self.update_embed(channel)
        self.start_competition_task()
        
        # Send final confirmation
        try:
            await ctx.followup.send(f"✅ DP competition started for {duration_minutes} minutes!\n🗑️ Cleared {deleted_count} previous forum entries.", ephemeral=True)
        except Exception:
            # Fallback if followup fails
            await ctx.send(f"✅ PP competition started for {duration_minutes} minutes!\n🗑️ Cleared {deleted_count} previous forum entries.", ephemeral=True)

    def start_competition_task(self):
        if self.competition_task:
            self.competition_task.cancel()
        self.competition_task = self.bot.loop.create_task(self.competition_timer())

    async def competition_timer(self):
        while True:
            if not self.data.get("active"):
                break
            now = datetime.utcnow().timestamp()
            if now >= self.data.get("end_timestamp", 0):
                await self.end_competition()
                break
            await discord.utils.sleep_until(datetime.utcfromtimestamp(self.data["end_timestamp"]))

    async def end_competition(self):
        self.data["active"] = False
        save_competition(self.data)
        channel = self.bot.get_channel(COMPETITION_CHANNEL_ID)
        forum = self.bot.get_channel(FORUM_CHANNEL_ID)
        participants = self.data.get("participants", [])
        forum_messages = self.data.get("forum_messages", {})
        
        winner = None
        max_votes = -1
        results = []
        
        for p in participants:
            message_id = forum_messages.get(str(p["user_id"]))
            votes = 0
            if message_id:
                try:
                    # First try to get the thread
                    thread_id = self.data.get("forum_threads", {}).get(str(p["user_id"]))
                    if thread_id:
                        thread = forum.get_thread(thread_id)
                        if not thread:
                            thread = await forum.fetch_channel(thread_id)
                        
                        if thread:
                            # Get the message with reactions from the thread
                            message = await thread.fetch_message(message_id)
                            reaction = discord.utils.get(message.reactions, emoji=VOTE_EMOJI)
                            if reaction:
                                votes = reaction.count - 1  # exclude bot's own reaction
                except Exception as e:
                    print(f"Error fetching votes for {p['name']}: {e}")
                    # Fallback: try to fetch directly from forum channel
                    try:
                        message = await forum.fetch_message(message_id)
                        reaction = discord.utils.get(message.reactions, emoji=VOTE_EMOJI)
                        if reaction:
                            votes = reaction.count - 1
                    except Exception as e2:
                        print(f"Fallback failed for {p['name']}: {e2}")
            
            results.append((p["name"], votes))
            if votes > max_votes:
                winner = p["name"]
                max_votes = votes
        
        # Sort results by votes (highest first)
        results.sort(key=lambda x: x[1], reverse=True)
        
        embed = discord.Embed(
            title="🏆 pp flex Competition Ended!",
            description="",
            color=discord.Color.gold()
        )
        
        if winner and max_votes > 0:
            embed.add_field(name="Winner", value=f"🎉 {winner}'s pp flex wins with {max_votes} votes!", inline=False)
        else:
            embed.add_field(name="Winner", value="No winner (no votes received).", inline=False)
        
        embed.set_thumbnail(url=EMBED_THUMBNAIL)
        await channel.send(embed=embed)
        await self.update_embed(channel)

    @commands.Cog.listener()
    async def on_message(self, message):
        # Debug: print message info
        print(f"on_message: author={message.author}, channel={message.channel.id}, content={message.content}")
        
        if not self.data.get("active"):
            print("Competition not active.")
            return
            
        if message.author.bot:
            print("Message from bot, ignoring.")
            return
            
        if message.channel.id != COMPETITION_CHANNEL_ID:
            print(f"Wrong channel: {message.channel.id}")
            return
        
        # Check if already joined
        for p in self.data.get("participants", []):
            if p["user_id"] == str(message.author.id):
                print(f"User {message.author.display_name} already joined.")
                try:
                    await message.delete()
                except Exception as e:
                    print(f"Error deleting message: {e}")
                return
        
        # Add participant
        print(f"Adding participant: {message.author.display_name}")
        participant = {
            "user_id": str(message.author.id),
            "name": message.author.display_name
        }
        self.data["participants"].append(participant)
        
        # Create forum thread
        forum = self.bot.get_channel(FORUM_CHANNEL_ID)
        thread_title = f"{message.author.display_name}'s pp flex"
        
        # Get user avatar URL with proper fallback
        avatar_url = None
        if hasattr(message.author, "display_avatar"):
            avatar_url = message.author.display_avatar.url
        elif hasattr(message.author, "avatar") and message.author.avatar:
            avatar_url = message.author.avatar.url
        else:
            avatar_url = message.author.default_avatar.url
        
        embed = discord.Embed(title=thread_title, color=discord.Color.blue())
        embed.set_image(url=avatar_url)
        
        thread = None
        thread_message = None
        
        try:
            # Create thread in forum channel
            thread, thread_message = await forum.create_thread(
                name=thread_title,
                content=f"**Vote with {VOTE_EMOJI}!**",
                embed=embed
            )
            
            # Add the voting reaction
            await thread_message.add_reaction(VOTE_EMOJI)
            
            # Store both thread ID and message ID
            self.data["forum_threads"][str(message.author.id)] = thread.id
            self.data["forum_messages"][str(message.author.id)] = thread_message.id
            
            print(f"Forum thread created for {message.author.display_name} (Thread: {thread.id}, Message: {thread_message.id})")
            
        except Exception as e:
            print(f"Error creating forum thread: {e}")
            # If thread creation fails, still add the participant but without voting capability
        
        save_competition(self.data)
        
        # Delete user message
        try:
            await message.delete()
        except Exception as e:
            print(f"Error deleting message: {e}")
        
        # Update embed
        channel = self.bot.get_channel(COMPETITION_CHANNEL_ID)
        await self.update_embed(channel)
        print(f"Participant {message.author.display_name} added and embed updated.")

    @commands.Cog.listener()
    async def on_ready(self):
        await self.bot.wait_until_ready()
        channel = self.bot.get_channel(COMPETITION_CHANNEL_ID)
        if channel:
            await self.get_or_create_embed_message(channel)

    @commands.hybrid_command(name="end_dp_competition", with_app_command=True)
    @commands.has_permissions(manage_messages=True)
    async def end_dp_competition_manual(self, ctx):
        """Manually end the current DP competition"""
        if not self.data.get("active"):
            await ctx.send("❌ No competition is currently running.", ephemeral=True)
            return
        
        await self.end_competition()
        await ctx.send("✅ Competition ended manually!", ephemeral=True)

    @commands.hybrid_command(name="competition_status", with_app_command=True)
    async def competition_status(self, ctx):
        """Check the status of the current competition"""
        if not self.data.get("active"):
            await ctx.send("❌ No competition is currently running.", ephemeral=True)
            return
        
        participants_count = len(self.data.get("participants", []))
        end_time = self.data.get("end_time", "Unknown")
        
        embed = discord.Embed(
            title="🏆 Competition Status",
            color=discord.Color.blue()
        )
        embed.add_field(name="Status", value="Active ✅", inline=True)
        embed.add_field(name="Participants", value=str(participants_count), inline=True)
        embed.add_field(name="Ends at", value=end_time, inline=False)
        
        await ctx.send(embed=embed, ephemeral=True)

    @commands.hybrid_command(name="clear_forum_entries", with_app_command=True)
    @commands.has_permissions(manage_messages=True)
    async def clear_forum_entries_manual(self, ctx):
        """Manually clear all forum entries (threads)"""
        await ctx.send("🔄 Clearing all forum entries...", ephemeral=True)
        
        deleted_count = await self.clear_forum_threads(ctx)
        
        try:
            await ctx.followup.send(f"✅ Cleared {deleted_count} forum entries!", ephemeral=True)
        except Exception:
            await ctx.send(f"✅ Cleared {deleted_count} forum entries!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(DPCompetition(bot))
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
            title="🏆 Best DP Competition",
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

    async def get_or_create_embed_message(self, channel):
        if self.data.get("embed_id"):
            try:
                message = await channel.fetch_message(self.data["embed_id"])
                self.embed_message = message
                return message
            except discord.NotFound:
                pass
        embed = self.create_embed()
        message = await channel.send(embed=embed)
        self.embed_message = message
        self.data["embed_id"] = message.id
        save_competition(self.data)
        return message

    async def update_embed(self, channel):
        try:
            embed_message = await self.get_or_create_embed_message(channel)
            new_embed = self.create_embed()
            await embed_message.edit(embed=new_embed)
        except Exception as e:
            print(f"Error updating competition embed: {e}")

    @commands.hybrid_command(name="start_dp_competition", with_app_command=True)
    @commands.has_permissions(manage_messages=True)
    async def start_dp_competition(self, ctx, duration_minutes: int):
        """Start a new DP competition with a duration in minutes"""
        if self.data.get("active"):
            await ctx.send("❌ A competition is already running.", ephemeral=True)
            return
        end_time = (datetime.utcnow() + timedelta(minutes=duration_minutes)).strftime("%Y-%m-%d %H:%M UTC")
        self.data = {
            "active": True,
            "participants": [],
            "forum_threads": {},
            "embed_id": None,
            "end_time": end_time,
            "end_timestamp": (datetime.utcnow() + timedelta(minutes=duration_minutes)).timestamp()
        }
        save_competition(self.data)
        channel = self.bot.get_channel(COMPETITION_CHANNEL_ID)
        await self.update_embed(channel)
        self.start_competition_task()
        await ctx.send(f"✅ DP competition started for {duration_minutes} minutes!", ephemeral=True)

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
        threads = self.data.get("forum_threads", {})
        winner = None
        max_votes = -1
        results = []
        for p in participants:
            thread_id = threads.get(str(p["user_id"]))
            votes = 0
            if thread_id:
                try:
                    thread = await forum.fetch_message(thread_id)
                    reaction = discord.utils.get(thread.reactions, emoji=VOTE_EMOJI)
                    if reaction:
                        votes = reaction.count - 1  # exclude bot's own reaction
                except Exception:
                    pass
            results.append((p["name"], votes))
            if votes > max_votes:
                winner = p["name"]
                max_votes = votes
        result_text = "\n".join([f"{name}: {votes} votes" for name, votes in results])
        embed = discord.Embed(
            title="🏆 DP Competition Ended!",
            description=result_text,
            color=discord.Color.gold()
        )
        if winner:
            embed.add_field(name="Winner", value=f"🎉 {winner} with {max_votes} votes!", inline=False)
        else:
            embed.add_field(name="Winner", value="No winner.", inline=False)
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
        save_competition(self.data)
        # Create forum thread (forum channel uses threads, not just messages)
        forum = self.bot.get_channel(FORUM_CHANNEL_ID)
        thread_title = f"{message.author.display_name}'s DP"
        avatar_url = message.author.display_avatar.url if hasattr(message.author, "display_avatar") else message.author.avatar_url
        embed = discord.Embed(title=thread_title, color=discord.Color.blue())
        embed.set_image(url=avatar_url)
        thread = None
        thread_message = None
        try:
            thread, thread_message = await forum.create_thread(
                name=thread_title,
                content=f"**Vote with {VOTE_EMOJI}!**",
                embed=embed
            )
            await thread_message.add_reaction(VOTE_EMOJI)
            self.data["forum_threads"][str(message.author.id)] = thread.id
            print(f"Forum thread created for {message.author.display_name}.")
        except Exception as e:
            print(f"Error creating forum thread: {e}")
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

async def setup(bot):
    await bot.add_cog(DPCompetition(bot))

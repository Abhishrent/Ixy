import discord
from discord.ext import commands
import aiohttp
import asyncio
import json
import os
import re
from config import EMBED_THUMBNAIL  # <-- Add this import

FEELINGS_PATH = os.path.join(os.path.dirname(__file__), "../bot_memory/feelings.json")
GEMINI_API_KEY = "REDACTED_GOOGLE_API_KEY"
GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

MOODS = ["depressed", "sad", "neutral", "happy", "overjoyed"]
FAVORITE_THRESHOLD = 50
FRIENDSHIP_PRAISE = 5
FRIENDSHIP_SCOLD = -7
FRIENDSHIP_GIFT = 3

# Centralized response guidelines
BASE_GUIDELINES = (
    "IMPORTANT: You are Ixy—a sassy, playful sidekick. Be cheeky but caring.\n"
    "1. Keep responses SHORT (1-2 sentences max). Quality over quantity.\n"
    "2. Lead with sass, follow with sweetness if needed.\n"
    "3. Use emojis sparingly—only when they add impact.\n"
    "4. React dramatically to praise ('Obvs! ✨') or mock-offense to scolding, but keep it brief.\n"
    "5. Never mention being AI/bot/technology. Just be Ixy.\n"
    "6. No introductions—jump straight into the response.\n"
    "7. Use casual slang but avoid rambling or over-explaining.\n"
    "8. One witty line beats three mediocre ones.\n"
    "9. Stay in character always.\n"
)
def load_memory():
    if not os.path.exists(FEELINGS_PATH):
        return {"mood": "neutral", "members": {}}
    with open(FEELINGS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_memory(data):
    with open(FEELINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

class Feelings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.memory = load_memory()
        self.lock = asyncio.Lock()

    async def cog_save(self):
        async with self.lock:
            save_memory(self.memory)

    def get_member_profile(self, member: discord.Member):
        m = self.memory["members"].setdefault(str(member.id), {
            "name": member.display_name,
            "friendship": 0,
            "favorite": False,
            "gifts": []
        })
        m["name"] = member.display_name
        return m

    def build_guidelines(self, extra_guidelines=None):
        """Build the response guidelines by combining the base guidelines with any additional context."""
        guidelines = BASE_GUIDELINES
        if extra_guidelines:
            guidelines += "\n" + extra_guidelines
        return guidelines

    async def gemini_reply(self, user, message, extra_context=None, classify_only=False, gift_emoji=None, extra_guidelines=None):
        """Generate a reply using Gemini with the provided context and guidelines."""
        profile = self.get_member_profile(user)
        mood = self.memory.get("mood", "neutral")
        gifts = " ".join(profile["gifts"]) if profile["gifts"] else "None"
        prompt = (
            f"Current mood: {mood}.\n"
            f"User: {profile['name']} with {profile['friendship']} friendship points.\n"
            f"{profile['name']} is {'a favorite' if profile['favorite'] else 'not a favorite'}.\n"
            f"Gifts: {gifts}.\n"
            f"User message: '{message}'\n"
        )
        if gift_emoji:
            prompt += f"The user just gave you a gift: {gift_emoji}\n"
        if extra_context:
            prompt += f"Context: {extra_context}\n"
        prompt += self.build_guidelines(extra_guidelines)
        prompt += (
            "Decide if this is praise, scolding, or neutral, then generate an emotional reply as Ixy. "
            "First, output ONLY the classification as one of [praise|scolding|neutral] on the first line, "
            "then your reply on the next lines. If this is a gift, treat it as praise."
        )
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 300
            }
        }
        headers = {
            "Content-Type": "application/json",
            "X-goog-api-key": GEMINI_API_KEY
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(GEMINI_ENDPOINT, headers=headers, json=payload) as resp:
                if resp.status != 200:
                    return "neutral", "Ixy is feeling a bit off and can't reply right now."
                data = await resp.json()
                try:
                    text = data["candidates"][0]["content"]["parts"][0]["text"]
                except Exception:
                    return "neutral", "Ixy is confused and can't reply right now."
        # Parse classification and reply
        lines = text.strip().splitlines()
        if not lines:
            return "neutral", text
        classification = lines[0].strip().lower()
        reply = "\n".join(lines[1:]).strip() or text
        if classify_only:
            return classification, None
        return classification, reply

    async def update_relationship(self, user, classification, gift_emoji=None):
        profile = self.get_member_profile(user)
        changed = False
        if classification == "praise":
            profile["friendship"] += FRIENDSHIP_PRAISE
            changed = True
            if gift_emoji and gift_emoji not in profile["gifts"]:
                profile["gifts"].append(gift_emoji)
                profile["friendship"] += FRIENDSHIP_GIFT
        elif classification == "scolding":
            profile["friendship"] += FRIENDSHIP_SCOLD
            changed = True
        elif classification == "neutral":
            # Small random nudge, or nothing
            pass
        # Update favorite status
        fav = profile["friendship"] >= FAVORITE_THRESHOLD
        if fav != profile["favorite"]:
            profile["favorite"] = fav
            changed = True
        await self.cog_save()
        return changed

    async def update_mood(self, classification):
        mood = self.memory.get("mood", "neutral")
        idx = MOODS.index(mood) if mood in MOODS else MOODS.index("neutral")
        old_idx = idx
        old_mood = mood

        if classification == "praise":
            idx = min(idx + 1, len(MOODS) - 1)
        elif classification == "scolding":
            idx = max(idx - 1, 0)
        # Neutral: no change

        self.memory["mood"] = MOODS[idx]
        await self.cog_save()

        # Return info if mood changed, else None
        if idx != old_idx:
            return {
                "old_mood": old_mood,
                "new_mood": MOODS[idx],
                "up": idx > old_idx
            }
        return None

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return
        
        # Skip responses in ticket channels to avoid conflicts with the gpt/openrouter cog
        if re.match(r"ticket-[a-zA-Z0-9_]+", message.channel.name):
            return
            
        if "ixy" not in message.content.lower():
            return
        # Avoid AI reply for general bot commands like "ixy count", "ixy help", etc.
        lowered = message.content.lower().strip()
        if re.match(r"^ixy\s+\w+", lowered):
            return
        # React to the message
        try:
            await message.add_reaction("🤖")
        except Exception:
            pass
        # Send to Gemini for classification and reply
        async with message.channel.typing():
            classification, reply = await self.gemini_reply(message.author, message.content)
            await self.update_relationship(message.author, classification)
            mood_change = await self.update_mood(classification)
            await message.channel.send(reply)
            # Send mood change embed after AI response
            if mood_change:
                color = discord.Color.green() if mood_change["up"] else discord.Color.red()
                if mood_change["up"]:
                    action = "You made Ixy feel better!"
                else:
                    action = "You made Ixy feel worse."
                description = (
                    f"Ixy's mood changed from **{mood_change['old_mood']}** to **{mood_change['new_mood']}**."
                )
                embed = discord.Embed(
                    title=f"🩺 {action}",
                    description=description,
                    color=color
                )
                embed.add_field(name="Previous Mood", value=mood_change["old_mood"])
                embed.add_field(name="Current Mood", value=mood_change["new_mood"])
                embed.set_footer(text="Your interactions affect Ixy's feelings!")
                embed.set_thumbnail(url=EMBED_THUMBNAIL)
                try:
                    await message.channel.send(embed=embed)
                except Exception:
                    pass

    @commands.hybrid_command()
    async def gift(self, ctx, emoji: str):
        """Give Ixy a gift (emoji)!"""
        await ctx.defer()
        if ctx.author.bot:
            return
        async with ctx.channel.typing():
            extra_guidelines = "Focus on expressing gratitude for the gift and mention how it makes Ixy feel."
            classification, reply = await self.gemini_reply(
                ctx.author,
                f"{ctx.author.display_name} gives you a gift: {emoji}",
                gift_emoji=emoji,
                extra_guidelines=extra_guidelines
            )
            await self.update_relationship(ctx.author, "praise", gift_emoji=emoji)
            mood_change = await self.update_mood("praise")
            profile = self.get_member_profile(ctx.author)
            embed = discord.Embed(
                title="🎁 Gift Given!",
                description=f"{ctx.author.mention} gave Ixy a gift: {emoji}",
                color=discord.Color.purple()
            )
            embed.add_field(name="Friendship Points", value=str(profile["friendship"]))
            embed.add_field(name="Favorite Status", value="Yes" if profile["favorite"] else "No")
            embed.add_field(name="All Gifts", value=" ".join(profile["gifts"]) if profile["gifts"] else "None")
            embed.set_footer(text="Gifts make Ixy happier and increase your friendship!")
            embed.set_thumbnail(url=EMBED_THUMBNAIL)
            await ctx.send(content=reply, embed=embed)
            # Send mood change embed after AI response
            if mood_change:
                color = discord.Color.green() if mood_change["up"] else discord.Color.red()
                if mood_change["up"]:
                    action = "You made Ixy feel better!"
                else:
                    action = "You made Ixy feel worse."
                description = (
                    f"Ixy's mood changed from **{mood_change['old_mood']}** to **{mood_change['new_mood']}**."
                )
                mood_embed = discord.Embed(
                    title=f"🩺 {action}",
                    description=description,
                    color=color
                )
                mood_embed.add_field(name="Previous Mood", value=mood_change["old_mood"])
                mood_embed.add_field(name="Current Mood", value=mood_change["new_mood"])
                mood_embed.set_footer(text="Your interactions affect Ixy's feelings!")
                mood_embed.set_thumbnail(url=EMBED_THUMBNAIL)
                try:
                    await ctx.send(embed=mood_embed)
                except Exception:
                    pass

    @commands.hybrid_command()
    async def mood(self, ctx):
        """Ask Ixy about her mood."""
        await ctx.defer()
        mood = self.memory.get("mood", "neutral")
        extra_guidelines = "Describe your mood in a gentle, supportive way as Ixy."
        classification, reply = await self.gemini_reply(
            ctx.author,
            f"Ask Ixy about her mood.",
            extra_guidelines=extra_guidelines
        )
        embed = discord.Embed(
            title="Ixy's Current Mood",
            description=f"Ixy is currently feeling **{mood}**.",
            color=discord.Color.blue()
        )
        embed.add_field(name="Mood Meaning", value={
            "depressed": "Ixy feels really down and needs lots of love.",
            "sad": "Ixy is feeling sad. Maybe a gift or kind words will help?",
            "neutral": "Ixy is feeling okay, just chilling.",
            "happy": "Ixy is cheerful and energetic!",
            "overjoyed": "Ixy is absolutely ecstatic and loves everyone!"
        }.get(mood, "Unknown mood."))
        embed.set_footer(text="Ixy's mood changes with your interactions!")
        embed.set_thumbnail(url=EMBED_THUMBNAIL)  # <-- Add thumbnail
        await ctx.send(content=reply, embed=embed)

    @commands.hybrid_command()
    async def relationship(self, ctx, member: discord.Member = None):
        """Show your (or another user's) friendship with Ixy."""
        await ctx.defer()
        member = member or ctx.author
        profile = self.get_member_profile(member)
        gifts = " ".join(profile["gifts"]) if profile["gifts"] else "None"
        fav = "Yes" if profile["favorite"] else "No"
        extra_guidelines = (
            "Focus on being playful and positive about the friendship, and mention gifts if any."
        )
        classification, summary = await self.gemini_reply(
            member,
            f"Summarize the relationship between Ixy and {profile['name']}.",
            extra_guidelines=extra_guidelines
        )
        embed = discord.Embed(
            title=f"Relationship with Ixy: {profile['name']}",
            color=discord.Color.green()
        )
        embed.add_field(name="Friendship Points", value=str(profile["friendship"]))
        embed.add_field(name="Favorite Status", value=fav)
        embed.add_field(name="Gifts Given", value=gifts)
        embed.set_footer(text="Increase your friendship by praising or gifting Ixy!")
        embed.set_thumbnail(url=EMBED_THUMBNAIL)  # <-- Add thumbnail
        await ctx.send(content=summary, embed=embed)

    @commands.hybrid_command()
    @commands.has_permissions(administrator=True)
    async def setfriendship(self, ctx, member: discord.Member, points: int):
        """[Admin/Debug] Set friendship points manually."""
        await ctx.defer()
        profile = self.get_member_profile(member)
        profile["friendship"] = points
        profile["favorite"] = points >= FAVORITE_THRESHOLD
        await self.cog_save()
        async with ctx.channel.typing():
            text = f"Set {profile['name']}'s friendship to {points}."
            embed = discord.Embed(
                title="Friendship Points Updated",
                description=f"{member.mention}'s friendship points have been set.",
                color=discord.Color.orange()
            )
            embed.add_field(name="New Friendship Points", value=str(points))
            embed.add_field(name="Favorite Status", value="Yes" if profile["favorite"] else "No")
            embed.set_footer(text="Admin action: Friendship manually adjusted.")
            embed.set_thumbnail(url=EMBED_THUMBNAIL)  # <-- Add thumbnail
            await ctx.send(content=text, embed=embed)

async def setup(bot):
    await bot.add_cog(Feelings(bot))

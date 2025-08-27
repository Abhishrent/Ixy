import discord
from discord.ext import commands, tasks
import os

class PersistentEmbed(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.channel_embeds = {}  # {channel_id: message_id}
        self.embed_title = "Persistent Embed"
        self.embed_description = "This is a persistent embed!"
        self.embed_color = discord.Color.blurple()
        self.embed_footer = None
        self.embed_thumbnail = None
        # Store JSON in bot_memory folder (absolute path)
        self.storage_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "bot_memory", "persistent_embed.json"
        )
        self.storage_file = os.path.abspath(self.storage_file)
        self.bot.loop.create_task(self.setup_view())
        self.bot.loop.create_task(self.load_persistent_embeds())

    async def setup_view(self):
        await self.bot.wait_until_ready()
        self.bot.add_view(PersistentEmbedView(self))

    async def load_persistent_embeds(self):
        await self.bot.wait_until_ready()
        import json
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, "r") as f:
                    data = json.load(f)
                    self.channel_embeds = data.get("channel_embeds", {})
                    self.embed_title = data.get("embed_title", self.embed_title)
                    self.embed_description = data.get("embed_description", self.embed_description)
                    self.embed_color = discord.Color(data.get("embed_color", self.embed_color.value))
                    self.embed_footer = data.get("embed_footer", self.embed_footer)
                    self.embed_thumbnail = data.get("embed_thumbnail", self.embed_thumbnail)
            except Exception:
                pass
        # Restore persistent embeds in all channels
        for channel_id in list(self.channel_embeds.keys()):
            channel = self.bot.get_channel(int(channel_id))
            if channel:
                try:
                    await self.resend_embed(channel)
                except Exception:
                    pass

    def save_persistent_embeds(self):
        import json
        os.makedirs(os.path.dirname(self.storage_file), exist_ok=True)
        data = {
            "channel_embeds": self.channel_embeds,
            "embed_title": self.embed_title,
            "embed_description": self.embed_description,
            "embed_color": self.embed_color.value if isinstance(self.embed_color, discord.Color) else self.embed_color,
            "embed_footer": self.embed_footer,
            "embed_thumbnail": self.embed_thumbnail,
        }
        with open(self.storage_file, "w") as f:
            json.dump(data, f)

    async def resend_embed(self, channel):
        embed = discord.Embed(
            title=self.embed_title,
            description=self.embed_description,
            color=self.embed_color
        )
        if self.embed_footer:
            embed.set_footer(text=self.embed_footer)
        if self.embed_thumbnail:
            embed.set_thumbnail(url=self.embed_thumbnail)
        msg = await channel.send(embed=embed, view=PersistentEmbedView(self))
        self.channel_embeds[str(channel.id)] = msg.id
        self.save_persistent_embeds()

    @commands.hybrid_command(name="persistent_embed", with_app_command=True)
    @commands.has_permissions(administrator=True)
    async def persistent_embed(
        self, ctx,
        *,
        content: str = None,
        title: str = None,
        color: str = None,
        footer: str = None,
        thumbnail: str = None
    ):
        """Send a persistent embed that stays at the bottom of the channel. All options are optional."""
        if title:
            self.embed_title = title
        if content:
            self.embed_description = content
        if color:
            try:
                self.embed_color = discord.Color(int(color, 16))
            except Exception:
                await ctx.send("Invalid color hex. Use format like `0x3498db`.", ephemeral=True)
                return
        if footer is not None:
            self.embed_footer = footer
        if thumbnail is not None:
            self.embed_thumbnail = thumbnail

        embed = discord.Embed(
            title=self.embed_title,
            description=self.embed_description,
            color=self.embed_color
        )
        if self.embed_footer:
            embed.set_footer(text=self.embed_footer)
        if self.embed_thumbnail:
            embed.set_thumbnail(url=self.embed_thumbnail)

        # Delete previous embed if exists
        prev_msg_id = self.channel_embeds.get(str(ctx.channel.id))
        if prev_msg_id:
            try:
                prev_msg = await ctx.channel.fetch_message(prev_msg_id)
                await prev_msg.delete()
            except Exception:
                pass
        msg = await ctx.send(embed=embed, view=PersistentEmbedView(self))
        self.channel_embeds[str(ctx.channel.id)] = msg.id
        self.save_persistent_embeds()

class PersistentEmbedView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog

    # You can add buttons here if needed for future expansion

    # No buttons for now, just persistent view for session compatibility

class PersistentEmbedSessionHandler(commands.Cog):
    def __init__(self, bot, main_cog):
        self.bot = bot
        self.main_cog = main_cog

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        channel_id = str(message.channel.id)
        msg_id = self.main_cog.channel_embeds.get(channel_id)
        if msg_id:
            try:
                prev_msg = await message.channel.fetch_message(msg_id)
                embed = prev_msg.embeds[0] if prev_msg.embeds else None
                content = prev_msg.content
                view = PersistentEmbedView(self.main_cog)
                await prev_msg.delete()
                if embed:
                    new_msg = await message.channel.send(content=content, embed=embed, view=view)
                    self.main_cog.channel_embeds[channel_id] = new_msg.id
                    self.main_cog.save_persistent_embeds()
            except Exception:
                pass

async def setup(bot):
    main_cog = PersistentEmbed(bot)
    await bot.add_cog(main_cog)
    await bot.add_cog(PersistentEmbedSessionHandler(bot, main_cog))

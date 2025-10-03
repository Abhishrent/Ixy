import discord
from discord.ext import commands
from config import EMBED_THUMBNAIL, ANNOUNCE_INPUT_CHANNEL_ID, ANNOUNCE_OUTPUT_CHANNEL_ID, IMAGE_UPLOAD_CHANNEL_ID

class ConfirmView(discord.ui.View):
    def __init__(self, author, timeout=60):
        super().__init__(timeout=timeout)
        self.author = author
        self.value = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.author.id

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = True
        await interaction.response.defer()
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = False
        await interaction.response.defer()
        self.stop()

class AnnouncementCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Ignore bot messages
        if message.author.bot:
            return

        # Announcement input channel: send embed to the announcement output channel
        if message.channel.id == ANNOUNCE_INPUT_CHANNEL_ID:
            # Split first line as title, rest as description
            lines = message.content.split('\n', 1)
            title = lines[0].strip() if lines else ""
            description = lines[1].strip() if len(lines) > 1 else ""
            embed = discord.Embed(
                title=title,
                description=description,
                color=discord.Color.blue()
            )
            embed.set_thumbnail(url=EMBED_THUMBNAIL)
            # Attachments as images
            if message.attachments:
                for attachment in message.attachments:
                    if attachment.content_type and attachment.content_type.startswith("image/"):
                        # Notify about image upload
                        notifier_embed = discord.Embed(
                            title="Building Preview",
                            description="Please wait while I generate the preview",
                            color=discord.Color.orange()
                        )
                        notifier_msg = await message.channel.send(embed=notifier_embed)

                        # Upload image to the dedicated channel
                        upload_channel = self.bot.get_channel(IMAGE_UPLOAD_CHANNEL_ID)
                        if upload_channel:
                            uploaded_msg = await upload_channel.send(file=await attachment.to_file())
                            if uploaded_msg.attachments:
                                embed.set_image(url=uploaded_msg.attachments[0].url)

                        # Delete notifier message
                        await notifier_msg.delete()
                        break

            # Show confirmation with a preview before sending announcement (using buttons)
            preview_content = None
            if message.attachments:
                filenames = [
                    attachment.filename for attachment in message.attachments
                    if not (attachment.content_type and attachment.content_type.startswith("image/") and embed.image and embed.image.url)
                ]
                if filenames:
                    preview_content = "Attachments:\n```\n" + "\n".join(filenames) + "\n```"

            view = ConfirmView(message.author)
            preview_msg = await message.channel.send(
                preview_content if preview_content else None,
                embed=embed,
                view=view
            )
            await view.wait()

            if view.value is None:
                await preview_msg.edit(
                    embed=discord.Embed(
                        title="Timed Out",
                        description="Timed out. Announcement not sent.",
                        color=discord.Color.red()
                    ),
                    view=None
                )
                await message.delete()  # Delete the original user message
                return

            if view.value:
                await message.delete()
                output_channel = message.guild.get_channel(ANNOUNCE_OUTPUT_CHANNEL_ID)
                if output_channel:
                    try:
                        # Collect mentions for users and roles
                        pings = []
                        if message.mentions:
                            pings.extend(user.mention for user in message.mentions)
                        if message.role_mentions:
                            pings.extend(role.mention for role in message.role_mentions)
                        
                        # Check for @everyone and @here mentions
                        if "@everyone" in message.content:
                            pings.append("@everyone")
                        if "@here" in message.content:
                            pings.append("@here")
                        
                        content = " ".join(pings) if pings else None
                        await output_channel.send(content=content, embed=embed)
                        
                        # Send non-image attachments if any
                        for attachment in message.attachments:
                            if not (attachment.content_type and attachment.content_type.startswith("image/")):
                                await output_channel.send(file=await attachment.to_file())
                    except Exception:
                        pass
                await preview_msg.edit(
                    embed=discord.Embed(
                        title="Announcement Sent",
                        description="The announcement has been sent successfully.",
                        color=discord.Color.green()
                    ),
                    view=None
                )
            else:
                await preview_msg.edit(
                    content=None,  # Clear the message content
                    embed=discord.Embed(
                        title="Announcement Cancelled",
                        description="The announcement was cancelled.",
                        color=discord.Color.red()
                    ),
                    view=None
                )
                await message.delete()  # Delete the original user message
                return

async def setup(bot):
    await bot.add_cog(AnnouncementCog(bot))
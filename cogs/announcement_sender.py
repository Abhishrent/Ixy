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
            # Check if there's only attachments without text
            attachments_only = message.attachments and not message.content.strip()
            
            embed = None
            footer_text = None
            footer_icon_url = None
            
            if not attachments_only:
                # Split first line as title, rest as description, and extract footer block after '---'
                raw_lines = message.content.split('\n')
                footer = None
                footer_index = None
                for i, ln in enumerate(raw_lines):
                    if ln.strip() == '---':
                        footer_index = i
                        break
                if footer_index is not None:
                    footer = '\n'.join(raw_lines[footer_index+1:]).strip()
                    content_lines = raw_lines[:footer_index]
                else:
                    content_lines = raw_lines

                # Determine footer text and possible footer icon URL (if first footer line is a direct image URL)
                if footer:
                    footer_lines = [l for l in footer.split('\n') if l.strip()]
                    if footer_lines:
                        first = footer_lines[0].strip()
                        # simple image URL heuristic
                        if first.lower().startswith(('http://', 'https://')) and first.lower().split('?')[0].endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                            footer_icon_url = first
                            footer_text = '\n'.join(footer_lines[1:]).strip()
                        else:
                            footer_text = footer

                title = content_lines[0].strip() if content_lines else ""
                description = '\n'.join(content_lines[1:]).strip() if len(content_lines) > 1 else ""
                embed = discord.Embed(
                    title=title,
                    description=description,
                    color=discord.Color.blue()
                )
                embed.set_thumbnail(url=EMBED_THUMBNAIL)
                # Note: footer will be applied later after potential attachment uploads set footer_icon_url

            # Attachments as images (only process for embed if not attachments_only)
            if message.attachments and not attachments_only:
                # Prefer an attachment intended as footer if its filename contains 'footer'
                footer_attachment = next((a for a in message.attachments if 'footer' in (a.filename or '').lower()), None)

                for attachment in message.attachments:
                    if attachment.content_type and attachment.content_type.startswith("image/"):
                        # If this attachment is the footer attachment, upload it and set footer_icon_url
                        if footer_attachment and attachment == footer_attachment:
                            notifier_embed = discord.Embed(
                                title="Building Preview",
                                description="Please wait while I generate the preview",
                                color=discord.Color.orange()
                            )
                            notifier_msg = await message.channel.send(embed=notifier_embed)

                            upload_channel = self.bot.get_channel(IMAGE_UPLOAD_CHANNEL_ID)
                            if upload_channel:
                                uploaded_msg = await upload_channel.send(file=await attachment.to_file())
                                if uploaded_msg.attachments:
                                    # set as footer icon (takes precedence over inline URL in footer text)
                                    footer_icon_url = uploaded_msg.attachments[0].url
                            await notifier_msg.delete()
                            # continue scanning other attachments for main image
                            continue

                        # Otherwise treat as main embed image (first non-footer image)
                        notifier_embed = discord.Embed(
                            title="Building Preview",
                            description="Please wait while I generate the preview",
                            color=discord.Color.orange()
                        )
                        notifier_msg = await message.channel.send(embed=notifier_embed)

                        upload_channel = self.bot.get_channel(IMAGE_UPLOAD_CHANNEL_ID)
                        if upload_channel:
                            uploaded_msg = await upload_channel.send(file=await attachment.to_file())
                            if uploaded_msg.attachments:
                                embed.set_image(url=uploaded_msg.attachments[0].url)

                        await notifier_msg.delete()
                        break

                # If a footer_attachment was present but not processed above (e.g., it wasn't image/ or loop skipped), try uploading it now
                if footer_attachment and not footer_icon_url:
                    if footer_attachment.content_type and footer_attachment.content_type.startswith("image/"):
                        upload_channel = self.bot.get_channel(IMAGE_UPLOAD_CHANNEL_ID)
                        if upload_channel:
                            uploaded_msg = await upload_channel.send(file=await footer_attachment.to_file())
                            if uploaded_msg.attachments:
                                footer_icon_url = uploaded_msg.attachments[0].url

                # Finally set the footer if we have text or an icon
                if footer_text or footer_icon_url:
                    embed.set_footer(
                        text=footer_text if footer_text else "",
                        icon_url=footer_icon_url if footer_icon_url else None
                    )
            elif embed and (footer_text or footer_icon_url):
                # Set footer even if no attachments (for text-only footers)
                embed.set_footer(
                    text=footer_text if footer_text else "",
                    icon_url=footer_icon_url if footer_icon_url else None
                )
            
            # Show confirmation with a preview before sending announcement (using buttons)
            preview_content = None
            if message.attachments:
                if attachments_only:
                    # For attachments-only, show all attachment filenames
                    filenames = [attachment.filename for attachment in message.attachments]
                    preview_content = "Attachments to send:\n```\n" + "\n".join(filenames) + "\n```"
                else:
                    # For regular posts, show only non-image attachments
                    filenames = [
                        attachment.filename for attachment in message.attachments
                        if not (attachment.content_type and attachment.content_type.startswith("image/") and embed.image and embed.image.url)
                    ]
                    if filenames:
                        preview_content = "Attachments:\n```\n" + "\n".join(filenames) + "\n```"

            view = ConfirmView(message.author)
            preview_msg = await message.channel.send(
                preview_content if preview_content else None,
                embed=embed,  # Will be None for attachments-only mode
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
                # Store non-image attachments before deleting the message
                attachment_files = []
                for attachment in message.attachments:
                    # In attachments-only mode, save all attachments
                    # In regular mode, save only non-image attachments
                    if attachments_only or not (attachment.content_type and attachment.content_type.startswith("image/")):
                        attachment_files.append(await attachment.to_file())
                
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
                
                # Now delete the original message
                await message.delete()
                
                output_channel = message.guild.get_channel(ANNOUNCE_OUTPUT_CHANNEL_ID)
                if output_channel:
                    try:
                        content = " ".join(pings) if pings else None
                        
                        # For attachments-only mode, just send the files without any embed
                        if attachments_only:
                            await output_channel.send(content=content, files=attachment_files)
                        else:
                            # For regular mode, send the embed and then any non-image attachments
                            await output_channel.send(content=content, embed=embed)
                            if attachment_files:
                                await output_channel.send(files=attachment_files)
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
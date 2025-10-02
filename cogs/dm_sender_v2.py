import discord
from discord.ext import commands
import json
import os
import asyncio
from config import EMBED_THUMBNAIL
import discord.errors  # Add this import for exception handling

DM_CHANNEL_ID = 1406952218543788063
IMAGE_UPLOAD_CHANNEL_ID = 1410834897584783380
SERVER_USER_JSON = os.path.join(os.path.dirname(__file__), '../bot_memory/server_user_id.json')

def ensure_and_update_server_user_json(guild):
    """Ensure the server_user_id.json exists and is up-to-date with current guild members."""
    os.makedirs(os.path.dirname(SERVER_USER_JSON), exist_ok=True)
    
    # Load existing data if file exists
    existing_data = {}
    if os.path.exists(SERVER_USER_JSON):
        try:
            with open(SERVER_USER_JSON, 'r') as f:
                existing_entries = json.load(f)
                existing_data = {entry['user_id']: entry for entry in existing_entries}
        except (json.JSONDecodeError, KeyError):
            # If file is corrupted, start fresh
            existing_data = {}
    
    # Update with current guild members, preserving existing data
    user_data = []
    for member in guild.members:
        if member.id in existing_data:
            # Preserve existing entry, update display_name
            entry = existing_data[member.id].copy()
            entry['display_name'] = member.display_name
        else:
            # Create new entry
            entry = {
                "user_id": member.id,
                "display_name": member.display_name
            }
        user_data.append(entry)
    
    with open(SERVER_USER_JSON, "w") as f:
        json.dump(user_data, f, indent=2)

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

class RoleSelectView(discord.ui.View):
    def __init__(self, author, roles, allowed_users, base_embed, timeout=120):
        super().__init__(timeout=timeout)
        self.author = author
        self.allowed_users = allowed_users
        self.roles = roles
        self.selected_role_ids = set()
        self.value = None
        self.base_embed = base_embed
        self.select = discord.ui.Select(
            placeholder="Select roles to DM...",
            min_values=1,
            max_values=len(roles),
            options=[
                discord.SelectOption(label=role.name, value=str(role.id))
                for role in roles
            ]
        )
        self.select.callback = self.select_callback
        self.add_item(self.select)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.author.id

    async def on_timeout(self):
        # Optionally handle timeout cleanup if needed
        pass

    async def select_callback(self, interaction: discord.Interaction):
        self.selected_role_ids = set(map(int, self.select.values))
        # Create a new embed for role selection status
        desc_lines = []
        for role in self.roles:
            selected = " **[SELECTED]**" if role.id in self.selected_role_ids else ""
            desc_lines.append(f"{role.name}{selected}")
        embed = discord.Embed(
            title="Select Roles to DM",
            description="",  # No description here
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=self.base_embed.thumbnail.url if self.base_embed.thumbnail else discord.Embed.Empty)
        if self.base_embed.image and self.base_embed.image.url:
            embed.set_image(url=self.base_embed.image.url)
        embed.add_field(name="Selected Roles", value="\n".join(desc_lines) or "None", inline=False)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.selected_role_ids:
            await interaction.response.send_message("Please select at least one role.", ephemeral=True)
            return
        self.value = True
        await interaction.response.defer()
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = False
        await interaction.response.defer()
        self.stop()

class DMProgressView(discord.ui.View):
    def __init__(self, author, sent_count, total_count, timeout=60):
        super().__init__(timeout=timeout)
        self.author = author
        self.value = None
        self.sent_count = sent_count
        self.total_count = total_count

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.author.id

    @discord.ui.button(label="Continue", style=discord.ButtonStyle.success)
    async def continue_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = "continue"
        await interaction.response.defer()
        self.stop()

    @discord.ui.button(label="New", style=discord.ButtonStyle.danger)
    async def new_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = "new"
        await interaction.response.defer()
        self.stop()

class DMSenderCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Ignore bot messages
        if message.author.bot:
            return

        # DM channel: DM users from JSON only
        if message.channel.id == DM_CHANNEL_ID:
            # Ensure and update the user JSON before loading
            ensure_and_update_server_user_json(message.guild)
            # Load allowed user IDs from server_user_id.json
            with open(SERVER_USER_JSON, 'r') as f:
                allowed_users = set(entry['user_id'] for entry in json.load(f))

            # Find all roles with at least one allowed user
            roles_with_allowed = []
            for role in message.guild.roles:
                if any(member.id in allowed_users for member in role.members):
                    roles_with_allowed.append(role)
            if not roles_with_allowed:
                await message.channel.send(
                    embed=discord.Embed(
                        title="No Roles Found",
                        description="No roles with allowed users found.",
                        color=discord.Color.red()
                    ),
                    delete_after=5
                )
                await message.delete()
                return

            # Split first line as title, rest as description
            lines = message.content.split('\n', 1)
            title = lines[0].strip() if lines else ""
            description = lines[1].strip() if len(lines) > 1 else ""

            # Preview embed (blue)
            preview_embed = discord.Embed(
                title=title,
                description=description,
                color=discord.Color.blue()
            )
            preview_embed.set_thumbnail(url=EMBED_THUMBNAIL)

            # Prepare attachment lists
            embed_image_url = None
            attachments_to_send = []

            # Handle image attachments
            if message.attachments:
                for attachment in message.attachments:
                    if attachment.content_type and attachment.content_type.startswith("image/") and embed_image_url is None:
                        # show this while the image is being uploaded to the dedicated storage channel
                        notifier_embed = discord.Embed(
                            title="Building Preview",
                            description="Please wait while I generate the preview...",
                            color=discord.Color.orange()
                        )
                        notifier_msg = await message.channel.send(embed=notifier_embed)

                        # Upload image to the dedicated channel
                        upload_channel = self.bot.get_channel(IMAGE_UPLOAD_CHANNEL_ID)
                        if upload_channel:
                            uploaded_msg = await upload_channel.send(file=await attachment.to_file())
                            if uploaded_msg.attachments:
                                embed_image_url = uploaded_msg.attachments[0].url
                                preview_embed.set_image(url=embed_image_url)

                        # Delete notifier message
                        await notifier_msg.delete()
                        # Only first image is used for embed
                    else:
                        attachments_to_send.append(attachment)
            # Show preview first

            # Prepare preview content with attachment filenames
            preview_content = None
            if attachments_to_send:
                filenames = [attachment.filename for attachment in attachments_to_send]
                preview_content = "Attachments:\n```\n" + "\n".join(filenames) + "\n```"

            preview_view = ConfirmView(message.author)
            preview_msg = await message.channel.send(
                preview_content if preview_content else None,
                embed=preview_embed,
                view=preview_view
            )
            await preview_view.wait()

            if preview_view.value is None:
                await preview_msg.edit(
                    embed=discord.Embed(
                        title="Timed Out",
                        description="Timed out. DM not sent.",
                        color=discord.Color.red()
                    ),
                    view=None
                )
                await message.delete()
                return

            if not preview_view.value:
                await preview_msg.edit(
                    content=None,  # Clear the message content
                    embed=discord.Embed(
                        title="DM Cancelled",
                        description="The DM was cancelled.",
                        color=discord.Color.red()
                    ),
                    view=None
                )
                await message.delete()
                return

            # Role selection embed (green, separate from preview)
            # Show all roles before any selection
            desc_lines = [f"{role.name}" for role in roles_with_allowed]
            role_select_embed = discord.Embed(
                title="Select Roles to DM",
                description="",  # No description here
                color=discord.Color.green()
            )
            role_select_embed.set_thumbnail(url=EMBED_THUMBNAIL)
            if preview_embed.image and preview_embed.image.url:
                role_select_embed.set_image(url=preview_embed.image.url)
            role_select_embed.add_field(
                name="Roles",
                value="\n".join(desc_lines) or "None",
                inline=False
            )

            role_view = RoleSelectView(message.author, roles_with_allowed, allowed_users, role_select_embed)
            await preview_msg.edit(
                content="Select roles to DM. Confirm to send, Cancel to abort.",
                embed=role_select_embed,
                view=role_view
            )
            await role_view.wait()

            if role_view.value is None:
                await preview_msg.edit(
                    embed=discord.Embed(
                        title="Timed Out",
                        description="Timed out. DM not sent.",
                        color=discord.Color.red()
                    ),
                    view=None
                )
                await message.delete()
                return

            if not role_view.value:
                await preview_msg.edit(
                    content=None,  # Clear the message content
                    embed=discord.Embed(
                        title="DM Cancelled",
                        description="The DM was cancelled.",
                        color=discord.Color.red()
                    ),
                    view=None
                )
                await message.delete()
                return

            # Collect users in selected roles who are in allowed_users
            selected_roles = [role for role in roles_with_allowed if role.id in role_view.selected_role_ids]
            # Load user data from server_user_id.json
            with open(SERVER_USER_JSON, 'r') as f:
                user_data = json.load(f)
            user_data_dict = {entry['user_id']: entry for entry in user_data}

            # --- Interactive prompt if any users have already received DMs ---
            already_sent_users = [entry for entry in user_data if entry.get('dm_sent', False)]
            total_selected_users = set()
            for role in selected_roles:
                for member in role.members:
                    if member.id in allowed_users:
                        total_selected_users.add(member.id)
            sent_count = sum(1 for entry in user_data if entry.get('dm_sent', False) and entry['user_id'] in total_selected_users)
            total_count = len(total_selected_users)

            if sent_count > 0:
                progress_embed = discord.Embed(
                    title="Some Users Have Already Received DMs",
                    description=(
                        f"{sent_count} out of {total_count} users in the selected roles have already received DMs.\n\n"
                        "Would you like to continue sending DMs to the remaining users, or start a new DM session and DM everyone again?"
                    ),
                    color=discord.Color.orange()
                )
                progress_embed.add_field(
                    name="Continue",
                    value="Only DM users who have not received a DM yet from the previous DM request.",
                    inline=False
                )
                progress_embed.add_field(
                    name="New",
                    value="Clear all DM progress and DM everyone in the selected roles.",
                    inline=False
                )
                progress_view = DMProgressView(message.author, sent_count, total_count)
                progress_msg = await message.channel.send(embed=progress_embed, view=progress_view)
                await progress_view.wait()
                await progress_msg.edit(view=None)
                if progress_view.value is None:
                    await progress_msg.edit(
                        embed=discord.Embed(
                            title="Timed Out",
                            description="Timed out. DM not sent.",
                            color=discord.Color.red()
                        ),
                        view=None
                    )
                    await message.delete()
                    return
                if progress_view.value == "new":
                    # Clear all dm_sent flags for selected users
                    for entry in user_data_dict.values():
                        if entry['user_id'] in total_selected_users and 'dm_sent' in entry:
                            entry.pop('dm_sent')
                    with open(SERVER_USER_JSON, 'w') as f:
                        json.dump(list(user_data_dict.values()), f, indent=2)
                # Store reference to delete later
                progress_msg_to_delete = progress_msg
            else:
                progress_msg_to_delete = None
            # --- End interactive prompt ---

            # Build users_to_dm list based on user's choice
            users_to_dm = set()
            for role in selected_roles:
                for member in role.members:
                    if member.id in allowed_users:
                        entry = user_data_dict.get(member.id)
                        # Only DM users who have not been marked as sent
                        if not entry.get('dm_sent', False):
                            users_to_dm.add(member)
            users = list(users_to_dm)
            if not users:
                await preview_msg.edit(
                    embed=discord.Embed(
                        title="No Valid Users Found",
                        description="No valid users found in selected roles.",
                        color=discord.Color.red()
                    ),
                    view=None
                )
                await message.delete()
                return
            failed_users = []
            # --- Progress bar code starts here ---
            total = len(users)
            progress_bar_length = 10
            # Count already sent (for progress bar)
            sent_count = sum(1 for entry in user_data if entry.get('dm_sent', False) and entry['user_id'] in total_selected_users)

            def make_progress_bar(done, total, bar_len=10):
                filled = int(bar_len * done / total) if total else 0
                return "[" + "█" * filled + "-" * (bar_len - filled) + f"] {done}/{total}"

            # Show initial progress bar
            progress = make_progress_bar(sent_count, total, progress_bar_length)
            await preview_msg.edit(
                content=None,  # Clear the message content
                embed=discord.Embed(
                    title="DMing Users",
                    description=f"DMing users: {progress}",
                    color=discord.Color.blue()
                ),
                view=None
            )

            # DM users in batches to save time and avoid rate limits
            batch_size = 100  # Adjust as needed for Discord rate limits

            async def dm_user(user):
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        await user.send(embed=preview_embed)
                        # Send non-image attachments (files)
                        for attachment in attachments_to_send:
                            await user.send(file=await attachment.to_file())
                        # Mark as sent in user_data (progress tracking)
                        entry = user_data_dict.get(user.id)
                        if entry:
                            entry['dm_sent'] = True
                            # Save to JSON after each DM
                            with open(SERVER_USER_JSON, 'w') as f:
                                json.dump(list(user_data_dict.values()), f, indent=2)
                        return None  # Success
                    except discord.errors.Forbidden:
                        # DMs are disabled or bot is blocked
                        return (getattr(user, 'mention', str(user)), "DMs Disabled")
                    except Exception as e:
                        if attempt == max_retries - 1:
                            return (getattr(user, 'mention', str(user)), f"Error: {type(e).__name__}")
                return None

            # Process users in batches
            for i in range(0, len(users), batch_size):
                batch = users[i:i+batch_size]
                # Send DMs concurrently for the batch
                results = await asyncio.gather(*(dm_user(user) for user in batch))
                # Collect failed users
                failed_users.extend([r for r in results if r])
                sent_count += len(batch)
                # Update progress every batch or on last user
                if sent_count % batch_size == 0 or sent_count == total:
                    progress = make_progress_bar(sent_count, total, progress_bar_length)
                    await preview_msg.edit(
                        embed=discord.Embed(
                            title="DMing Users",
                            description=f"DMing users: {progress}",
                            color=discord.Color.blue()
                        ),
                        view=None
                    )
            # Optionally clear dm_sent flags after done (reset progress for next run)
            for entry in user_data_dict.values():
                if 'dm_sent' in entry:
                    entry.pop('dm_sent')
            with open(SERVER_USER_JSON, 'w') as f:
                json.dump(list(user_data_dict.values()), f, indent=2)
            
            # Delete the progress message if it exists
            if progress_msg_to_delete:
                await progress_msg_to_delete.delete()
            
            await preview_msg.edit(
                content=None,  # Clear the message content
                embed=discord.Embed(
                    title="DMs Sent",
                    description=(
                        f"DMs sent to {sent_count - len(failed_users)} users out of {sent_count}.\n\n"
                        f"**Roles Included:**\n" + 
                        "\n".join([role.name for role in selected_roles])
                    ),
                    color=discord.Color.green()
                ),
                view=None
            )
            if failed_users:
                # Show reason for each failed user
                failed_desc = "\n".join(
                    f"{user} - {reason}" for user, reason in failed_users
                )
                failed_embed = discord.Embed(
                    title="Some Users Could Not Be DMed",
                    description=failed_desc,
                    color=discord.Color.red()
                )
                await message.channel.send(embed=failed_embed)
            else:
                pass
            await message.delete()

async def setup(bot):
    await bot.add_cog(DMSenderCog(bot))
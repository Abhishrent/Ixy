import discord
from discord.ext import commands
import json
import os
from config import EMBED_THUMBNAIL

ANNOUNCE_INPUT_CHANNEL_ID = 1406952251695566908
ANNOUNCE_OUTPUT_CHANNEL_ID = 1130103633141317643
DM_CHANNEL_ID = 1406952218543788063

SERVER_USER_JSON = os.path.join(os.path.dirname(__file__), '../bot_memory/server_user_id.json')

def ensure_and_update_server_user_json(guild):
    """Ensure the server_user_id.json exists and is up-to-date with current guild members."""
    os.makedirs(os.path.dirname(SERVER_USER_JSON), exist_ok=True)
    user_data = []
    for member in guild.members:
        user_data.append({
            "user_id": member.id,
            "display_name": member.display_name
        })
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

class AnnouncerCog(commands.Cog):
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
                        embed.set_image(url=attachment.url)
                        break

            # Show confirmation with a preview before sending announcement (using buttons)
            view = ConfirmView(message.author)
            preview_msg = await message.channel.send(
                "Preview of the announcement. Click **Confirm** to send, **Cancel** to abort.",
                embed=embed,
                view=view
            )
            await view.wait()

            if view.value is None:
                await preview_msg.edit(content="Timed out. Announcement not sent.", view=None)
                await message.delete()
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
                        content = " ".join(pings) if pings else None
                        await output_channel.send(content=content, embed=embed)
                    except Exception:
                        pass
                await preview_msg.edit(content="Announcement sent.", embed=None, view=None)
            else:
                await preview_msg.edit(content="Announcement cancelled.", embed=None, view=None)

            return

# DM channel: DM users from JSON only
        elif message.channel.id == DM_CHANNEL_ID:
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
                await message.channel.send("No roles with allowed users found.", delete_after=5)
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
            if message.attachments:
                for attachment in message.attachments:
                    if attachment.content_type and attachment.content_type.startswith("image/"):
                        preview_embed.set_image(url=attachment.url)
                        break

            # Show preview first
            preview_view = ConfirmView(message.author)
            preview_msg = await message.channel.send(
                "Preview of the DM to be sent. Click **Confirm** to select roles, **Cancel** to abort.",
                embed=preview_embed,
                view=preview_view
            )
            await preview_view.wait()

            if preview_view.value is None:
                await preview_msg.edit(content="Timed out. DM not sent.", view=None)
                await message.delete()
                return

            if not preview_view.value:
                await preview_msg.edit(content="DM cancelled.", embed=None, view=None)
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
                await preview_msg.edit(content="Timed out. DM not sent.", view=None)
                await message.delete()
                return

            if role_view.value:
                # Collect users in selected roles who are in allowed_users
                selected_roles = [role for role in roles_with_allowed if role.id in role_view.selected_role_ids]
                users_to_dm = set()
                for role in selected_roles:
                    for member in role.members:
                        if member.id in allowed_users:
                            users_to_dm.add(member)
                users = list(users_to_dm)
                if not users:
                    await preview_msg.edit(content="No valid users found in selected roles.", embed=None, view=None)
                    await message.delete()
                    return
                failed_users = []
                for user in users:
                    try:
                        await user.send(embed=preview_embed)
                        # Send attachments if any (non-image files)
                        for attachment in message.attachments:
                            if not (attachment.content_type and attachment.content_type.startswith("image/")):
                                await user.send(file=await attachment.to_file())
                    except Exception:
                        failed_users.append(getattr(user, 'mention', str(user)))
                await preview_msg.edit(content="DM sent to selected roles.", embed=None, view=None)
                if failed_users:
                    failed_embed = discord.Embed(
                        title="Some users could not be DMed",
                        description="\n".join(failed_users),
                        color=discord.Color.red()
                    )
                    await message.channel.send(embed=failed_embed)
            else:
                await preview_msg.edit(content="DM cancelled.", embed=None, view=None)

            await message.delete()

async def setup(bot):
    await bot.add_cog(AnnouncerCog(bot))

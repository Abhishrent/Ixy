import discord
from discord.ext import commands
from discord import app_commands
from config import PREFIX, EMBED_THUMBNAIL
import datetime

#The annoucement modal for the /announce command
class AnnouncementModal(discord.ui.Modal, title="Announcement"):
    title_input = discord.ui.TextInput(
        label="Title",
        placeholder="Enter the announcement title",
        max_length=256
    )
    description_input = discord.ui.TextInput(
        label="Description",
        style=discord.TextStyle.paragraph,
        placeholder="Enter the announcement description",
        max_length=2000
    )
    mentions_input = discord.ui.TextInput(
        label="Mentions (comma-separated, optional)",
        required=False,
        placeholder="@everyone, @here, @role"
    )
    image_input = discord.ui.TextInput(
        label="Image URL (optional)",
        required=False,
        placeholder="https://example.com/image.png"
    )

    def __init__(self, interaction: discord.Interaction):
        super().__init__()
        self.interaction = interaction

    async def on_submit(self, interaction: discord.Interaction):
        mentions_text = ""
        mentions = self.mentions_input.value
        if mentions:
            mentions_list = mentions.split(",")
            mentions_text = " ".join([mention.strip() for mention in mentions_list])

        embed = discord.Embed(
            title=self.title_input.value,
            description=self.description_input.value,
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=EMBED_THUMBNAIL)
        image = self.image_input.value
        if image:
            embed.set_image(url=image)

        await interaction.response.send_message(content=mentions_text, embed=embed)


# ModerationCog class to handle moderation commands
class ModerationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def check_permissions(self, interaction: discord.Interaction, permission: str):
        """Check if user has the required permission"""
        user = interaction.user
        
        # Check if user has the specific permission
        if not getattr(user.guild_permissions, permission, False):
            embed = discord.Embed(
                title="❌ Insufficient Permissions",
                description=f"That's for the moderator only twin.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return False
        return True

    #announce command
    @app_commands.command(name="announce", description="Send an announcement with title, description, and optional mentions.")
    @app_commands.default_permissions(manage_messages=True)
    async def send_embed(self, interaction: discord.Interaction):
        # Check permissions at runtime
        if not await self.check_permissions(interaction, "manage_messages"):
            return
        
        # Show the modal to the user
        await interaction.response.send_modal(AnnouncementModal(interaction))

    #udau command
    @app_commands.command(name="udau", description="Delete a specified number of messages in the channel.")
    @app_commands.describe(
        number="The number of messages to delete"
    )
    @app_commands.default_permissions(manage_messages=True)
    async def delete_messages(self, interaction: discord.Interaction, number: int):
        # Check permissions at runtime
        if not await self.check_permissions(interaction, "manage_messages"):
            return
        
        # Acknowledge the interaction immediately to prevent timeout
        await interaction.response.send_message(f"Attempting to delete {number} message(s)...", ephemeral=True)

        # Get the channel where the command was used
        channel = interaction.channel

        # Try to delete the messages
        try:
            deleted = await channel.purge(limit=number)
            await interaction.followup.send(f"Successfully deleted {len(deleted)} message(s).", ephemeral=True)
        except discord.Forbidden:
            await interaction.followup.send("I don't have permission to delete messages in this channel.", ephemeral=True)
        except discord.HTTPException as e:
            await interaction.followup.send(f"Failed to delete messages: {e}", ephemeral=True)

# Bhana command
    @commands.command('say')
    @commands.has_permissions(manage_messages=True)
    async def bhana(self, ctx, channel: discord.TextChannel, *, args):
        # Splits the message into title, content, mentions, and image_url
        # Format expected: #channel title | content | @user1 @user2 @user3 | image_url
        parts = args.split('|', 3)  # Splits into maximum of 4 parts
        if len(parts) < 2:
            await ctx.send(f"Please use the format: `{PREFIX[0]}bhana #channel title | content | @mentions | image_url`")
            return
        
        title = parts[0].strip()
        content = parts[1].strip()
        
        # Creates the embed
        embed = discord.Embed(
            title=title,
            description=content,
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=EMBED_THUMBNAIL)
        
        # If image_url is provided (4th part), set it in the embed
        if len(parts) == 4:
            image_url = parts[3].strip()
            if image_url:
                embed.set_image(url=image_url)
        
        # If there are mentions (part 3 exists), include them in the content parameter
        content_param = None
        if len(parts) >= 3:
            mentions = parts[2].strip()
            if mentions:
                content_param = mentions

        # Send embed to the specified channel with mentions in content if provided
        embed_content = await channel.send(content=content_param, embed=embed)
        
        # Handle attachments
        attachments = ctx.message.attachments
        if attachments:
            for attachment in attachments:
                await channel.send(file=await attachment.to_file())
        
        # Deletes the original command message
        await ctx.message.delete()
        
        # Add reactions to the embed in the target channel
        reactions = ['✅', '❌']
        for reaction in reactions:
            await embed_content.add_reaction(reaction)

    # Timeout command
    @app_commands.command(name="timeout", description="Timeout a member for a specified duration (in minutes).")
    @app_commands.describe(member="The member to timeout", duration="Duration in minutes", reason="Reason for timeout")
    @app_commands.default_permissions(moderate_members=True)
    async def timeout_member(self, interaction: discord.Interaction, member: discord.Member, duration: int, reason: str = "No reason provided"):
        # Check permissions at runtime
        if not await self.check_permissions(interaction, "moderate_members"):
            return
        
        try:
            # Notify the member via DM
            try:
                embed = discord.Embed(
                    title="You have been timed out 😵",
                    description=f"You have been timed out in **{interaction.guild.name}** for {duration} minute(s).",
                    color=discord.Color.orange()
                )
                embed.add_field(name="Reason", value=reason, inline=False)
                await member.send(embed=embed)
            except Exception:
                pass  # Ignore if DM fails

            await member.timeout(datetime.timedelta(minutes=duration), reason=reason)
            
            # Send confirmation in the channel as an embed
            confirm_embed = discord.Embed(
                title="Member Timed Out",
                description=f"{member.mention} has been timed out for {duration} minutes.",
                color=discord.Color.orange()
            )
            confirm_embed.add_field(name="Reason", value=reason, inline=False)
            await interaction.response.send_message(embed=confirm_embed)
        except Exception as e:
            await interaction.response.send_message(f"Failed to timeout {member.mention}: {e}", ephemeral=True)

    # Kick command
    @app_commands.command(name="kick", description="Kick a member from the server.")
    @app_commands.describe(member="The member to kick", reason="Reason for kick")
    @app_commands.default_permissions(kick_members=True)
    async def kick_member(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        # Check permissions at runtime
        if not await self.check_permissions(interaction, "kick_members"):
            return
        
        try:
            # Notify the member via DM
            try:
                kick_dm_embed = discord.Embed(
                    title="You have been kicked 👢",
                    description=f"You have been kicked from **{interaction.guild.name}**.",
                    color=discord.Color.red()
                )
                kick_dm_embed.add_field(name="Reason", value=reason, inline=False)
                await member.send(embed=kick_dm_embed)
            except Exception:
                pass  # Ignore if DM fails

            await member.kick(reason=reason)

            # Send confirmation in the channel as an embed
            kick_embed = discord.Embed(
                title="Member Kicked",
                description=f"{member.mention} has been kicked.",
                color=discord.Color.red()
            )
            kick_embed.add_field(name="Reason", value=reason, inline=False)
            await interaction.response.send_message(embed=kick_embed)
        except Exception as e:
            await interaction.response.send_message(f"Failed to kick {member.mention}: {e}", ephemeral=True)

    # Ban command
    @app_commands.command(name="ban", description="Ban a member from the server.")
    @app_commands.describe(member="The member to ban", reason="Reason for ban")
    @app_commands.default_permissions(ban_members=True)
    async def ban_member(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        # Check permissions at runtime
        if not await self.check_permissions(interaction, "ban_members"):
            return
        
        try:
            # Notify the member via DM
            try:
                ban_dm_embed = discord.Embed(
                    title="You have been banned 🔨",
                    description=f"You have been banned from **{interaction.guild.name}**.",
                    color=discord.Color.dark_red()
                )
                ban_dm_embed.add_field(name="Reason", value=reason, inline=False)
                await member.send(embed=ban_dm_embed)
            except Exception:
                pass  # Ignore if DM fails

            await member.ban(reason=reason)

            # Send confirmation in the channel as an embed
            ban_embed = discord.Embed(
                title="Member Banned",
                description=f"{member.mention} has been banned.",
                color=discord.Color.dark_red()
            )
            ban_embed.add_field(name="Reason", value=reason, inline=False)
            await interaction.response.send_message(embed=ban_embed)
        except Exception as e:
            await interaction.response.send_message(f"Failed to ban {member.mention}: {e}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(ModerationCog(bot))
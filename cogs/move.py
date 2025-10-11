import discord
from discord.ext import commands
from discord import app_commands
from typing import Union

class MoveCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def check_permissions(self, interaction: discord.Interaction, permission: str):
        """Check if user has the required permission"""
        user = interaction.user
        
        # Check if user has the specific permission
        if not getattr(user.guild_permissions, permission, False):
            embed = discord.Embed(
                title="❌ Insufficient Permissions",
                description=f"You need the `{permission}` permission to use this command.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return False
        return True

    @app_commands.command(name="move", description="Move a member from their current voice channel to another voice/stage channel.")
    @app_commands.describe(
        member="The member to move",
        channel="The voice/stage channel to move them to"
    )
    @app_commands.default_permissions(move_members=True)
    async def move_member(self, interaction: discord.Interaction, member: discord.Member, channel: Union[discord.VoiceChannel, discord.StageChannel]):
        # Check permissions at runtime
        if not await self.check_permissions(interaction, "move_members"):
            return
        
        # Check if the member is in a voice channel
        if not member.voice:
            embed = discord.Embed(
                title="❌ Cannot Move Member",
                description=f"{member.mention} is not currently in a voice channel.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Check if the target channel is a voice or stage channel
        if not isinstance(channel, (discord.VoiceChannel, discord.StageChannel)):
            embed = discord.Embed(
                title="❌ Invalid Channel",
                description="You can only move members to voice or stage channels.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        current_channel = member.voice.channel
        
        # Check if member is already in the target channel
        if current_channel == channel:
            embed = discord.Embed(
                title="❌ Already in Channel",
                description=f"{member.mention} is already in {channel.mention}.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        try:
            # Move the member
            await member.move_to(channel)
            
            # Send confirmation
            embed = discord.Embed(
                title="✅ Member Moved",
                description=f"Successfully moved {member.mention} from {current_channel.mention} to {channel.mention}.",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed)
            
        except discord.Forbidden:
            embed = discord.Embed(
                title="❌ Permission Error",
                description="I don't have permission to move members or access the target channel.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except discord.HTTPException as e:
            embed = discord.Embed(
                title="❌ Move Failed",
                description=f"Failed to move {member.mention}: {e}",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(MoveCog(bot))

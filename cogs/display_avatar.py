import discord
from discord.ext import commands
from discord import app_commands

class DisplayAvatar(commands.Cog):
    """Cog for displaying user avatars."""
    
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="avatar", aliases=["av", "pfp"], description="Display a user's avatar")
    async def display_avatar(self, ctx, *, user: discord.User = None):
        """Display a user's avatar.
        
        Usage: !avatar [@user]
        If no user is specified, shows your own avatar.
        """
        try:
            # Use the command author if no user is specified
            target_user = user or ctx.author
            
            # Get the avatar URL, fallback to default if none
            if target_user.avatar:
                avatar_url = target_user.avatar.url
            else:
                avatar_url = target_user.default_avatar.url
            
            # Create embed
            embed = discord.Embed(
                title=f"{target_user.display_name}'s Avatar",
                color=discord.Color.blurple()
            )
            embed.set_image(url=avatar_url)
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            error_embed = discord.Embed(
                title="Error",
                description=f"An error occurred while fetching the avatar: {str(e)}",
                color=discord.Color.red()
            )
            await ctx.send(embed=error_embed)

async def setup(bot):
    await bot.add_cog(DisplayAvatar(bot))
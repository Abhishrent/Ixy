import discord
from discord.ext import commands

class SelfDestructCog(commands.Cog):
    """A cog for self-destruct commands."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name = 'destruct')
    @commands.has_permissions(administrator=True)
    async def self_destruct(self, ctx):
        """Deletes all channels, roles, and optionally bans members."""
        if ctx.author.id != ctx.guild.owner_id:
            await ctx.send("Only the server owner can use this command.")
            return

        confirmation_message = await ctx.send(
            "⚠️ This will delete EVERYTHING in the server. Type `CONFIRM` to proceed."
        )

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content == "CONFIRM"

        try:
            await self.bot.wait_for('message', check=check, timeout=30.0)
        except Exception:
            await ctx.send("Self-destruct command timed out.")
            return

        # Delete all channels
        await ctx.send("Deleting all channels...")
        for channel in ctx.guild.channels:
            try:
                await channel.delete()
            except Exception as e:
                print(f"Failed to delete channel {channel.name}: {e}")

        # Delete all roles
        await ctx.send("Deleting all roles...")
        for role in ctx.guild.roles:
            if role.name != "@everyone":  # Prevent deleting the @everyone role
                try:
                    await role.delete()
                except Exception as e:
                    print(f"Failed to delete role {role.name}: {e}")

        # Optional: Ban all members
        await ctx.send("Banning all members (except the owner)...")
        for member in ctx.guild.members:
            if member != ctx.guild.owner:  # Skip the owner
                try:
                    await member.ban(reason="Server self-destruct command executed.")
                except Exception as e:
                    print(f"Failed to ban member {member.name}: {e}")

        await ctx.send("💥 The server has been self-destructed.")

# Add the cog to the bot
async def setup(bot):
    await bot.add_cog(SelfDestructCog(bot))

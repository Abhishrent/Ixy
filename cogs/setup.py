import discord
from discord.ext import commands

class ServerSetup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Logged in as {self.bot.user}')

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setup(self, ctx):
        guild = ctx.guild

        # Categories to create
        categories = ['Text Channels', 'Voice Channels', 'Admin']

        # Text Channels to create
        text_channels = ['🌍・general', '🎵・music', '🤖・bot-commands', '🔒・admin-channel']  # Added private channel

        # Voice Channels to create
        voice_channels = ['🎵・music', '🎮・gaming']

        # Roles to create
        roles = [
            {'name': 'Admin', 'permissions': discord.Permissions(administrator=True)},
            {'name': 'Moderator', 'permissions': discord.Permissions(manage_messages=True, kick_members=True)},
            {'name': 'Member', 'permissions': discord.Permissions(send_messages=True)},
        ]

        # Create roles
        for role in roles:
            if not discord.utils.get(guild.roles, name=role['name']):
                await guild.create_role(name=role['name'], permissions=role['permissions'])

        # Create categories
        created_categories = {}
        for category_name in categories:
            category = discord.utils.get(guild.categories, name=category_name)
            if not category:
                category = await guild.create_category(category_name)
            created_categories[category_name] = category

        # Create text channels
        for channel_name in text_channels:
            if channel_name == '🌍・general':  # Check for general channel
                if not discord.utils.get(guild.text_channels, name=channel_name):
                    await guild.create_text_channel(channel_name)  # No category specified, creating outside
            elif channel_name == '🔒・admin-channel':  # Private admin channel
                if not discord.utils.get(guild.text_channels, name=channel_name):
                    overwrites = {
                        guild.default_role: discord.PermissionOverwrite(view_channel=False),  # Hide from @everyone
                        discord.utils.get(guild.roles, name='Admin'): discord.PermissionOverwrite(view_channel=True)  # Only admins can view
                    }
                    await guild.create_text_channel(channel_name, category=created_categories['Admin'], overwrites=overwrites)
            else:
                if not discord.utils.get(guild.text_channels, name=channel_name):
                    await guild.create_text_channel(channel_name, category=created_categories['Text Channels'])

        # Create voice channels
        for channel_name in voice_channels:
            if not discord.utils.get(guild.voice_channels, name=channel_name):
                await guild.create_voice_channel(channel_name, category=created_categories['Voice Channels'])

        await ctx.send("Server setup complete!")

async def setup(bot):
    await bot.add_cog(ServerSetup(bot))
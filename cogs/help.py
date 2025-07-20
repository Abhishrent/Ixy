import discord
from discord.ext import commands
from config import HELP_CHANNEL_ID
from config import EMBED_THUMBNAIL

class HelpView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)  # Persistent view
    
    @discord.ui.button(label="Open Support Ticket", style=discord.ButtonStyle.primary, emoji="🎫")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Get the Support cog and call the open_ticket method directly
        support_cog = interaction.client.get_cog("Support")
        if support_cog:
            # Check if user already has a ticket
            guild = interaction.guild
            existing_channel = discord.utils.get(guild.text_channels, name=f"ticket-{interaction.user.name}")
            if existing_channel:
                await interaction.response.send_message(f"You already have a ticket open: {existing_channel.mention}", ephemeral=True)
                return
            
            # Defer the response since ticket creation might take time
            await interaction.response.defer(ephemeral=True)
            
            # Create a mock context object for the command
            class MockContext:
                def __init__(self, interaction):
                    self.author = interaction.user
                    self.guild = interaction.guild
                    self.channel = interaction.channel
                    
                async def send(self, content):
                    # Send the response via followup since we deferred
                    await interaction.followup.send(content, ephemeral=True)
            
            mock_ctx = MockContext(interaction)
            
            # Call the open_ticket method
            await support_cog.open_ticket(mock_ctx)
        else:
            await interaction.response.send_message("Unable to find the support system. Please use `/open` manually.", ephemeral=True)

class HelpEmbedCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.last_help_message_id = None
    
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        if message.channel.id != HELP_CHANNEL_ID:
            return
        
        # Delete previous help message if it exists
        if self.last_help_message_id:
            try:
                prev_msg = await message.channel.fetch_message(self.last_help_message_id)
                await prev_msg.delete()
            except discord.NotFound:
                pass  # Message already deleted
        
        # Send new help embed with button
        embed = discord.Embed(
            title="Need Personal Assistance?",
            description="Click the button below to open a private support ticket with the organizing committee:",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="What happens when you open a ticket?",
            value="• You'll get a private channel with the organizing committee\n• Your issue will be handled confidentially\n• Use `/close` when your issue is resolved",
            inline=False
        )
        
        embed.set_footer(text="The organizing committee will respond as soon as possible.")
        embed.set_thumbnail(url=f"{EMBED_THUMBNAIL}")
        
        view = HelpView()
        help_msg = await message.channel.send(embed=embed, view=view)
        self.last_help_message_id = help_msg.id

async def setup(bot):
    await bot.add_cog(HelpEmbedCog(bot))
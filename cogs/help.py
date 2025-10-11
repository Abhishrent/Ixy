import discord
from discord.ext import commands
from config import HELP_CHANNEL_ID
from config import EMBED_THUMBNAIL

class HelpView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None)  # Persistent view
        self.cog = cog
    
    @discord.ui.button(label="Open Support Ticket", style=discord.ButtonStyle.primary, emoji="🎫", custom_id="help_ticket_button")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Get the Ticket cog and call the open method directly
        ticket_cog = interaction.client.get_cog("Ticket")
        if ticket_cog:
            # Check if user already has a ticket
            guild = interaction.guild
            existing_channel = discord.utils.get(guild.text_channels, name=f"ticket-{interaction.user.name}")
            if existing_channel:
                embed = discord.Embed(
                    title="Ticket Already Open",
                    description=f"You already have a ticket open: {existing_channel.mention}",
                    color=discord.Color.orange()
                )
                embed.set_thumbnail(url=EMBED_THUMBNAIL)
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Defer the response since ticket creation might take time
            await interaction.response.defer(ephemeral=True)
            
            # Create a mock context object for the command
            class MockContext:
                def __init__(self, interaction):
                    self.author = interaction.user
                    self.guild = interaction.guild
                    self.channel = interaction.channel
                    
                async def send(self, content=None, embed=None):
                    # Send the response via followup since we deferred
                    if embed:
                        embed.set_thumbnail(url=EMBED_THUMBNAIL)
                    await interaction.followup.send(content=content, embed=embed, ephemeral=True)
            
            mock_ctx = MockContext(interaction)
            
            # Call the open method (updated from open_ticket)
            await ticket_cog.open(mock_ctx)
        else:
            embed = discord.Embed(
                title="Ticket System Not Found",
                description="Unable to find the ticket system. Please use `/ticket open` manually.",
                color=discord.Color.red()
            )
            embed.set_thumbnail(url=EMBED_THUMBNAIL)
            await interaction.response.send_message(embed=embed, ephemeral=True)

class HelpEmbedCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.last_help_message_id = None
        self.bot.loop.create_task(self.setup_view())
    
    async def setup_view(self):
        await self.bot.wait_until_ready()
        self.bot.add_view(HelpView(self))  # Pass self to the view
    
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
            value="• You'll get a private channel with the organizing committee\n• Your issue will be handled confidentially\n• Use `/ticket close` when your issue is resolved",
            inline=False
        )

        embed.set_footer(text="The organizing committee will respond as soon as possible.")
        embed.set_thumbnail(url=EMBED_THUMBNAIL)
        
        view = HelpView(self)  # Pass self to the view
        help_msg = await message.channel.send(embed=embed, view=view)
        self.last_help_message_id = help_msg.id

async def setup(bot):
    await bot.add_cog(HelpEmbedCog(bot))
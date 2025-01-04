import discord
from discord.ext import commands
from discord import app_commands
from config import PREFIX

class ModerationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="announce", description="Send an announcement with title, description, and optional mentions.")
    @app_commands.describe(
        title="The title of the announcement",
        description="The description of the announcement",
        mentions="The mentions to include in the message (comma-separated, optional)",
        image="The image URL to include in the embed (optional)"
    )
    @commands.has_permissions(manage_messages=True)  # Only administrators can use this command
    async def send_embed(self, interaction: discord.Interaction, title: str, description: str, mentions: str = "", image: str = None):
        # Prepare the mention text if provided
        mentions_text = ""
        if mentions:
            mentions_list = mentions.split(",")
            mentions_text = " ".join([mention.strip() for mention in mentions_list])

        # Create the embed
        embed = discord.Embed(
            title=title,
            description=description,
            color=discord.Color.blue()
        )

        # Set the image if the URL is provided
        if image:
            embed.set_image(url=image)

        # Send the embed along with mentions in the same message
        await interaction.response.send_message(content=mentions_text, embed=embed)



    @app_commands.command(name="udau", description="Delete a specified number of messages in the channel.")
    @app_commands.describe(
        number="The number of messages to delete"
    )
    @commands.has_permissions(manage_messages=True)  # Only users with "Manage Messages" permission can use this
    async def delete_messages(self, interaction: discord.Interaction, number: int):
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



    @commands.command('bhana')
    async def bhana(self, ctx, *, args):
        # Splits the message into title, content, and mentions
        # Format expected: title | content | @user1 @user2 @user3
        parts = args.split('|', 2)  # Splits into maximum of 3 parts
        
        if len(parts) < 2:
            await ctx.send(f"Please use the format: `{PREFIX[0]}bhana title | content | @mentions`")
            return
            
        title = parts[0].strip()
        content = parts[1].strip()
        
        # Creates the embed
        embed = discord.Embed(title=title,
                            description=content,
                            color=discord.Color.blue())              
        #embed.set_image(url=PHUL_BANNER)
        
        # Check for attachments
        attachments = ctx.message.attachments
        
        # Send the embed
        embed_content = await ctx.send(embed=embed)
        
        # If there are attachments, send them
        if attachments:
            # Send attachments separately using send method for each file
            for attachment in attachments:
                await ctx.send(file=await attachment.to_file())
        
        # If there are mentions (part 3 exists), sends them in a separate message
        if len(parts) == 3:
            mentions = parts[2].strip()
            if mentions:
                await ctx.send(mentions)
        
        # Deletes the original command message
        await ctx.message.delete()
        
        # Add reactions
        reactions = ['✅', '❌', '😊', '☹️']
        for reaction in reactions:
            await embed_content.add_reaction(reaction)


async def setup(bot):
    await bot.add_cog(ModerationCog(bot))

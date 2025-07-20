import discord
from discord.ext import commands
from discord import app_commands
import zipfile
import io
import os

class ZipHandlerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="upload_zip", description="Upload and display contents of a zip file")
    @app_commands.describe(
        zip_file="The zip file to upload and analyze",
        show_content="Whether to show file contents (text files only, max 2000 chars per file)"
    )
    async def upload_zip(
        self, 
        interaction: discord.Interaction, 
        zip_file: discord.Attachment,
        show_content: bool = False
    ):
        # Defer the response as file processing might take time
        await interaction.response.defer()
        
        # Check if the uploaded file is a zip
        if not zip_file.filename.lower().endswith('.zip'):
            await interaction.followup.send("❌ Please upload a valid ZIP file.", ephemeral=True)
            return
        
        # Check file size (Discord limit is 25MB for bots, but let's be conservative)
        if zip_file.size > 20 * 1024 * 1024:  # 20MB limit
            await interaction.followup.send("❌ File too large. Please upload a ZIP file smaller than 20MB.", ephemeral=True)
            return
        
        try:
            # Download the zip file
            zip_data = await zip_file.read()
            
            # Create embed for the response
            embed = discord.Embed(
                title=f"📁 Zip File Analysis: {zip_file.filename}",
                color=0x2F3136,
                timestamp=interaction.created_at
            )
            
            embed.add_field(name="📊 File Size", value=f"{zip_file.size:,} bytes", inline=True)
            
            # Process the zip file
            with zipfile.ZipFile(io.BytesIO(zip_data), 'r') as zip_ref:
                file_list = zip_ref.namelist()
                total_files = len(file_list)
                
                # Get zip file info
                total_uncompressed = sum(info.file_size for info in zip_ref.infolist())
                
                embed.add_field(name="📋 Total Files", value=str(total_files), inline=True)
                embed.add_field(name="📦 Uncompressed Size", value=f"{total_uncompressed:,} bytes", inline=True)
                
                # Create file structure display
                file_structure = []
                directories = set()
                
                for file_path in sorted(file_list):
                    if file_path.endswith('/'):
                        directories.add(file_path)
                        file_structure.append(f"📁 {file_path}")
                    else:
                        # Get file info
                        file_info = zip_ref.getinfo(file_path)
                        size_str = f" ({file_info.file_size:,} bytes)" if file_info.file_size > 0 else ""
                        file_structure.append(f"📄 {file_path}{size_str}")
                
                # Limit the file list display to avoid Discord's embed limits
                max_files_display = 20
                if len(file_structure) > max_files_display:
                    displayed_files = file_structure[:max_files_display]
                    displayed_files.append(f"... and {len(file_structure) - max_files_display} more files")
                else:
                    displayed_files = file_structure
                
                file_list_text = "\n".join(displayed_files)
                if len(file_list_text) > 1024:  # Discord embed field limit
                    file_list_text = file_list_text[:1021] + "..."
                
                embed.add_field(name="📂 Contents", value=f"```\n{file_list_text}\n```", inline=False)
                
                # If user wants to see file contents
                if show_content:
                    content_fields = []
                    text_extensions = {'.txt', '.py', '.js', '.html', '.css', '.json', '.xml', '.md', '.yml', '.yaml', '.ini', '.cfg', '.log'}
                    
                    for file_path in file_list[:5]:  # Limit to first 5 files to avoid spam
                        if not file_path.endswith('/'):  # Skip directories
                            file_ext = os.path.splitext(file_path)[1].lower()
                            
                            if file_ext in text_extensions:
                                try:
                                    with zip_ref.open(file_path) as file:
                                        content = file.read()
                                        
                                        # Try to decode as text
                                        try:
                                            text_content = content.decode('utf-8')
                                        except UnicodeDecodeError:
                                            try:
                                                text_content = content.decode('latin-1')
                                            except UnicodeDecodeError:
                                                continue  # Skip binary files
                                        
                                        # Limit content length
                                        if len(text_content) > 500:
                                            text_content = text_content[:497] + "..."
                                        
                                        content_fields.append({
                                            'name': f"📄 {file_path}",
                                            'value': f"```{file_ext[1:] if file_ext else 'text'}\n{text_content}\n```"
                                        })
                                        
                                except Exception as e:
                                    content_fields.append({
                                        'name': f"❌ {file_path}",
                                        'value': f"Error reading file: {str(e)}"
                                    })
            
            # Send the main embed
            await interaction.followup.send(embed=embed)
            
            # Send content embeds if requested
            if show_content and 'content_fields' in locals():
                for field in content_fields:
                    content_embed = discord.Embed(
                        title=field['name'],
                        description=field['value'],
                        color=0x2F3136
                    )
                    await interaction.followup.send(embed=content_embed)
        
        except zipfile.BadZipFile:
            await interaction.followup.send("❌ The uploaded file is not a valid ZIP archive.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ An error occurred while processing the ZIP file: {str(e)}", ephemeral=True)



async def setup(bot):
    await bot.add_cog(ZipHandlerCog(bot))

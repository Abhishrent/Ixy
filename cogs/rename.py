import discord
from discord.ext import commands
import zipfile
import os
import tempfile
from datetime import datetime

class ZipSorterCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='rename')
    async def sort_zip(self, ctx):
        """
        Command to sort and rename files in a zip archive by creation date.
        Usage: !sortzip (with attached zip file)
        """
        if not ctx.message.attachments:
            await ctx.send("Please attach a zip file!")
            return

        attachment = ctx.message.attachments[0]
        if not attachment.filename.endswith('.zip'):
            await ctx.send("Please attach a ZIP file!")
            return

        # Create temporary directories for processing
        with tempfile.TemporaryDirectory() as temp_dir:
            input_zip_path = os.path.join(temp_dir, 'input.zip')
            output_zip_path = os.path.join(temp_dir, 'sorted.zip')

            # Download the zip file
            await attachment.save(input_zip_path)

            try:
                # Get file information directly from zip
                files = []
                with zipfile.ZipFile(input_zip_path, 'r') as zip_ref:
                    for info in zip_ref.infolist():
                        if not info.filename.endswith('/'):  # Skip directories
                            # Get the file's timestamp from zip info
                            date_time = info.date_time
                            timestamp = datetime(*date_time).timestamp()
                            files.append((timestamp, info.filename))

                # Sort files by timestamp
                files.sort(key=lambda x: x[0])

                # Create new zip with renamed files
                with zipfile.ZipFile(output_zip_path, 'w', zipfile.ZIP_DEFLATED) as output_zip:
                    with zipfile.ZipFile(input_zip_path, 'r') as input_zip:
                        # Add files in sorted order with new names
                        for index, (_, original_filename) in enumerate(files, 1):
                            # Read original file data
                            file_data = input_zip.read(original_filename)
                            
                            # Create new filename with number prefix
                            new_filename = f"{index}.{os.path.basename(original_filename)}"
                            
                            # Write to new zip
                            output_zip.writestr(new_filename, file_data)

                # Send the processed zip file back
                await ctx.send("Here's your sorted and renamed zip file:",
                             file=discord.File(output_zip_path, 'sorted.zip'))

            except zipfile.BadZipFile:
                await ctx.send("The uploaded file appears to be corrupted or not a valid ZIP file.")
            except Exception as e:
                await ctx.send(f"An error occurred: {str(e)}")

async def setup(bot):
    await bot.add_cog(ZipSorterCog(bot))
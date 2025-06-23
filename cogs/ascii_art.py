import discord
from discord.ext import commands
from PIL import Image
import io
import aiohttp
from config import *

class ASCIIArt(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ASCII = ["=", "+", "-", "*", "#", "%", "@", ":", "."]
    
    def resize_img(self, img, new_width=100, correction=2):
        width, height = img.size
        aspect_ratio = width / height
        new_height = int(new_width / (aspect_ratio * correction))
        return img.resize((new_width, new_height))
    
    def get_pixels(self, img):
        grayscale_img = img.convert("L")
        pixels = list(grayscale_img.getdata())
        return pixels
    
    def map_pixels(self, pixels):
        scale_factor = 256 / len(self.ASCII)
        ascii_pixels = [self.ASCII[min(int(x / scale_factor), len(self.ASCII) - 1)] for x in pixels]
        return ascii_pixels
    
    def format_art(self, ascii_pixels, width=100):
        ascii_lines = []
        for i in range(0, len(ascii_pixels), width):
            ascii_lines.append(''.join(ascii_pixels[i:i + width]))
        return "\n".join(ascii_lines)
    
    async def get_image_from_url(self, url):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    return None
                image_data = await response.read()
                return Image.open(io.BytesIO(image_data))
    
    @commands.command(name='ascii')
    async def ascii_art(self, ctx, width: int = 100):
        """
        Convert an attached image to ASCII art and send as a text file
        Usage: !ascii [width]
        Default width is 100 characters
        """
        if not ctx.message.attachments:
            await ctx.send("Please attach an image to convert!")
            return
        
        try:
            # Limit the maximum width to prevent oversized outputs
            width = min(max(width, 20), 150)
            
            # Get the first attachment
            attachment = ctx.message.attachments[0]
            
            # Check if it's an image
            if not attachment.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                await ctx.send("Please attach a valid image file!")
                return
            
            # Download and process the image
            img = await self.get_image_from_url(attachment.url)
            if img is None:
                await ctx.send("Failed to download the image!")
                return
            
            # Process the image
            img = self.resize_img(img, width)
            pixels = self.get_pixels(img)
            ascii_pixels = self.map_pixels(pixels)
            output = self.format_art(ascii_pixels, width)
            
            # Create a file-like object in memory
            file_io = io.StringIO(output)
            
            # Get original filename without extension
            original_name = '.'.join(attachment.filename.split('.')[:-1])
            
            # Create Discord file object
            discord_file = discord.File(
                fp=file_io, 
                filename=f"{original_name}_ascii.txt"
            )
            
            # Create embed with EMBED_THUMBNAIL as thumbnail
            embed = discord.Embed(
                description=(
                    f"Your image has been converted to ASCII art.\n"
                    f"Download the attached `.txt` file to view or share it.\n"
                    f"To convert another image, just attach it and use `{PREFIX[1]}ascii` again."
                ),
                color=discord.Color.blue()
            )
            embed.set_thumbnail(url=EMBED_THUMBNAIL)

            # Send the embed first
            await ctx.send(embed=embed)
            # Then send the file
            await ctx.send(file=discord_file)
            
            # Close the file-like object
            file_io.close()
                
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

async def setup(bot):
    await bot.add_cog(ASCIIArt(bot))
import discord, os
from discord.ext import commands
from googleapiclient.discovery import build
from google.oauth2 import service_account
import json
import random
from config import *

class Drive(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.credentials = self.get_credentials()
        self.drive_service = build('drive', 'v3', credentials=self.credentials)

    def get_credentials(self):
        """Function to load credentials from environment or local file."""
        try:
            # Check if credentials are set as an environment variable
            service_account_info = os.getenv('SERVICE_ACCOUNT_JSON')
            if service_account_info:
                print("Loading credentials from environment variable...")
                credentials_info = json.loads(service_account_info)
                return service_account.Credentials.from_service_account_info(
                    credentials_info, 
                    scopes=SCOPES
                )
            
            # Fall back to loading from a local file
            print("Environment variable not set. Attempting to load from local file...")
            return service_account.Credentials.from_service_account_file(
                SERVICE_ACCOUNT_JSON,  # Path to the local JSON file
                scopes=SCOPES
            )

        except Exception as e:
            raise RuntimeError(f"Failed to load credentials: {e}")

    # Function to retrieve image URLs from the specified folder in Google Drive
    def get_image_urls(self, folder_id):
        results = self.drive_service.files().list(
            q=f"'{folder_id}' in parents and mimeType contains 'image/'",
            fields="files(id, name, owners(displayName))"
        ).execute()
        items = results.get('files', [])
        
        image_infos = []
        for item in items:
            url = f'https://drive.google.com/thumbnail?id={item["id"]}&sz=w1000'
            uploader = item.get("owners", [{}])[0].get("displayName", "Unknown")
            image_infos.append({"url": url, "uploader": uploader})
        
        return image_infos

    # Hybrid command to fetch and display a random image from the specified Google Drive folder
    @commands.hybrid_command(name='photo', description="Fetches a random image from the folder")
    async def randomimage(self, ctx):
        print("Command received")  # Debugging line to confirm command received
        image_infos = self.get_image_urls(FOLDER_ID)
        print("Image URLs retrieved:", image_infos)  # Debugging line to show retrieved URLs
        
        if image_infos:
            image_info = random.choice(image_infos)
            image_url = image_info["url"]
            uploader = image_info["uploader"]
            embed = discord.Embed(title="Here's a Random Photo!", color=discord.Color.blue())
            embed.set_image(url=image_url)
            embed.set_thumbnail(url=EMBED_THUMBNAIL)
            embed.add_field(name="", value=f"[Click here to add your own photos](https://drive.google.com/drive/u/1/folders/{FOLDER_ID})")
            embed.set_footer(text=f'Uploaded by: {uploader}', icon_url=EMBED_FOOTER)
            await ctx.send(embed=embed)
        else:
            await ctx.send("No images found in the folder.")

# Adding the cog to the bot
async def setup(bot):
    await bot.add_cog(Drive(bot))

import discord
from discord.ext import commands, tasks
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
import asyncio
import json
import os

# === CONFIG ===
DRIVE_FOLDER_ID = "1hUa7ScMuhZ1nwZmHwtx8RjfruAFLc2fQ"
CREDENTIALS_FILE = "google_drive.json"
NOTIFY_CHANNEL_ID = 1388895797722091530  # Replace with your channel ID
BOT_MEMORY_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../bot_memory")
NOTIFIED_FILES_PATH = os.path.join(BOT_MEMORY_DIR, "notified_files.json")

def get_drive_service():
    creds = Credentials.from_service_account_file(
        CREDENTIALS_FILE,
        scopes=["https://www.googleapis.com/auth/drive.readonly"]
    )
    return build("drive", "v3", credentials=creds)

def load_notified_file_ids():
    if os.path.exists(NOTIFIED_FILES_PATH):
        try:
            with open(NOTIFIED_FILES_PATH, "r") as f:
                return set(json.load(f))
        except Exception:
            return set()
    return set()

def save_notified_file_ids(file_ids):
    try:
        os.makedirs(BOT_MEMORY_DIR, exist_ok=True)
        with open(NOTIFIED_FILES_PATH, "w") as f:
            json.dump(list(file_ids), f)
    except Exception as e:
        print(f"Failed to save notified file ids: {e}")

class DriveVideoNotify(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.notified_file_ids = load_notified_file_ids()
        self.drive_service = get_drive_service()
        self.check_drive_files.start()  # Renamed for clarity

    @tasks.loop(minutes=2)
    async def check_drive_files(self):
        await self.bot.wait_until_ready()
        try:
            # Query for any files in the folder
            query = (
                f"'{DRIVE_FOLDER_ID}' in parents and trashed = false"
            )
            results = self.drive_service.files().list(
                q=query,
                fields="files(id, name, mimeType, webViewLink, createdTime)"
            ).execute()
            files = results.get("files", [])
            new_files = [f for f in files if f["id"] not in self.notified_file_ids]
            if new_files:
                channel = self.bot.get_channel(NOTIFY_CHANNEL_ID)
                if channel:
                    role_mention = "<@&1388822888043384913> <@&1130181397093548094> <@&1388823285906804777>"
                    note = "Please consider uploading this after reviewing."
                    for file in new_files:
                        # Format createdTime to a prettier format in Nepal time
                        created_time = file.get("createdTime", "Unknown")
                        pretty_time = created_time
                        try:
                            from datetime import datetime
                            import pytz
                            dt = datetime.fromisoformat(created_time.replace("Z", "+00:00"))
                            nepal_tz = pytz.timezone("Asia/Kathmandu")
                            dt_nepal = dt.astimezone(nepal_tz)
                            pretty_time = dt_nepal.strftime("%b %d, %Y at %I:%M %p (Nepal Time)")
                        except Exception:
                            pass
                        embed = discord.Embed(
                            title="New Content Ready for Upload",
                            description=f"[{file['name']}]({file['webViewLink']})",
                            color=discord.Color.blue()
                        )
                        embed.add_field(name="Uploaded At", value=pretty_time, inline=True)
                        await channel.send(content=f"{role_mention}\n{note}", embed=embed)
                        self.notified_file_ids.add(file["id"])
                    save_notified_file_ids(self.notified_file_ids)
        except Exception as e:
            print(f"Drive file notify error: {e}")

    @check_drive_files.before_loop
    async def before_check_drive_files(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(DriveVideoNotify(bot))

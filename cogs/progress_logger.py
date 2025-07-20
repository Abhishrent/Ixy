import discord
from discord.ext import commands, tasks
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pytz
import asyncio
from config import MODLOG_CHANNEL_ID # Replace with your actual MODLOG_CHANNEL_ID

# === Google Sheet Config ===
GOOGLE_SHEET_ID = "1bY5U9Sa_G5_h-fL29VDJanjd7nuZeXBKN9AWPpAWgTw"
CREDENTIALS_FILE = "google_drive.json" # Path to your JSON key

# === Helper function to write to Google Sheet ===
def append_log_to_sheet(log_entry):
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(GOOGLE_SHEET_ID).sheet1
    
    # Add header row if empty
    if sheet.row_count == 0 or sheet.cell(1, 1).value != "Timestamp":
        sheet.insert_row(["Timestamp", "User", "Team Name", "Progress", "Issues"], index=1)
    
    sheet.append_row(log_entry)

# === Discord Modal UI ===
class LogModal(discord.ui.Modal, title="Log Team Progress"):
    team_name = discord.ui.TextInput(label="Team Name", required=True)
    progress = discord.ui.TextInput(label="Today's Progress", style=discord.TextStyle.paragraph, required=True)
    issues = discord.ui.TextInput(label="Issues (if any)", style=discord.TextStyle.paragraph, required=False)
    
    async def on_submit(self, interaction: discord.Interaction):
        # Defer the response immediately to prevent timeout
        await interaction.response.defer(ephemeral=True)
        
        user = interaction.user
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        log_entry = [now, str(user), self.team_name.value, self.progress.value, self.issues.value]
        
        try:
            # Run the sheet operation in a thread pool to avoid blocking
            await asyncio.get_event_loop().run_in_executor(None, append_log_to_sheet, log_entry)
            
            # Send success message using followup instead of response
            await interaction.followup.send("✅ Your progress has been logged!", ephemeral=True)
            
        except Exception as e:
            print(f"Error logging to sheet: {e}")
            await interaction.followup.send("❌ There was an error logging your progress. Please try again.", ephemeral=True)

# === View with Link Button ===
class SheetLinkView(discord.ui.View):
    def __init__(self, sheet_url):
        super().__init__(timeout=None)
        self.add_item(discord.ui.Button(label="View Sheet", url=sheet_url, style=discord.ButtonStyle.link))

# === Main Bot Cog ===
class ProgressLogger(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.send_sheet_link_daily.start()
    
    @commands.hybrid_command(name="log", description="Log your team's progress for today.")
    async def log(self, ctx: commands.Context):
        interaction = getattr(ctx, "interaction", None)
        if interaction:
            await interaction.response.send_modal(LogModal())
        else:
            await ctx.send("⚠️ Please use this command as a slash command in Discord.", ephemeral=True)
    
    @tasks.loop(minutes=1)
    async def send_sheet_link_daily(self):
        tz = pytz.timezone("Asia/Kathmandu")
        now = datetime.now(tz)
        
        if now.hour == 20 and now.minute == 0:
            channel = self.bot.get_channel(MODLOG_CHANNEL_ID)
            if channel:
                sheet_link = f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}"
                
                # Create embed and button
                embed = discord.Embed(title="📋 Daily Progress Log", color=discord.Color.blue())
                view = SheetLinkView(sheet_link)
                
                await channel.send(embed=embed, view=view)
    
    @send_sheet_link_daily.before_loop
    async def before_send_sheet(self):
        await self.bot.wait_until_ready()

# === Setup ===
async def setup(bot):
    await bot.add_cog(ProgressLogger(bot))
import discord
from discord.ext import commands
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os

GOOGLE_CREDS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../google_drive.json')
SCOPES = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]
SHEET_NAME = 'MBM IdeaX 2025 Registration Form (Responses)'  # <-- Change this to your actual sheet name
EMAIL_COLUMN = 'Email Address'  # <-- Change this to the exact column name in your sheet

class CheckRegistrationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sheet = None
        self._init_sheet()

    def _init_sheet(self):
        creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_CREDS_FILE, SCOPES)
        gc = gspread.authorize(creds)
        self.sheet = gc.open(SHEET_NAME).sheet1  # or .worksheet('Sheet1')

    @commands.hybrid_command(name="check_registration", description="Check if your email is registered via Google Forms.")
    async def check_registration(self, ctx, email: str):
        """Check if an email is registered in the Google Sheet (checks all team member email columns)."""
        EMAIL_COLUMNS = [
            "Email Address",
            "Team Member 2 Email Address:",
            "Team Member 3 Email Address:",
            "Team Member 4 Email Address:"
        ]
        # Determine if this is a ticket channel
        is_ticket_channel = ctx.channel and ctx.channel.name.startswith("ticket-")
        await ctx.defer(ephemeral=not is_ticket_channel)
        try:
            if not self.sheet:
                self._init_sheet()
            header_row = self.sheet.row_values(1)
            found = False
            for col_name in EMAIL_COLUMNS:
                try:
                    col_index = header_row.index(col_name) + 1
                except ValueError:
                    continue  # Skip if column not found
                email_values = [v.strip().lower() for v in self.sheet.col_values(col_index)[1:]]
                if email.strip().lower() in email_values:
                    found = True
                    break
            if found:
                result_embed = discord.Embed(
                    title="Registration Found! ✅",
                    description=f"Registration found for `{email}`.",
                    color=discord.Color.green()
                )
            else:
                result_embed = discord.Embed(
                    title="Registration Not Found ❌",
                    description=f"No registration found for `{email}`.",
                    color=discord.Color.red()
                )
            await ctx.reply(embed=result_embed, ephemeral=not is_ticket_channel)
        except Exception as e:
            error_embed = discord.Embed(
                title="Error",
                description=f"Error checking registration: {e}",
                color=discord.Color.red()
            )
            await ctx.reply(embed=error_embed, ephemeral=not is_ticket_channel)

async def setup(bot):
    await bot.add_cog(CheckRegistrationCog(bot))

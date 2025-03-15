import discord
import re
import calendar
from datetime import datetime
from discord.ext import commands
from discord.ui import Button, View
from config import *  # Make sure SPECIAL_DATES and IDEAX_LOGO are imported from config.py

class Calendar(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name='calendar', description='Show calendar for a specific month and year')
    @discord.app_commands.describe(month='Month number (1-12)', year='Year')
    async def show_calendar(self, ctx, month: int = None, year: int = None):
        # Default to current month and year if not provided
        now = datetime.now()
        month = month or now.month
        year = year or now.year
        await self.send_calendar_embed(ctx, month, year)

    # Helper function to generate and send the calendar embed with buttons
    async def send_calendar_embed(self, ctx_or_interaction, month, year, edit=False):
        now = datetime.now()
        today = now.date()

        # Validate month and year inputs
        if month < 1 or month > 12:
            await ctx_or_interaction.send("Invalid month. Please use a number between 1 and 12.", ephemeral=True)
            return

        # Generate the calendar for the specified month and year, starting with Sunday
        cal = calendar.TextCalendar(firstweekday=6)  # 6 means Sunday
        calendar_text = cal.formatmonth(year, month)

        # Split the calendar text into header (title and days of week) and body (dates grid)
        calendar_lines = calendar_text.splitlines()
        header = "\n".join(calendar_lines[:2])  # The first two lines (title and weekdays)
        dates_grid = calendar_lines[2:]  # The remaining lines (the calendar dates)

        # Process each line in the dates grid to mark special dates
        marked_dates_grid = []
        for line in dates_grid:
            # Replace today's date with 🔹 and special dates with 🔸
            for (special_month, special_day), description in SPECIAL_DATES.items():
                if month == special_month:
                    pattern = r'(\s)' + f"{special_day:2}".strip() + r'(\s|$)'
                    line = re.sub(pattern, r'\1🔸\2', line)

            # Check if today's date is in the current line, and replace it with 🔹
            if month == today.month and year == today.year:
                pattern = r'(\s)' + f"{today.day:2}".strip() + r'(\s|$)'
                line = re.sub(pattern, r'\1🔹\2', line)

            marked_dates_grid.append(line)

        # Reconstruct the full calendar with header and marked dates grid
        marked_calendar_text = f"{header}\n" + "\n".join(marked_dates_grid)

        # Create the embed
        embed = discord.Embed(
            title=f"Calendar for {calendar.month_name[month]} {year}",
            description=f"```{marked_calendar_text}```",
            color=discord.Color.blue()
        )

        # Add fields for each special date with descriptions and days remaining
        for (special_month, special_day), description in SPECIAL_DATES.items():
            if month == special_month:
                event_date = datetime(year, special_month, special_day).date()
                days_remaining = (event_date - today).days

                # Adjust the message for past events
                if days_remaining > 0:
                    countdown_text = f"{days_remaining} day(s) remaining"
                elif days_remaining == 0:
                    countdown_text = "Today!"
                else:
                    countdown_text = "Event has passed"

                embed.add_field(
                    name=f"{special_day} {calendar.month_name[special_month]}",
                    value=f"{description} - {countdown_text}",
                    inline=False
                )

        embed.set_footer(text='🔹- Today \n🔸- Special Event')

        # Set up the buttons
        prev_button = Button(label="◀ Previous Month", style=discord.ButtonStyle.primary)
        next_button = Button(label="Next Month ▶", style=discord.ButtonStyle.primary)

        # Define button callbacks to update month and year
        async def prev_callback(interaction):
            nonlocal month, year
            month -= 1
            if month < 1:
                month = 12
                year -= 1
            await interaction.response.defer()  # Prevent "Interaction failed" message
            await self.send_calendar_embed(interaction, month, year, edit=True)

        async def next_callback(interaction):
            nonlocal month, year
            month += 1
            if month > 12:
                month = 1
                year += 1
            await interaction.response.defer()  # Prevent "Interaction failed" message
            await self.send_calendar_embed(interaction, month, year, edit=True)

        # Assign callbacks to buttons
        prev_button.callback = prev_callback
        next_button.callback = next_callback

        # Create the view and add buttons
        view = View()
        view.add_item(prev_button)
        view.add_item(next_button)

        # Decide whether to edit the message or send a new one
        if edit:
            await ctx_or_interaction.edit_original_response(embed=embed, view=view)
        else:
            await ctx_or_interaction.send(embed=embed, view=view)

    @commands.hybrid_command(name='events', description='List upcoming events')
    async def list_events(self, ctx):
        now = datetime.now().date()
        upcoming_events = []

        # Iterate through SPECIAL_DATES to collect upcoming events
        for (month, day), description in SPECIAL_DATES.items():
            event_date = datetime(now.year, month, day).date()

            # Check if the event date is in the future or today
            days_remaining = (event_date - now).days
            if days_remaining >= 0:
                countdown_text = (
                    f"{days_remaining} day(s) remaining" if days_remaining > 0 else "Today!"
                )
                upcoming_events.append((event_date, description, countdown_text))

        # Sort events by date
        upcoming_events.sort()

        # Prepare the embed
        embed = discord.Embed(
            title="Upcoming Events",
            color=discord.Color.blue()
        )

        if not upcoming_events:
            embed.description = "No upcoming events found."
        else:
            for event_date, description, countdown in upcoming_events:
                embed.add_field(
                    name=f"{event_date.strftime('%d %B')}",
                    value=f"{description} - {countdown}",
                    inline=False
                )

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Calendar(bot))
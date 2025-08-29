import discord
from discord.ext import commands, tasks
from discord import app_commands, Interaction
import pytz
from datetime import datetime, time, timedelta
from config import ATTENDANCE_CHANNEL_ID

class AttendanceView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(label="Mark Attendance", style=discord.ButtonStyle.success, custom_id="attendance_button")
    async def mark_attendance(self, interaction: Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        if user_id not in self.cog.attendance_today:
            # Store (display_name, time_str)
            now = datetime.now(pytz.timezone("Asia/Kathmandu"))
            time_str = now.strftime("%H:%M")
            self.cog.attendance_today[user_id] = (interaction.user.display_name, time_str)
            # Check if already responded
            if not interaction.response.is_done():
                await interaction.response.send_message("Attendance marked!", ephemeral=True)
            else:
                await interaction.followup.send("Attendance marked!", ephemeral=True)
        else:
            if not interaction.response.is_done():
                await interaction.response.send_message("You have already marked your attendance today.", ephemeral=True)
            else:
                await interaction.followup.send("You have already marked your attendance today.", ephemeral=True)

    @discord.ui.button(label="View Attendance", style=discord.ButtonStyle.primary, custom_id="view_attendance_button")
    async def view_attendance_button(self, interaction: Interaction, button: discord.ui.Button):
        guild = interaction.guild
        role_id = 1130051976189722680
        role = guild.get_role(role_id) if guild else None

        # Prepare attendees with times
        attendees = [
            f"{name} (`{time_str}`)"
            for (name, time_str) in self.cog.attendance_today.values()
        ]
        attendees_display = "\n".join(attendees) if attendees else "No one has marked attendance today."

        absentees_display = "N/A"
        if role:
            absentees = [
                member.display_name
                for member in role.members
                if member.id not in self.cog.attendance_today
            ]
            absentees_display = "\n".join(absentees) if absentees else "None! Everyone marked attendance."

        embed = discord.Embed(
            title="Today's Attendance",
            color=discord.Color.green()
        )
        embed.add_field(name="✅ Present", value=attendees_display, inline=False)
        embed.add_field(name="❌ Absent", value=absentees_display, inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

class AttendanceCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.attendance_today = {}  # user_id: (display_name, time_str)
        self.last_attendance_message_id = None
        self.summary_sent_today = False  # Track if summary was already sent today
        self.bot.loop.create_task(self.setup_view())
        self.reset_attendance_daily.start()
        self.attendance_summary.start()  # Start the summary task here

    async def setup_view(self):
        await self.bot.wait_until_ready()
        self.bot.add_view(AttendanceView(self))

    async def ensure_attendance_embed(self, channel):
        # Delete previous attendance message if it exists
        if self.last_attendance_message_id:
            try:
                prev_msg = await channel.fetch_message(self.last_attendance_message_id)
                await prev_msg.delete()
            except discord.NotFound:
                pass  # Message already deleted
        
        # Send new attendance embed
        embed = discord.Embed(
            title="Attendance",
            description="Click the button below to mark your attendance for today!",
            color=discord.Color.green()
        )
        sent_msg = await channel.send(embed=embed, view=AttendanceView(self))
        self.last_attendance_message_id = sent_msg.id

    @tasks.loop(hours=24)
    async def reset_attendance_daily(self):
        await self.bot.wait_until_ready()
        now = datetime.now(pytz.timezone("Asia/Kathmandu"))
        target = now.replace(hour=0, minute=0, second=0, microsecond=0)
        if now > target:
            target += timedelta(days=1)
        await discord.utils.sleep_until(target)
        self.attendance_today = {}
        self.summary_sent_today = False  # Reset the summary flag

    @tasks.loop(minutes=1)
    async def attendance_summary(self):
        await self.bot.wait_until_ready()
        now = datetime.now(pytz.timezone("Asia/Kathmandu"))
        
        # Check if it's 10 PM and we haven't sent the summary today
        if now.hour == 22 and now.minute == 0 and not self.summary_sent_today:
            channel = self.bot.get_channel(1390954199591813121)  # manager channel id
            if channel:
                guild = channel.guild
                role_id = 1130051976189722680
                role = guild.get_role(role_id) if guild else None

                attendees = [
                    f"{name} (`{time_str}`)"
                    for (name, time_str) in self.attendance_today.values()
                ]
                attendees_display = "\n".join(attendees) if attendees else "No one has marked attendance today."

                absentees_display = "N/A"
                if role:
                    absentees = [
                        member.display_name
                        for member in role.members
                        if member.id not in self.attendance_today
                    ]
                    absentees_display = "\n".join(absentees) if absentees else "None! Everyone marked attendance."

                embed = discord.Embed(
                    title="Today's Attendance Summary",
                    color=discord.Color.blue() if attendees else discord.Color.red()
                )
                embed.add_field(name="✅ Present", value=attendees_display, inline=False)
                embed.add_field(name="❌ Absent", value=absentees_display, inline=False)
                
                # Add timestamp to the embed
                embed.set_footer(text=f"Report generated at {now.strftime('%Y-%m-%d %H:%M:%S')} NPT")
                
                await channel.send(embed=embed)
                self.summary_sent_today = True  # Mark as sent for today

    @reset_attendance_daily.before_loop
    async def before_reset_attendance_daily(self):
        await self.bot.wait_until_ready()

    @attendance_summary.before_loop
    async def before_attendance_summary(self):
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        if message.channel.id != ATTENDANCE_CHANNEL_ID:
            return
        
        # Re-send the attendance embed to keep it as the latest message
        await self.ensure_attendance_embed(message.channel)

    @commands.Cog.listener()
    async def on_ready(self):
        # Send initial attendance embed when bot starts
        await self.bot.wait_until_ready()
        channel = self.bot.get_channel(ATTENDANCE_CHANNEL_ID)
        if channel:
            await self.ensure_attendance_embed(channel)

async def setup(bot):
    await bot.add_cog(AttendanceCog(bot))
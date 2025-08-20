import discord
from discord.ext import commands, tasks
import pytz
from datetime import datetime, timedelta
import os
import json

ATTENDANCE_CHANNEL_ID = 1393576065427046621
MANAGER_CHANNEL_ID = 1390954199591813121
ROLE_ID = 1130051976189722680
ATTENDANCE_KEYWORD = "jay"  # Users must reply with this word (case-insensitive)

BOT_MEMORY_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../bot_memory")
ATTENDANCE_FILE = os.path.join(BOT_MEMORY_DIR, "attendance.json")

def save_attendance_today(attendance_today):
    os.makedirs(BOT_MEMORY_DIR, exist_ok=True)
    with open(ATTENDANCE_FILE, "w") as f:
        json.dump(attendance_today, f, indent=2)

def load_attendance_today():
    if os.path.exists(ATTENDANCE_FILE):
        try:
            with open(ATTENDANCE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

class AttendanceCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # user_id: {"display_name": str, "time_str": str, "count": int}
        self.attendance_today = load_attendance_today()
        self.last_attendance_message_id = None
        self.summary_sent_today = False
        self.reset_attendance_daily.start()
        self.attendance_summary.start()
        self.send_attendance_prompt.start()

    @tasks.loop(hours=2)
    async def send_attendance_prompt(self):
        await self.bot.wait_until_ready()
        now = datetime.now(pytz.timezone("Asia/Kathmandu"))
        if 22 <= now.hour or now.hour < 5:
            return  # Skip sending prompt between 10pm and 5am
        channel = self.bot.get_channel(ATTENDANCE_CHANNEL_ID)
        guild = channel.guild if channel else None
        role = guild.get_role(ROLE_ID) if guild else None
        if channel and role:
            msg = await channel.send(
                f"{role.mention} Shree Krishna bhagwan ko..."
            )
            self.last_attendance_message_id = msg.id

    @tasks.loop(hours=24)
    async def reset_attendance_daily(self):
        await self.bot.wait_until_ready()
        now = datetime.now(pytz.timezone("Asia/Kathmandu"))
        target = now.replace(hour=0, minute=0, second=0, microsecond=0)
        if now > target:
            target += timedelta(days=1)
        await discord.utils.sleep_until(target)
        self.attendance_today = {}
        save_attendance_today(self.attendance_today)
        self.summary_sent_today = False

    @tasks.loop(minutes=1)
    async def attendance_summary(self):
        await self.bot.wait_until_ready()
        now = datetime.now(pytz.timezone("Asia/Kathmandu"))
        if now.hour == 22 and now.minute == 0 and not self.summary_sent_today:
            channel = self.bot.get_channel(MANAGER_CHANNEL_ID)
            guild = channel.guild if channel else None
            role = guild.get_role(ROLE_ID) if guild else None
            if channel and role:
                attendees = [
                    f"{data['display_name']} (`{data['time_str']}`)"
                    for data in self.attendance_today.values()
                ]
                attendees_display = "\n".join(attendees) if attendees else "No one has marked attendance today."

                absentees_display = "N/A"
                if role:
                    absentees = [
                        member.display_name
                        for member in role.members
                        if str(member.id) not in self.attendance_today
                    ]
                    absentees_display = "\n".join(absentees) if absentees else "None! Everyone marked attendance."

                embed = discord.Embed(
                    title="Today's Attendance Summary",
                    color=discord.Color.blue() if attendees else discord.Color.red()
                )
                embed.add_field(name="✅ Present", value=attendees_display, inline=False)
                embed.add_field(name="❌ Absent", value=absentees_display, inline=False)
                embed.set_footer(text=f"Report generated at {now.strftime('%Y-%m-%d %H:%M:%S')} NPT")
                await channel.send(embed=embed)

                # Divine message for top jay count
                attendance_channel = self.bot.get_channel(ATTENDANCE_CHANNEL_ID)
                if attendance_channel and self.attendance_today:
                    max_count = max(data.get("count", 1) for data in self.attendance_today.values())
                    top_users = [
                        data["display_name"]
                        for data in self.attendance_today.values()
                        if data.get("count", 1) == max_count
                    ]
                    if top_users:
                        top_mentions = ", ".join(f"**{name}**" for name in top_users)
                        divine_msg = (
                            f"🌺 {top_mentions} chanted 'jay' {max_count} times today!\n"
                            "✨ By the grace of Lord Krishna, your devotion shines the brightest today! ✨\n"
                            "जय श्री कृष्णा! 🙏"
                        )
                        await attendance_channel.send(divine_msg)
                self.summary_sent_today = True
        elif now.hour != 22 or now.minute != 0:
            self.summary_sent_today = False  # Reset flag for next day

    @send_attendance_prompt.before_loop
    async def before_send_attendance_prompt(self):
        await self.bot.wait_until_ready()
        # Removed wait-until-midnight logic so the first prompt is sent immediately

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
        if ATTENDANCE_KEYWORD in message.content.lower():
            user_id = str(message.author.id)
            now = datetime.now(pytz.timezone("Asia/Kathmandu"))
            time_str = now.strftime("%H:%M")
            # Initialize user attendance if not present
            if user_id not in self.attendance_today:
                self.attendance_today[user_id] = {
                    "display_name": message.author.display_name,
                    "time_str": time_str,
                    "count": 1
                }
                save_attendance_today(self.attendance_today)
                try:
                    await message.add_reaction("🕉️")
                except Exception:
                    pass
            else:
                # Increment jay count
                self.attendance_today[user_id]["count"] += 1
                save_attendance_today(self.attendance_today)
                user_count = self.attendance_today[user_id]["count"]
                await message.reply(
                    f"You have chanted 'jay' {user_count} times today.",
                    mention_author=False,
                    delete_after=5
                )

    @commands.Cog.listener()
    async def on_ready(self):
        await self.bot.wait_until_ready()
        channel = self.bot.get_channel(ATTENDANCE_CHANNEL_ID)
        guild = channel.guild if channel else None
        role = guild.get_role(ROLE_ID) if guild else None
        if channel and role and not self.last_attendance_message_id:
            msg = await channel.send(
                f"{role.mention} Please reply to this message with **{ATTENDANCE_KEYWORD}** to mark your attendance for today!"
            )
            self.last_attendance_message_id = msg.id

async def setup(bot):
    await bot.add_cog(AttendanceCog(bot))
import discord
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta, timezone
from config import EMBED_THUMBNAIL

# Configuration - Replace with your actual bug report channel ID
BUG_REPORT_CHANNEL_ID = 1409002396180418593  # Replace with actual channel ID

# File to store bug reports persistently
BOT_MEMORY_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../bot_memory")
BUG_REPORTS_FILE = os.path.join(BOT_MEMORY_DIR, "bug_reports.json")

def load_bug_reports():
    """Load bug reports from file"""
    if os.path.exists(BUG_REPORTS_FILE):
        try:
            with open(BUG_REPORTS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {"reports": [], "message_id": None}
    return {"reports": [], "message_id": None}

def save_bug_reports(data):
    """Save bug reports to file"""
    os.makedirs(BOT_MEMORY_DIR, exist_ok=True)
    with open(BUG_REPORTS_FILE, "w") as f:
        json.dump(data, f, indent=2)

class BugReportTracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data = load_bug_reports()
        self.bug_embed_message = None

    async def get_or_create_embed_message(self, channel):
        """Get existing embed message or create a new one"""
        if self.data.get("message_id"):
            try:
                message = await channel.fetch_message(self.data["message_id"])
                self.bug_embed_message = message
                return message
            except discord.NotFound:
                # Message was deleted, create a new one
                pass
        
        # Create new embed message
        embed = self.create_bug_embed()
        message = await channel.send(embed=embed)
        self.bug_embed_message = message
        self.data["message_id"] = message.id
        save_bug_reports(self.data)
        return message

    def create_bug_embed(self):
        """Create the bug report embed"""
        embed = discord.Embed(
            title="🐛 Bug Reports Tracker",
            description="All reported bugs are tracked below:",
            color=discord.Color.red()
        )
        
        embed.set_thumbnail(url=EMBED_THUMBNAIL)
        
        reports = self.data.get("reports", [])
        if not reports:
            embed.add_field(
                name="📝 Current Reports",
                value="```\nNo bug reports yet.\n```",
                inline=False
            )
        else:
            # Group reports into chunks to avoid embed limits
            report_text = ""
            for i, report in enumerate(reports[-20:], 1):  # Show last 20 reports
                timestamp = report.get("timestamp", "Unknown time")
                username = report.get("username", "Unknown user")
                content = report.get("content", "No content")
                status = report.get("status", "open")
                bug_id = report.get("id", i)
                
                # Status emoji mapping
                status_emoji = {
                    "open": "🟡",
                    "review": "🔍",
                    "fixed": "✅",
                    "closed": "❌"
                }
                emoji = status_emoji.get(status, "🟡")
                
                report_line = f"{emoji} #{bug_id} [{timestamp}] {username}: {content}\n"
                if len(report_text + report_line) > 1000:  # Discord code block limit
                    break
                report_text += report_line
            
            if not report_text:
                report_text = "No recent reports to display.\n"
            
            embed.add_field(
                name="📝 Recent Bug Reports",
                value=f"```\n{report_text}```",
                inline=False
            )
            
            embed.set_footer(text=f"Total reports: {len(reports)} | Showing last {min(20, len(reports))}\n🟡 Open\n🔍 Under Review\n✅ Fixed\n❌ Closed")
        
        embed.timestamp = discord.utils.utcnow()
        return embed

    @commands.Cog.listener()
    async def on_message(self, message):
        """Handle incoming messages in the bug report channel"""
        # Ignore bot messages
        if message.author.bot:
            return
        
        # Only process messages in the bug report channel
        if message.channel.id != BUG_REPORT_CHANNEL_ID:
            return
        
        # Add the bug report to our data
        nepal_tz = timezone(timedelta(hours=5, minutes=45))
        timestamp = datetime.now(nepal_tz).strftime("%Y-%m-%d %H:%M")
        # Generate unique ID for the bug report
        bug_id = len(self.data.get("reports", [])) + 1
        bug_report = {
            "id": bug_id,
            "timestamp": timestamp,
            "username": message.author.display_name,
            "user_id": str(message.author.id),
            "content": message.content[:500],  # Limit content length
            "status": "open"  # open, review, fixed, closed
        }
        
        self.data["reports"].append(bug_report)
        
        # Keep only last 100 reports to prevent file from growing too large
        if len(self.data["reports"]) > 100:
            self.data["reports"] = self.data["reports"][-100:]
        
        save_bug_reports(self.data)

        # DM the user confirming bug registration
        try:
            status_text = {
                "open": "🟡 Open"
            }
            embed = discord.Embed(
                title="Bug Report Received",
                color=discord.Color.green()
            )
            embed.add_field(name="Bug ID", value=str(bug_id), inline=True)
            embed.add_field(name="Status", value=status_text["open"], inline=True)
            embed.add_field(name="Details", value="Your bug report has been received and will be reviewed by the team.", inline=False)
            await message.author.send(embed=embed)
        except Exception as e:
            print(f"Failed to DM user {message.author.id}: {e}")

        # Delete the user's message
        try:
            await message.delete()
        except discord.Forbidden:
            pass  # Bot doesn't have permission to delete messages
        except discord.NotFound:
            pass  # Message already deleted

        # Update the embed
        await self.update_embed(message.channel)

    async def update_embed(self, channel):
        """Update the bug report embed"""
        try:
            embed_message = await self.get_or_create_embed_message(channel)
            new_embed = self.create_bug_embed()
            await embed_message.edit(embed=new_embed)
        except Exception as e:
            print(f"Error updating bug report embed: {e}")

    @commands.Cog.listener()
    async def on_ready(self):
        """Initialize the embed when bot is ready"""
        await self.bot.wait_until_ready()
        channel = self.bot.get_channel(BUG_REPORT_CHANNEL_ID)
        if channel:
            await self.get_or_create_embed_message(channel)

    @commands.hybrid_command(name="clear_bugs", with_app_command=True)
    @commands.has_permissions(manage_messages=True)
    async def clear_bugs(self, ctx):
        """Clear all bug reports (Admin only)"""
        if ctx.channel.id != BUG_REPORT_CHANNEL_ID:
            await ctx.send("❌ This command can only be used in the bug report channel.", ephemeral=True)
            return
        
        self.data["reports"] = []
        save_bug_reports(self.data)
        
        # Update the embed
        await self.update_embed(ctx.channel)
        await ctx.send("✅ All bug reports have been cleared.", ephemeral=True)

    @commands.hybrid_command(name="export_bugs", with_app_command=True)
    @commands.has_permissions(manage_messages=True)
    async def export_bugs(self, ctx):
        """Export all bug reports to a text file (Admin only)"""
        reports = self.data.get("reports", [])
        if not reports:
            await ctx.send("❌ No bug reports to export.", ephemeral=True)
            return
        
        # Create text file content
        content = "Bug Reports Export\n"
        content += "=" * 50 + "\n\n"
        
        for i, report in enumerate(reports, 1):
            content += f"Report #{i}\n"
            content += f"Time: {report.get('timestamp', 'Unknown')}\n"
            content += f"User: {report.get('username', 'Unknown')} (ID: {report.get('user_id', 'Unknown')})\n"
            content += f"Content: {report.get('content', 'No content')}\n"
            content += "-" * 30 + "\n\n"
        
        # Create file and send
        file_content = content.encode('utf-8')
        file = discord.File(
            fp=__import__('io').BytesIO(file_content),
            filename=f"bug_reports_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )
        
        await ctx.send("📁 Bug reports exported:", file=file, ephemeral=True)

    @commands.hybrid_command(name="bug_status", with_app_command=True)
    @commands.has_permissions(manage_messages=True)
    async def update_bug_status(self, ctx, bug_id: int, status: str, developer_message: str = None):
        """Update the status of a bug report (Admin only)
        
        Args:
            bug_id: The ID number of the bug report
            status: New status (open, review, fixed, closed)
        """
        valid_statuses = ["open", "review", "fixed", "closed"]
        if status.lower() not in valid_statuses:
            await ctx.send(f"❌ Invalid status. Valid options: {', '.join(valid_statuses)}", ephemeral=True)
            return
        
        reports = self.data.get("reports", [])
        bug_found = False
        
        for report in reports:
            if report.get("id") == bug_id:
                old_status = report.get("status", "open")
                report["status"] = status.lower()
                bug_found = True
                
                # DM the user who reported the bug
                user_id = report.get("user_id")
                try:
                    user = await self.bot.fetch_user(int(user_id))
                    status_text = {
                        "open": "🟡 Open",
                        "review": "🔍 Under Review",
                        "fixed": "✅ Fixed",
                        "closed": "❌ Closed"
                    }
                    status_expl = {
                        "open": "Your reported bug is now open and will be reviewed soon.",
                        "review": "Your reported bug is under review by the team.",
                        "fixed": "Your reported bug has been marked as fixed.",
                        "closed": "Your reported bug has been closed."
                    }
                    embed = discord.Embed(
                        title="Your Bug Report Status Updated",
                        color=discord.Color.orange()
                    )
                    embed.add_field(name="Bug ID", value=str(bug_id), inline=True)
                    embed.add_field(name="New Status", value=status_text.get(status.lower(), status), inline=True)
                    embed.add_field(name="Details", value=status_expl.get(status.lower(), "Status updated."), inline=False)
                    if developer_message:
                        embed.add_field(name="Message from Developer", value=developer_message, inline=False)
                    await user.send(embed=embed)
                except Exception as e:
                    print(f"Failed to DM user {user_id}: {e}")
                break
        
        if not bug_found:
            await ctx.send(f"❌ Bug report #{bug_id} not found.", ephemeral=True)
            return
        
        save_bug_reports(self.data)
        
        # Update the embed if we're in the bug report channel
        if ctx.channel.id == BUG_REPORT_CHANNEL_ID:
            await self.update_embed(ctx.channel)
        
        status_text = {
            "open": "🟡 Open",
            "review": "🔍 Under Review", 
            "fixed": "✅ Fixed",
            "closed": "❌ Closed"
        }
        
        await ctx.send(
            f"✅ Bug report #{bug_id} status updated to: {status_text.get(status.lower(), status)}", 
            ephemeral=True
        )

    @commands.hybrid_command(name="bug_info", with_app_command=True)
    async def bug_info(self, ctx, bug_id: int):
        """Get detailed information about a specific bug report"""
        reports = self.data.get("reports", [])
        bug_report = None
        
        for report in reports:
            if report.get("id") == bug_id:
                bug_report = report
                break
        
        if not bug_report:
            await ctx.send(f"❌ Bug report #{bug_id} not found.", ephemeral=True)
            return
        
        status_text = {
            "open": "🟡 Open",
            "review": "🔍 Under Review", 
            "fixed": "✅ Fixed",
            "closed": "❌ Closed"
        }
        
        embed = discord.Embed(
            title=f"🐛 Bug Report #{bug_id}",
            color=discord.Color.orange()
        )
        embed.set_thumbnail(url=EMBED_THUMBNAIL)
        embed.add_field(name="Status", value=status_text.get(bug_report.get("status", "open"), "Unknown"), inline=True)
        embed.add_field(name="Reported By", value=bug_report.get("username", "Unknown"), inline=True)
        embed.add_field(name="Timestamp", value=bug_report.get("timestamp", "Unknown"), inline=True)
        embed.add_field(name="Description", value=f"```{bug_report.get('content', 'No description')}```", inline=False)
        
        await ctx.send(embed=embed, ephemeral=True)

    @commands.hybrid_command(name="bug_list", with_app_command=True)
    async def bug_list(self, ctx, status: str = None):
        """List bug reports by status (Admin only)
        
        Args:
            status: Filter by status (open, review, fixed, closed). Leave empty for all.
        """
        if not ctx.author.guild_permissions.manage_messages:
            await ctx.send("❌ You don't have permission to use this command.", ephemeral=True)
            return
        
        reports = self.data.get("reports", [])
        
        if status:
            if status.lower() not in ["open", "review", "fixed", "closed"]:
                await ctx.send("❌ Invalid status. Valid options: open, review, fixed, closed", ephemeral=True)
                return
            filtered_reports = [r for r in reports if r.get("status", "open") == status.lower()]
        else:
            filtered_reports = reports
        
        if not filtered_reports:
            status_msg = f" with status '{status}'" if status else ""
            await ctx.send(f"No bug reports found{status_msg}.", ephemeral=True)
            return
        
        # Group by status
        status_groups = {
            "open": [],
            "review": [],
            "fixed": [],
            "closed": []
        }
        
        for report in filtered_reports[-20:]:  # Last 20 reports
            report_status = report.get("status", "open")
            status_groups[report_status].append(report)
        
        embed = discord.Embed(
            title="🐛 Bug Reports List",
            color=discord.Color.blue()
        )
        
        status_emojis = {
            "open": "🟡",
            "review": "🔍",
            "fixed": "✅",
            "closed": "❌"
        }
        
        for status_key, reports_list in status_groups.items():
            if reports_list:
                report_lines = []
                for report in reports_list:
                    bug_id = report.get("id", "?")
                    username = report.get("username", "Unknown")[:15]  # Truncate long names
                    content = report.get("content", "No description")[:50]  # Truncate long content
                    if len(content) == 50:
                        content += "..."
                    report_lines.append(f"#{bug_id} {username}: {content}")
                
                if report_lines:
                    embed.add_field(
                        name=f"{status_emojis[status_key]} {status_key.title()} ({len(report_lines)})",
                        value="```\n" + "\n".join(report_lines) + "```",
                        inline=False
                    )
        
        await ctx.send(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(BugReportTracker(bot))
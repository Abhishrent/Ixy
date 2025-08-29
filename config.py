import os

# General Bot Configuration
BOT_NAME = 'Ixy'  # Name of the bot
PREFIX = ('ixy ', 'Ixy ')  # Command prefixes for the bot

# Special Dates for Event Scheduling
SPECIAL_DATES = {
    (7, 21): "ML Workshop Starts",
    (8, 1): "ML Workshop Finishes",
    (8, 10): "Internal Ideathon Reg. Starts",
    (8, 26): "Internal Ideathon Reg. Closes",
    (8, 29): "Internal Ideathon",
    (9, 6): "IdeaX Registration Closes",
    (9, 11): "IdeaX Online Round Day 1",
    (9, 12): "IdeaX Online Round Day 2",
    (9, 13): "IdeaX Online Round Day 3",
    (9, 14): "IdeaX Online Round Day 4",
    (9, 15): "IdeaX Online Round Day 5",
    (9, 16): "IdeaX Online Round Day 6",
    (10, 31): "IdeaX Final Hackathon Day 1",
    (11, 1): "IdeaX Final Hackathon Day 2",
    (11, 2): "IdeaX Final Hackathon Day 3",
}

# Discord Channel IDs
# These IDs are used to identify specific channels in the server

# General Channels
WELCOME_CHANNEL_ID = 1130051976667865090  # Channel for welcoming new members (Used in cogs/greeter.py)
GENERAL_CHANNEL_ID = 1295939872581750839  # General discussion channel (Used in main.py)
HELP_CHANNEL_ID = 1388896467594510437  # Channel for help and support (Used in cogs/help.py)

# Moderation and Logs
MODLOG_CHANNEL_ID = 1130051976667865097  # Channel for moderation logs (Used in cogs/progress_logger.py)
LOG_CHANNEL_ID = 1408799166267920455  # Channel for logging bot activities (Used in cogs/logs.py)

# Announcements and Updates
ANNOUNCE_INPUT_CHANNEL_ID = 1406952251695566908  # Channel for inputting announcements (Used in cogs/announcement_sender.py)
ANNOUNCE_OUTPUT_CHANNEL_ID = 1130103633141317643  # Channel for posting announcements (Used in cogs/announcement_sender.py)
IMAGE_UPLOAD_CHANNEL_ID = 1410834897584783380  # Channel for storing images (Used in cogs/announcement_sender.py, cogs/dm_sender.py)

# Direct Messages
DM_CHANNEL_ID = 1406952218543788063  # Channel for sending DMs (Used in cogs/dm_sender.py)

# Games and Leaderboards
DAILY_WORDLE_CHANNEL_ID = 1397577365957382316  # Channel for daily Wordle game (Used in cogs/wordle_daily.py)
WINNER_ANNOUNCEMENT_CHANNEL_ID = 1397578103571615774  # Channel for announcing Wordle winners (Used in cogs/wordle_daily.py)
LEADERBOARD_CHANNEL_ID = 1408845348214018118  # Channel for game leaderboard updates (Used in cogs/leaderboard_watcher.py)

# Notifications and Attendance
NOTIFY_CHANNEL_ID = 1388895797722091530  # Channel for notifications about Google Drive uploads (Used in cogs/upload_notifier.py)
ATTENDANCE_CHANNEL_ID = 1393576065427046621  # Channel for attendance tracking (Used in cogs/attendancev2.py, attendance.py)

# Manager-Specific
MANAGER_CHANNEL_ID = 1390954199591813121  # Channel for manager-specific tasks (Used in cogs/attendancev2.py)

# Google Drive Configuration
# Used for accessing files from Google Drive
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SERVICE_ACCOUNT_JSON = os.path.join(BASE_DIR, 'google_drive.json')
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
FOLDER_ID = '1EuFkB3s6shYxc58_D8yloe2OBNENimh_'

# Embed Assets
# URLs for images used in embeds
EMBED_THUMBNAIL = 'https://cdn.discordapp.com/attachments/1303620918454779914/1303621095571591218/ideax_logo_white.png?ex=672c6b41&is=672b19c1&hm=e5bd4447cf9d51d30d06710962d1cc50ac64ff82e0ab851e6be2672504033e64&'
EMBED_FOOTER = 'https://media.discordapp.net/attachments/1389639157743354028/1403646085729353830/X.png?ex=68984ec9&is=6896fd49&hm=dd85c5218e8d8de7aca71e922fb3dcd865810b359a1b33fbdd56ce404d334aeb&=&format=webp&quality=lossless'
EMBED_IMAGE = 'https://i.giphy.com/media/v1.Y2lkPTc5MGI3NjExbGk1c243M2x2b2k2djZpdnZtOWMzemk2djAxdHYyZHlpdDZkMXBxOSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/3Otqo8qv0LkmdUDe7w/giphy.gif'
WELCOME_BANNER = 'https://cdn.discordapp.com/attachments/1389639157743354028/1389643291519352943/1FDFD219-97F4-406A-ADFE-35F3D3E637EE_3.gif?ex=68655dab&is=68640c2b&hm=6a45634601be318f32b87e50c3ca8c868149ebc40da0225376f00ee270c59ef5&'
WELCOME_GRAPHICS = 'https://cdn.discordapp.com/attachments/1389639157743354028/1389794031608795187/welcome_graphics.gif?ex=6865ea0e&is=6864988e&hm=f4939516e4640e044bfc6731df805c38852da75351918efd377e0001176a01c8&'

# About Section
# Description of the bot and its history
ABOUT_DESCRIPTION = f"""{BOT_NAME} started as a hobby project in the form of a no-code discord bot back in 2021 when the popularity of Among Us gained traction. With having discord as the main form of communication among friends, it became a fun little project for our server but was soon discarded due to limited coding skills. 

The development process started again in October of 2024 when I felt comfortable enough to work in python after I had learned the basics of the language and developed a decent enough knowledge to write and navigate around the code.

The character design for {BOT_NAME} was done by the lead organizer of IdeaX 2024, Banshaj Paudel.

IdeaX 2025 is the first time {BOT_NAME} Bot is being hosted and running on this server for your help and entertainment. 

Thank you.
"""

# Bot Token
# Replace this with your bot token or set it as an environment variable
BOT_TOKEN = 'REDACTED_DISCORD_BOT_TOKEN'
# Uncomment the following lines to use an environment variable for the token
# BOT_TOKEN = os.environ.get("BOT_TOKEN")
# if not BOT_TOKEN:
#     raise ValueError("BOT_TOKEN environment variable not found")
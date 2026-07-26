# Yearly Handover Checklist

To ensure the IdeaX Discord Bot is ready for the new season each year, the outgoing and incoming maintainers should follow this checklist. This ensures no old data leaks into the new event and all configurations point to the new Discord server setup.

## 1. Credentials and Accounts
The new maintainer must acquire or regenerate the following credentials:
- **Discord Bot Token**: Transfer ownership of the application in the Discord Developer Portal, or have the new maintainer create a new Bot Application and provide the new token.
- **`.env` Keys**: Ensure the new maintainer has access to any required API keys for OpenAI, OpenRouter, TMDB, or others as listed in `.env.example`.
- **Google Drive Service Account**: Ensure the `google_drive.json` file is transferred securely, or generate a new service account JSON for the new year's Google Drive folder.

## 2. Configuration Updates (`config.py`)
Before launching the bot for the new year, update the `config.py` file:
- **Channel IDs**: When you set up the new Discord server for this year's IdeaX, copy the new Channel IDs and update variables like `WELCOME_CHANNEL_ID`, `LOG_CHANNEL_ID`, `ANNOUNCE_INPUT_CHANNEL_ID`, etc.
- **Dates**: Update the `SPECIAL_DATES` dictionary with the correct dates for the new year's workshops, registration deadlines, and hackathons.
- **Text & Links**: Update `ABOUT_DESCRIPTION` and social links if the year or links have changed.
- **Google Drive Folder**: Update `FOLDER_ID` to point to the new year's shared drive.

## 3. Data Cleanup (`bot_memory/`)
The bot stores persistent data locally in the `bot_memory/` directory. To ensure you don't carry over last year's attendees, bugs, or teams, you should **clear the contents** (or safely backup and delete the files) of the following files before the new season starts:
- `attendance.json`
- `bug_reports.json`
- `dp_competition.json`
- `events.json`
- `team_availability.json`
- `server_user_id.json`
- `openrouter_usage.json`

*(Note: Files like `country_codes.json` and `currency_codes.json` are static and do not need to be cleared.)*

## 4. Environment Reset
If you are moving to a new hosting server:
1. Clone the repository on the new host.
2. Place the populated `.env` and `google_drive.json` in the root folder.
3. Run `./setup_bot_hosting.sh` to install dependencies and start the systemd service.
4. Verify the bot is online and slash commands are synced in the new server.

# Setup and Hosting Guide

This guide provides instructions for deploying and hosting the IdeaX Discord Bot (Ixy).

## Prerequisites

- **OS:** A Linux-based system (Ubuntu/Debian, Fedora/RHEL, or Arch).
- **Python:** Python 3.10 or higher.
- **Bot Token:** A valid Discord Bot Token.
- **Google Drive Service Account (Optional):** Required for features interacting with Google Drive.

## Step 1: Clone the Repository

Clone this repository to your hosting environment:

```bash
git clone <repository_url> discord-bot-IdeaX
cd discord-bot-IdeaX
```

## Step 2: Configure Environment Variables

The bot uses a `.env` file to securely load sensitive credentials. 
Copy the example file and populate it with your specific credentials:

```bash
cp .env.example .env
```

**Required environment variables in `.env`:**
- `BOT_TOKEN`: Your Discord bot token (obtained from the Discord Developer Portal).

*Note: There might be other keys required by specific cogs (e.g., OPENAI_API_KEY for `gpt.py`). Refer to the `.env.example` file for a complete list of required keys.*

## Step 3: Configure Project Settings

Modify `config.py` to match your server's setup:
- Update channel IDs (`WELCOME_CHANNEL_ID`, `LOG_CHANNEL_ID`, etc.) to point to valid channels in your Discord server.
- Update `SPECIAL_DATES` for the current year's IdeaX events.
- Update social links or `ABOUT_DESCRIPTION` if needed.

If using Google Drive features, ensure `google_drive.json` (the service account credentials file) is placed in the root directory and the `FOLDER_ID` in `config.py` is updated.

## Step 4: Automated Deployment (Recommended)

The project includes a robust bash script (`setup_bot_hosting.sh`) designed to automate installation, dependency resolution, and systemd service creation.

1. Make the script executable:
   ```bash
   chmod +x setup_bot_hosting.sh
   ```

2. Run the script:
   ```bash
   ./setup_bot_hosting.sh
   ```

### What `setup_bot_hosting.sh` Does:
1. Detects your package manager (apt, dnf, pacman) and installs `python3` and `pip` if missing.
2. Generates a network connectivity check script (`wait-for-connectivity.sh`) to ensure the bot only starts when the server has internet access.
3. Creates a `systemd` service (`discordbot.service`) to run the bot automatically in the background and on system boot.
4. Installs all required Python packages from `requirements.txt`.
5. Starts the bot.

## Step 5: Managing the Bot Service

Once deployed via the setup script, you can manage the bot using standard `systemctl` commands:

- **Check Status:**
  ```bash
  sudo systemctl status discordbot
  ```

- **Restart the Bot (e.g., after updating code or config):**
  ```bash
  sudo systemctl restart discordbot
  ```

- **Stop the Bot:**
  ```bash
  sudo systemctl stop discordbot
  ```

- **View Live Logs:**
  ```bash
  journalctl -u discordbot -f
  ```

## Troubleshooting

- **Service fails to start:** Check the logs using `journalctl -u discordbot --no-pager --lines=50`. Ensure `python3` is accessible and `main.py` is in the correct directory.
- **Commands aren't working:** Ensure the bot has been invited to your server with the `applications.commands` scope and the necessary intents (Message Content, Server Members) are enabled in the Discord Developer Portal.

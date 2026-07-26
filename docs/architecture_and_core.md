# Architecture & Core Systems

This document explains the core architecture of the IdeaX Discord Bot (Ixy), focusing on how the bot starts up, manages configuration, and dynamically loads extensions (Cogs).

## Application Entry Point (`main.py`)

`main.py` is the central script that initializes the bot and coordinates its lifecycle.

### Key Responsibilities:
1. **Intents and Client Initialization:**
   The bot requests `Intents.default()` along with `message_content` and `members` intents to ensure it receives message data and member join/leave events.
2. **Dynamic Cog Loading:**
   Instead of manually importing every feature, `main.py` recursively walks through the `cogs/` directory and loads every `.py` file as a Discord Cog. This allows for a highly modular architecture where new features can be added by simply dropping a script into the `cogs/` folder.
3. **Command Syncing:**
   On startup (`on_ready`), the bot syncs its application (slash) commands to Discord. This ensures that new or updated slash commands instantly appear in the Discord UI.
4. **Presence Updates:**
   A background task loops every 10 minutes, randomly selecting a humorous or relatable status from a predefined list and updating the bot's rich presence.
5. **Error Handling:**
   A global `on_command_error` listener intercepts errors. For instance, if an unknown command is used, it displays a helpful embed with a button to view all available commands. If a command is used in a DM when restricted to servers, it provides a tailored error message.

## Configuration System (`config.py` & `.env`)

The project uses a two-tiered configuration system:

1. **`.env` / Environment Variables:**
   Strictly used for sensitive secrets (e.g., `BOT_TOKEN`, API keys). Loaded using the `python-dotenv` package.
2. **`config.py`:**
   Acts as the central registry for structural configurations. This includes:
   - Hardcoded Discord Channel IDs (e.g., `WELCOME_CHANNEL_ID`, `LOG_CHANNEL_ID`).
   - Feature toggles and string constants (e.g., `ABOUT_DESCRIPTION`, Social Links).
   - Event scheduling (`SPECIAL_DATES`).
   - Visual assets (Image and GIF URLs for embeds).

Other files throughout the project import directly from `config` (e.g., `from config import *`), ensuring a single source of truth for all channels and settings.

## Extensibility (The Cogs System)

The bot leverages the `discord.ext.commands.Cog` framework. Each file in the `cogs/` directory encapsulates a specific domain of features (e.g., moderation, attendance, games). 

### Administrator Cog Commands
Administrators (Bot Owners) can manage these cogs dynamically without restarting the entire bot process via special prefix commands defined in `main.py`:
- `ixy load <cog_name>`: Loads a specific cog.
- `ixy unload <cog_name>`: Unloads a specific cog.
- `ixy reload <cog_name>`: Reloads a cog (useful for hot-swapping code changes).
- `ixy switch <cog_old> <cog_new>`: Switches out one cog for another.

*Note: Slash commands are automatically re-synced when cogs are manually reloaded.*

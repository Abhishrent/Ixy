# Developer Guide

This document is intended for developers adding new features, cogs, or making significant modifications to the IdeaX Discord Bot.

## Project Structure

- `main.py`: The core initialization script.
- `config.py` & `.env`: Central configuration and secrets.
- `cogs/`: Contains all modular features. Drop new Python files here to add features.
- `utils/`: Reusable helper functions and classes.
- `game_files/` & `images/`: Static assets used by various commands.
- `bot_memory/`: Persistent local storage (e.g., JSON files) for features that don't use an external database.

## Creating a New Cog

To add a new feature, create a new Python file in the `cogs/` directory.

### Example Cog Skeleton:

```python
import discord
from discord.ext import commands
from discord import app_commands
from config import *

class MyNewFeature(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # An event listener
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return
        # Handle message...

    # A slash command
    @app_commands.command(name="mycommand", description="Does something cool")
    async def my_command(self, interaction: discord.Interaction):
        await interaction.response.send_message("Hello from the new cog!")

async def setup(bot):
    await bot.add_cog(MyNewFeature(bot))
```

*Note: Because `main.py` dynamically loads everything in `cogs/`, your new file will be loaded automatically on the next bot restart.*

## Key Learnings & Conventions

The `learning.md` file in the root directory contains crucial historical lessons learned during the bot's development. Here is a summary of the most important developer conventions:

### 1. Persistent UI Views (Buttons & Dropdowns)
By default, Discord UI components stop responding when the bot restarts. To make them persistent:
- In your `View` class constructor, set `timeout=None`.
- Assign a strictly unique `custom_id` to every UI element (e.g., `@discord.ui.button(custom_id="unique_button_1")`).
- Pass the Cog instance (using `self`) into the View constructor so it can interact with the Cog's data.
- Register the view with the bot in your Cog's initialization phase using `self.bot.add_view(MyView(self))`.

### 2. Comprehensive Slash Command Logging
If you need to log interactions, do not rely solely on `on_command`. Instead, use the `on_app_command_completion` listener. This ensures that pure slash commands (using `@app_commands.command`) and hybrid commands are reliably captured and logged.

### 3. Fetching External Images (Wired News Example)
When building features that scrape or pull previews from external news sites, standard RSS image fields often fail. Use the Open Graph meta tag (`<meta property="og:image">`) from the page's HTML as it is the most reliable fallback.

## Testing Your Changes
When testing changes to a specific cog, you don't need to restart the entire bot. If your Discord user is registered as a bot owner, you can hot-reload the cog in Discord:
```text
ixy reload <cog_name>
```

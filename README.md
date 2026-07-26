# IdeaX Discord Bot (Ixy)

Welcome to the official repository for **Ixy**, the Discord bot custom-built for **IdeaX 2025**. 

Ixy started as a hobby project in 2021 and has evolved into a fully modular, feature-rich bot to handle attendance, online competition rounds, ticketing, moderation, minigames, and AI integrations for the IdeaX community. Developed by Abhishrent Khatri.

The character design for Ixy was done by the lead organizer of IdeaX 2024, Banshaj Paudel.

## Project Documentation

To ensure smooth handovers between maintainers every year, this project is thoroughly documented. Please refer to the `docs/` directory for detailed information:

1. **[Setup & Hosting Guide](docs/setup_and_hosting.md)**: 
   Learn how to deploy the bot from scratch using `setup_bot_hosting.sh`, manage environment variables, and operate the systemd service.

2. **[Architecture & Core](docs/architecture_and_core.md)**: 
   Understand how `main.py` dynamic-loads cogs, handles errors, and syncs commands. Learn about the `config.py` structure.

3. **[Cogs Reference](docs/cogs_reference.md)**: 
   A complete index of all 50+ modules (Cogs) grouped by functionality (e.g., IdeaX Event Management, Fun & Games, AI & APIs, Administration).

4. **[Developer Guide](docs/developer_guide.md)**: 
   Crucial rules and lessons learned for adding new features, maintaining persistent Discord UI elements, and hot-reloading extensions.

5. **[Yearly Handover Checklist](docs/yearly_handover_checklist.md)**:
   A strict step-by-step guide for incoming maintainers on what data to wipe, which configs to update, and which credentials to transfer every year before launch.

## Quick Start

1. Clone the repository.
2. Run `cp .env.example .env` and insert your `BOT_TOKEN`.
3. Review and update `config.py` for channel IDs and special dates.
4. Run `./setup_bot_hosting.sh` to install dependencies and start the bot service.

## Tech Stack
- **Language**: Python 3.10+
- **Library**: `discord.py` (v2+)
- **Storage**: Local JSON / SQLite (via `bot_memory/`)
- **Key Integrations**: Google Drive API, OpenAI / OpenRouter API, TMDB API.

---
*Created and maintained by the MBMC IdeaX Tech Team.*

# Discord Bot

A Python-based bot featuring multiple functionalities, including games, utilities, moderation, and more. This project is modular, using cogs to separate features and enhance maintainability.

## Features

- **Astrology**: Retrieve astrological information.
- **Auto Reactions**: Automate responses to specific triggers.
- **Calendar**: Manage events and schedules.
- **Countdown**: Track time until specified events.
- **Currency Converter**: Convert between different currencies.
- **Dictionary**: Look up word definitions.
- **Drive Integration**: Interact with Google Drive.
- **Friends Trivia**: Test your knowledge of the TV show _Friends_.
- **Games**: Includes Wordle, Tic-Tac-Toe, and more.
- **Greeter**: Welcome users with custom messages.
- **Moderation Tools**: Manage user activities.
- **Music Player**: Play and manage music.
- **NSFW Content**: Handle sensitive content responsibly.
- **Utility Tools**: General-purpose utilities for various tasks.

## Installation

1. Clone the repository:
    
    ```bash
    git clone https://github.com/Abhishrent/Discord-Bot.git
    ```
    
2. Install dependencies:
    
    ```bash
    pip install -r requirements.txt
    ```
    
3. Set up configuration:
    
    - Edit `config.py` to provide necessary API keys, tokens, and settings.
    - Place `google_drive.json` in the project root for Google Drive integration.

## Usage

Run the bot with:

```bash
python main.py
```

## Directory Structure

```
├── cogs
│   ├── astrology.py
│   ├── autoreactions.py
│   ├── ...
│   └── utilities.py
├── images
│   ├── header_image.png
│   └── footer_image.png
├── config.py
├── main.py
├── requirements.txt
└── words.txt
```

### Key Files

- `main.py`: Entry point for the bot.
- `config.py`: Configuration file for API keys and settings.
- `cogs/`: Contains modular functionality of the bot.

## Lab Report Maker 

Version|Feature 
-------|--------
labv1|no theory generation
labv2|add theory generation
labv3|add language and compiler labels for the theory section
labv4|add header date and footer image

## Join here
[![Discord](https://discord.com/api/guilds/1306600182208659486/widget.png?style=banner2)](https://discord.gg/As2vjM8jV9)
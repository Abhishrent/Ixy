# Cogs Reference

The IdeaX Discord Bot uses a modular architecture via `discord.ext.commands.Cog`. Below is a comprehensive index of the available cogs and their respective slash commands, organized by their functionality.

## Administration & Core Systems
- **`HelpEmbedCog`** (`help.py`): Manages the custom help embeds and persistent UI views.
- **`LogsCog`** (`logs.py`): Tracks and logs bot activity to a dedicated channel (e.g., `LOG_CHANNEL_ID`).
- **`ProgressLogger`** (`progress_logger.py`): Logs moderation actions and project progress.
- **`ResourceMonitor`** (`resource_monitor.py`): Monitors system resources (CPU/RAM) on the host machine.
- **`PersistentEmbed`** (`persistent_embed.py`): Handles creating and maintaining persistent embed messages across restarts.

## Moderation & Anti-Spam
- **`ModerationCog`** (`moderation.py`): Contains essential server management commands.
  - *Commands:* `/announce`, `/udau`, `/bhana`, `/timeout`, `/kick`, `/ban`
- **`AntiSpam`** (`anti_spam.py`): Automated background monitoring for spammy behavior and rate-limiting.
- **`AutoResponseCog`** (`nsfw.py`): Manages auto-replies or filters for specific triggers.
  - *Commands:* `/add_trigger`, `/remove_trigger`, `/list_triggers`, `/add_response`, `/remove_response`, `/list_responses`

## IdeaX Event Management
These cogs are tailored for managing the actual IdeaX competitions and rounds.
- **`OnlineRoundCog`** (`online_round.py` & `onlineround.py`): Manages the complex logistics of the IdeaX online round.
  - *Commands:* `/setup_role`, `/register_team`, `/add_member`, `/remove_member`, `/list_teams`, `/set_queue`, `/setup_channels`, `/quick_setup`, `/start`, `/next`, `/stop`, `/status`, `/delete_team`, `/clear_all`, `/backup`
- **`CheckRegistrationCog`** (`check_registration.py`): Cross-references users with registration databases.
- **`DPCompetition`** (`dp_competition.py`): Specific logic for the Display Picture/Design competition.
- **`TeamPairing`** (`team_finder.py`): Helps solo participants find a team.
  - *Commands:* `/find-team`

## User Engagement & Utilities
- **`AttendanceCog`** (`attendancev2.py`): Tracks user attendance for events or workshops.
- **`Calendar`** (`event_calendar.py`) & **`EventDetails`** (`event_details.py`): Displays upcoming events and schedules.
- **`DMSenderCog`** (`dm_sender.py`, `dm_sender_v2.py`): Allows administrators to securely DM users via the bot.
- **`Ticket`** (`ticket.py`): A complete ticketing system for support requests.
  - *Commands:* `/open`, `/close`, `/add_to_channel`
- **`BugReportTracker`** (`report_bugs.py`): Allows users to report bugs which are tracked by administrators.

## AI & APIs
- **`TicketAIAssistant`** (`gpt.py` & `openrouter.py`): Integrates OpenAI/OpenRouter APIs to provide AI assistance directly in support tickets.
- **`Drive`** & **`DriveVideoNotify`** (`drive.py`, `upload_notifier.py`): Interfaces with Google Drive (using `google_drive.json`) to notify users of new uploads.
- **`CollegiateDictionary`** (`dictionary.py`): Dictionary lookups.
- **`TMDB`** (`tmdb.py`): Movie Database integration.
  - *Commands:* `/search`, `/recommend`

## Fun, Games, & Entertainment
- **`GameSelector`** (`game_selector.py`): A hub menu to select games.
- **`Connect4`** (`games/connect_4.py`): *Commands:* `/start`, `/stop`, `/scores`
- **`Mancala`** (`games/mancala.py`): *Commands:* `/start`, `/stop`, `/scores`
- **`TicTacToeGame`** (`games/tictactoe.py`): *Commands:* `/start`
- **`WordleGame`** (`games/wordle.py`): *Commands:* `/start`, `/quit`
- **`DailyWordleGame`** (`games/wordle_daily.py`): A daily scheduled wordle game for the server.
- **`FriendsTrivia`** (`games/friends.py`): *Commands:* `/quiz`
- **`MemoryMatchingGame`** & **`SequenceMemoryGame`**: *Commands:* `/start`
- **`GuessNumber`**: *Commands:* `/start`, `/stop`, `/scores`
- **`GuessTheFlag`** (`guess_the_flag.py`): *Commands:* `/flagguesser`
- **`Astro`** (`astrology.py`): Astrology and horoscopes.
- **`Books`** (`books.py`): *Commands:* `/search`, `/author`
- **`RedditImage`** (`spawn.py`): Spawns random images from Reddit.

## Miscellaneous & Tools
- **`AnnouncementCog`** (`announcement_sender.py`): Sends styled announcements.
- **`ASCIIArt`** (`ascii_art.py`): Generates ASCII art text. *Commands:* `/ascii`
- **`BirthdaysCog`** (`birthdays.py`): Tracks and announces user birthdays.
- **`CountdownCog`** (`countdown.py`): Live countdowns for specific dates.
- **`CurrencyConverterCog`** (`currency.py`): Converts currencies.
- **`DisplayAvatar`** (`display_avatar.py`): Quickly grabs a user's avatar.
- **`Welcome`** (`greeter.py`): Sends rich welcome messages to new members.
- **`General`** (`greetings.py`): Simple greeting commands (`/namaste`, `/hello`, etc.).
- **`Info`** (`info.py`): Displays bot latency, uptime, and info.
- **`Leaderboards`** & **`LeaderboardWatcher`**: Tracks game scores and general server activity.
- **`MoveCog`** (`move.py`): Moves users between voice channels. *Commands:* `/move`
- **`Poll`** (`poll.py`): Creates interactive polls.
- **`ZipHandlerCog`** & **`ZipSorterCog`** (`zip.py`, `rename.py`): Handles extracting and renaming zip files.
- **`LabReportGenerator`** (`labv5.py`): *Commands:* `/add_theory`
- **`ResourceDownloader`** (`resource_downloader.py`): *Commands:* `/force_gui`

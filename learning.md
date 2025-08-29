# Wired News Image Extraction: Approaches & Results

## Problem

Display the main image from each Wired news article in Discord embeds. Wired’s RSS feed does not always provide a direct image URL in a standard field.

---

## Approaches Tried

### 1. RSS Media Fields

Tried to extract the image from standard RSS fields:

```python
if "media_content" in entry and entry.media_content:
    image_url = entry.media_content[0].get("url")
elif "media_thumbnail" in entry and entry.media_thumbnail:
    image_url = entry.media_thumbnail[0].get("url")
elif "image" in entry:
    image_url = entry.image
```

**Result:**  
Wired’s RSS feed often does not include these fields, or they are empty.

---

### 2. Extracting `<img>` from HTML in Summary/Content

Parsed the HTML in the summary or content for an `<img src="...">` tag:

```python
html = ""
if hasattr(entry, "summary_detail") and hasattr(entry.summary_detail, "value"):
    html = entry.summary_detail.value
elif hasattr(entry, "content") and entry.content and "value" in entry.content[0]:
    html = entry.content[0]["value"]
match = re.search(r'<img[^>]+src="([^">]+)"', html)
if match:
    image_url = match.group(1)
```

**Result:**  
Wired’s RSS summary/content rarely contains an actual `<img>` tag, or the image is not the main article image.

---

### 3. Fetching the Article Page and Extracting Open Graph Image

Fetched the article’s HTML and extracted the Open Graph image:

```python
if not image_url:
    try:
        resp = requests.get(entry.link, timeout=5)
        if resp.status_code == 200:
            og_match = re.search(r'<meta property="og:image" content="([^"]+)"', resp.text)
            if og_match:
                image_url = og_match.group(1)
    except Exception as e:
        print(f"Failed to fetch og:image for {entry.link}: {e}")
```

**Result:**  
Most modern news sites, including Wired, use the Open Graph protocol to specify the main image for social sharing. The `<meta property="og:image" ...>` tag is reliably present and contains the correct image URL.

---

## Final Working Solution

The final code tries all the above methods, but reliably falls back to fetching the article and extracting the Open Graph image:

```python
for entry in feed.entries:
    if entry.link not in self.sent_links:
        image_url = None
        # Try RSS fields first
        if "media_content" in entry and entry.media_content:
            image_url = entry.media_content[0].get("url")
        elif "media_thumbnail" in entry and entry.media_thumbnail:
            image_url = entry.media_thumbnail[0].get("url")
        elif "image" in entry:
            image_url = entry.image
        else:
            # Try to extract <img src="..."> from summary or content
            html = ""
            if hasattr(entry, "summary_detail") and hasattr(entry.summary_detail, "value"):
                html = entry.summary_detail.value
            elif hasattr(entry, "content") and entry.content and "value" in entry.content[0]:
                html = entry.content[0]["value"]
            match = re.search(r'<img[^>]+src="([^">]+)"', html)
            if match:
                image_url = match.group(1)
        # Fallback: fetch article HTML and extract og:image
        if not image_url:
            try:
                resp = requests.get(entry.link, timeout=5)
                if resp.status_code == 200:
                    og_match = re.search(r'<meta property="og:image" content="([^"]+)"', resp.text)
                    if og_match:
                        image_url = og_match.group(1)
            except Exception as e:
                print(f"Failed to fetch og:image for {entry.link}: {e}")

        embed = discord.Embed(
            title=entry.title,
            url=entry.link,
            description=entry.summary[:200] + "...",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=EMBED_THUMBNAIL)
        if image_url:
            embed.set_image(url=image_url)
        embed.set_footer(text="WIRED Tech News")
        await channel.send(embed=embed)
        self.sent_links.add(entry.link)
        self.save_sent_links()
        break  # Only send one new article per cycle
```

---

## Summary

- **Standard RSS fields:** Not reliable for Wired.
- **HTML parsing:** Sometimes works, but not for Wired’s main images.
- **Open Graph meta tag:** Reliable and works for Wired and most news sites.

**Fetching the article and parsing the Open Graph image is the most robust solution for this use case.**

---

## Discord Bot: Making UI Buttons Persistent Across Restarts

### Problem

Discord UI buttons (like those in embeds) stop working after a bot restart. Users clicking the buttons get "This interaction failed" errors because the bot loses the view references when it restarts.

---

### What Didn't Work

#### 1. Basic View Implementation Without Persistence

```python
class HelpView(discord.ui.View):
    def __init__(self):
        super().__init__()  # No timeout=None, no persistence setup
    
    @discord.ui.button(label="Open Support Ticket", style=discord.ButtonStyle.primary)
    async def open_ticket(self, interaction, button):
        # Button logic here
        pass
```

**Result:**  
Buttons worked fine until bot restart, then became completely unresponsive.

#### 2. Setting Timeout to None Only

```python
class HelpView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)  # Persistent view but not registered
```

**Result:**  
Still didn't work after restart because the view wasn't registered with the bot.

#### 3. Basic View Registration (First Attempt)

```python
class HelpEmbedCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.last_help_message_id = None
        self.bot.loop.create_task(self.setup_view())
    
    async def setup_view(self):
        await self.bot.wait_until_ready()
        self.bot.add_view(HelpView())  # Missing cog parameter
    
    @commands.Cog.listener()
    async def on_message(self, message):
        # ...message handling...
        view = HelpView()  # Creating new instance - breaks persistence!
        help_msg = await message.channel.send(embed=embed, view=view)
```

**Result:**  
Still failed because new view instances weren't connected to the registered persistent view.

#### 4. Using Stored View Instance (Second Attempt)

```python
class HelpEmbedCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.help_view = HelpView()  # Store instance
        self.bot.loop.create_task(self.setup_view())
    
    async def setup_view(self):
        await self.bot.wait_until_ready()
        self.bot.add_view(self.help_view)  # Register stored instance
    
    @commands.Cog.listener()
    async def on_message(self, message):
        # ...message handling...
        view = self.help_view  # Use stored instance
        help_msg = await message.channel.send(embed=embed, view=view)
```

**Result:**  
Still didn't work because the view needed the cog reference to function properly.

---

### What Finally Worked

#### Complete Persistent View Setup with Cog Reference

The solution was to pass the cog instance to the view, exactly like the working attendance system:

```python
class HelpView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None)  # Persistent view
        self.cog = cog  # Store cog reference
    
    @discord.ui.button(
        label="Open Support Ticket", 
        style=discord.ButtonStyle.primary, 
        emoji="🎫", 
        custom_id="help_ticket_button"  # Important: unique custom_id
    )
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Button logic here - can access self.cog for data/methods
        support_cog = interaction.client.get_cog("Support")
        # ...rest of button logic...

class HelpEmbedCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.last_help_message_id = None
        self.bot.loop.create_task(self.setup_view())  # Setup on initialization
    
    async def setup_view(self):
        await self.bot.wait_until_ready()
        self.bot.add_view(HelpView(self))  # Pass self to view
    
    @commands.Cog.listener()
    async def on_message(self, message):
        # ...message handling...
        view = HelpView(self)  # Always pass self to view
        help_msg = await message.channel.send(embed=embed, view=view)
        self.last_help_message_id = help_msg.id
```

**Result:**  
Buttons work perfectly across bot restarts and maintain all functionality.

---

### Key Requirements for Persistent Buttons

1. **Set `timeout=None`** in the View constructor to make it persistent
2. **Pass cog instance to view** - `HelpView(self)` not `HelpView()`
3. **Store cog reference** - `self.cog = cog` in view constructor
4. **Add unique `custom_id`** to buttons for Discord's internal tracking
5. **Register view with bot** using `bot.add_view(ViewClass(self))` after bot is ready
6. **Always pass cog instance** when creating view instances in message handlers

---

### Why This Works

- `timeout=None` tells Discord that this view should persist indefinitely
- `custom_id` provides a unique identifier for Discord to track the button
- `bot.add_view()` registers the view with the bot's internal view handler
- **Cog reference** allows the view to access cog data and methods consistently
- When the bot restarts, it re-registers all persistent views during startup
- Discord maintains the button references and routes interactions to the registered views

---

### Comparison: Final Working vs Previous Attempts

**❌ Previous Attempts (buttons break after restart):**
```python
# Missing cog reference and proper view management
view = HelpView()  # No cog reference
self.bot.add_view(HelpView())  # No cog reference
```

**✅ Final Working Solution:**
```python
# Proper cog reference and view management
view = HelpView(self)  # Pass cog reference
self.bot.add_view(HelpView(self))  # Pass cog reference
```

**The critical difference is passing the cog instance to the view constructor, matching the pattern used in the working attendance system.**

---

## Slash Command Logging: Ensuring Comprehensive Coverage

### Problem

Need to log all slash command invocations for monitoring and debugging. Previously, some commands were not being logged.

---

## Why Slash Command Logging Did Not Work Before, and What Fixed It

### What Didn't Work

Previously, only the `on_command` event and (optionally) `on_application_command` were being used to log command usage. However, these listeners do **not** always capture all types of slash command invocations, especially if:

- The command is a pure application (slash) command (using `@app_commands.command` or `@bot.tree.command`).
- The event name or signature does not match the discord.py version in use.
- The command is a hybrid command or registered in a way that bypasses the listener.

As a result, some slash commands (like `/udau`) were not being logged, because their invocations did not trigger the expected event handler.

### What Made It Work

Adding a listener for `on_app_command_completion` (discord.py 2.x+) ensures that **all** application command completions—including pure slash commands and hybrid commands—are logged. This event is specifically designed to fire after any application command (slash command) is executed, regardless of how it was registered.

**Key changes that made it work:**

- Added the `on_app_command_completion` listener to the cog.
- Used the `interaction` and `command` parameters to extract user, command name, and options.
- Ensured the logging logic is compatible with both hybrid and pure slash commands.

**Summary:**  
The fix was to use the correct event (`on_app_command_completion`) that is guaranteed to fire for all slash command invocations, ensuring comprehensive logging of all command types, including `/udau`.

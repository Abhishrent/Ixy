import discord
from discord.ext import commands
import os
import asyncio
import re
import json
import aiohttp
from typing import List, Dict, Any, Literal
from utils.knowledge_base import get_system_prompt

# Constants
OPENROUTER_API_KEY = "***REMOVED***"
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_SITE_URL = "https://discord.gg/hackathon"
OPENROUTER_SITE_NAME = "IxyBot Discord Assistant"

# Path to store usage data
USAGE_DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../bot_memory/openrouter_usage.json")

class AIAssistant:
    """Handle AI-powered interactions using OpenRouter API"""
    
    def __init__(self):
        # Set up API access
        self.api_key = OPENROUTER_API_KEY
        
        # Default model - with fallback options
        self.models = [
            "mistralai/mistral-small-3.2-24b-instruct:free"
        ]
        
        # REMOVE cached system prompt to allow real-time refresh
        # self.system_prompt = get_system_prompt()
        self.context_window = []  # Store recent conversation history
        self.max_context_messages = 10  # Maximum number of messages to keep in context
        self.usage_data = self.load_usage_data()
        self.max_retries = 3  # Maximum retries per model
        self.retry_delay = 2  # Delay in seconds between retries
    
    @property
    def system_prompt(self):
        """Always fetch the latest system prompt (event config) at call time."""
        return get_system_prompt()
    
    def load_usage_data(self) -> Dict[str, Any]:
        """Load usage data from file or create if doesn't exist"""
        if os.path.exists(USAGE_DATA_PATH):
            try:
                with open(USAGE_DATA_PATH, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        
        # Initialize with default data
        data = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "models_used": {}
        }
        
        # Save initial data
        self.save_usage_data(data)
        return data
    
    def save_usage_data(self, data=None):
        """Save usage data to file"""
        if data is None:
            data = self.usage_data
            
        os.makedirs(os.path.dirname(USAGE_DATA_PATH), exist_ok=True)
        with open(USAGE_DATA_PATH, 'w') as f:
            json.dump(data, f, indent=2)
    
    def update_context(self, role: str, content: str):
        """Update conversation context window"""
        self.context_window.append({"role": role, "content": content})
        
        # Trim context if it's too long
        if len(self.context_window) > self.max_context_messages:
            # Remove oldest message (but preserve the system message if it exists)
            oldest_non_system = next(
                (i for i, msg in enumerate(self.context_window) if msg["role"] != "system"), 
                0
            )
            if oldest_non_system > 0:
                self.context_window.pop(oldest_non_system)
            else:
                self.context_window.pop(0)
    
    def update_usage_stats(self, success: bool, model_used: str = None):
        """Update usage statistics"""
        self.usage_data["total_requests"] += 1
        
        if success:
            self.usage_data["successful_requests"] += 1
            
            # Update model usage if provided
            if model_used:
                if model_used not in self.usage_data["models_used"]:
                    self.usage_data["models_used"][model_used] = 0
                self.usage_data["models_used"][model_used] += 1
        else:
            self.usage_data["failed_requests"] += 1
        
        self.save_usage_data()
    
    async def get_response(self, query: str) -> str:
        """Get AI response to user query with model fallback support"""
        # Try each model in succession if needed
        last_error = None
        
        for model in self.models:
            # Try with retries for each model
            for retry in range(self.max_retries):
                try:
                    print(f"Trying model: {model} (attempt {retry+1}/{self.max_retries})")
                    
                    # Prepare messages with system prompt and context window (system prompt fetched fresh)
                    messages = [{"role": "system", "content": self.system_prompt}]
                    messages.extend(self.context_window)
                    messages.append({"role": "user", "content": query})
                    
                    # Prepare request headers and data
                    headers = {
                        "Authorization": f"Bearer {self.api_key}",
                        "HTTP-Referer": OPENROUTER_SITE_URL,
                        "X-Title": OPENROUTER_SITE_NAME,
                        "Content-Type": "application/json"
                    }
                    
                    data = {
                        "model": model,
                        "messages": messages,
                        "temperature": 0.7,
                        "max_tokens": 500
                    }
                    
                    async with aiohttp.ClientSession() as session:
                        async with session.post(
                            url=OPENROUTER_API_URL,
                            headers=headers,
                            json=data
                        ) as response:
                            if response.status == 200:
                                result = await response.json()
                                ai_response = result["choices"][0]["message"]["content"]
                                
                                # Update context with this interaction
                                self.update_context("user", query)
                                self.update_context("assistant", ai_response)
                                
                                # Update usage stats
                                self.update_usage_stats(success=True, model_used=model)
                                
                                return ai_response
                            
                            # If rate limited, wait before retry or try next model
                            if response.status == 429:
                                error_text = await response.text()
                                last_error = f"Rate limit on {model}: {error_text}"
                                print(f"Rate limited on {model}, waiting {self.retry_delay} seconds before retry...")
                                await asyncio.sleep(self.retry_delay)
                                continue
                            
                            # Other errors
                            error_text = await response.text()
                            last_error = f"Error with {model}: {response.status} - {error_text}"
                            print(last_error)
                            break  # Try next model for non-rate-limit errors
                    
                except Exception as e:
                    last_error = f"Exception with {model}: {str(e)}"
                    print(last_error)
                    break  # Try next model
        
        # Update stats for failed request
        self.update_usage_stats(success=False)
        
        # If all models failed
        return "I'm having trouble connecting to my knowledge service right now. Please try again later or contact the organizing committee for assistance."

class TicketAIAssistant(commands.Cog):
    """Cog to provide AI assistance in ticket channels"""
    
    def __init__(self, bot):
        self.bot = bot
        self.assistants = {}  # Store AI assistants per channel
        self.ticket_pattern = re.compile(r"ticket-[a-zA-Z0-9_]+")
        # Add tracking for conversations
        self.ongoing_conversations = {}  # Track ongoing human conversations by channel
        self.last_activity = {}  # Track when last message was sent in a channel
        self.conversation_timeout = 180  # Consider conversation ended after 3 minutes of inactivity
        self.organizing_committee_role_id = 1130051976189722680  # The organizing committee role ID
        self.mod_role_names = ["mod", "moderator", "staff", "admin", "support"]  # Role names that indicate moderators
        self.enabled = True  # Global toggle for AI responses

    def get_assistant(self, channel_id: int) -> AIAssistant:
        """Get or create an AI assistant for a channel"""
        if channel_id not in self.assistants:
            self.assistants[channel_id] = AIAssistant()
        return self.assistants[channel_id]
    
    def is_staff(self, member: discord.Member) -> bool:
        """Check if a member is a staff member (mod or organizing committee)"""
        # Check for organizing committee role
        if self.organizing_committee_role_id in [role.id for role in member.roles]:
            return True
            
        # Check for admin permissions
        if member.guild_permissions.administrator:
            return True
            
        # Check for moderator role names
        for role in member.roles:
            if any(mod_term in role.name.lower() for mod_term in self.mod_role_names):
                return True
        
        return False
    
    def update_conversation_state(self, channel_id: int, author_id: int, is_staff: bool):
        """Update the state of ongoing conversations in the channel"""
        current_time = asyncio.get_event_loop().time()
        
        # Check if there's an existing conversation and if it's timed out
        if channel_id in self.ongoing_conversations:
            last_time = self.last_activity.get(channel_id, 0)
            if current_time - last_time > self.conversation_timeout:
                # Conversation timed out, reset it
                self.ongoing_conversations[channel_id] = {"user_id": author_id, "staff_active": is_staff}
            else:
                # Update the existing conversation state
                self.ongoing_conversations[channel_id]["staff_active"] = (
                    self.ongoing_conversations[channel_id]["staff_active"] or is_staff
                )
                if not is_staff:
                    self.ongoing_conversations[channel_id]["user_id"] = author_id
        else:
            # New conversation
            self.ongoing_conversations[channel_id] = {"user_id": author_id, "staff_active": is_staff}
            
        # Update the last activity time
        self.last_activity[channel_id] = current_time
    
    def should_ai_respond(self, channel_id: int, message: discord.Message) -> bool:
        """Determine if the AI should respond to this message"""
        # AI responds when:
        # 1. Message is directed at the bot (mentions or clear questions)
        # 2. No active staff conversation is happening
        # 3. It's been a while since the last message (conversation reset)
        
        # Check if the bot is mentioned
        bot_mentioned = self.bot.user in message.mentions
        
        # Check if the message is a question or command directed at the bot
        content = message.content.lower()
        is_directed_at_bot = (
            bot_mentioned or
            bool(re.search(r'\b(ixy|assistant|bot)\b', content, re.IGNORECASE)) or
            bool(re.search(r'\?$', content)) or
            bool(re.search(r'\bhelp\b', content, re.IGNORECASE)) or
            content.strip() in ['hi', 'hello', 'hey']
        )
        
        # Get conversation state
        convo = self.ongoing_conversations.get(channel_id, {"user_id": None, "staff_active": False})
        
        # Check if there's an ongoing conversation with staff
        if convo["staff_active"]:
            # Only respond if directly addressed or if it's been a while
            current_time = asyncio.get_event_loop().time()
            last_time = self.last_activity.get(channel_id, 0)
            conversation_reset = current_time - last_time > self.conversation_timeout
            
            return is_directed_at_bot or conversation_reset
        
        # If no staff is active, respond normally
        return True
    
    # Replace group-based ai_assist with single command having action choices
    def _ai_status_embed(self):
        color = 0x2ECC71 if self.enabled else 0xE74C3C
        return discord.Embed(title="AI Assistant Status", description=f"{'🟢 Enabled' if self.enabled else '🔴 Disabled'}", color=color)

    @commands.hybrid_command(name="ai_assist", aliases=["toggleai", "aistatus"], description="Enable, disable, or view AI assistant status.")
    @commands.has_permissions(administrator=True)
    async def ai_assist(self, ctx: commands.Context, action: Literal["on", "off", "status"] = "status"):
        """Toggle or view AI assistant status.
        action choices: on | off | status"""
        if action == "status":
            await ctx.reply(embed=self._ai_status_embed())
            return
        if action == "on":
            if self.enabled:
                embed = discord.Embed(title="AI Assistant", description="Already enabled ✅", color=0x2ECC71)
            else:
                self.enabled = True
                embed = discord.Embed(title="AI Assistant", description="Enabled ✅", color=0x2ECC71)
            await ctx.reply(embed=embed)
            return
        if action == "off":
            if not self.enabled:
                embed = discord.Embed(title="AI Assistant", description="Already disabled ⛔", color=0xE74C3C)
            else:
                self.enabled = False
                embed = discord.Embed(title="AI Assistant", description="Disabled ⛔", color=0xE74C3C)
            await ctx.reply(embed=embed)
            return

    @ai_assist.error
    async def ai_assist_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(title="AI Assistant Error", description="You need administrator permissions to use this command.", color=0xE74C3C)
        else:
            embed = discord.Embed(title="AI Assistant Error", description="Error processing command.", color=0xE74C3C)
        await ctx.reply(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Monitor messages in ticket channels and respond, and reply to bot mentions in public channels"""
        # Skip if globally disabled
        if not getattr(self, 'enabled', True):
            return
        
        # Ignore bot messages to prevent loops
        if message.author.bot:
            return
            
        # --- Ticket channel logic ---
        if message.guild and self.ticket_pattern.match(message.channel.name):
            # Check if we should respond
            is_staff = self.is_staff(message.author)
            self.update_conversation_state(message.channel.id, message.author.id, is_staff)
            
            if not self.should_ai_respond(message.channel.id, message):
                return
            
            # Process the message with AI
            async with message.channel.typing():  # Show typing indicator
                # Add a small delay to make the response seem more natural
                await asyncio.sleep(1.5)
                
                # Get AI assistant for this channel
                assistant = self.get_assistant(message.channel.id)
                
                # Generate response
                response = await assistant.get_response(message.content)
                
                # Send the response
                await message.reply(response)
            
            return  # Only handle one logic path per message

        # --- Public channel reply-on-mention logic ---
        # If the bot is mentioned in a reply, reply to the original message
        if (
            message.guild
            and self.bot.user in message.mentions
            and not self.ticket_pattern.match(message.channel.name)
            and message.reference is not None
        ):
            try:
                original_message = await message.channel.fetch_message(message.reference.message_id)
            except Exception:
                original_message = None
            if original_message:
                async with message.channel.typing():
                    await asyncio.sleep(1.5)
                    assistant = self.get_assistant(message.channel.id)
                    response = await assistant.get_response(original_message.content)
                    await original_message.reply(response, mention_author=True)
                return

        # If the bot is mentioned directly (not in a reply), reply to that message
        if (
            message.guild
            and self.bot.user in message.mentions
            and not self.ticket_pattern.match(message.channel.name)
        ):
            async with message.channel.typing():
                await asyncio.sleep(1.5)
                assistant = self.get_assistant(message.channel.id)
                response = await assistant.get_response(message.content)
                await message.reply(response, mention_author=True)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        """Clean up assistant when a ticket channel is deleted"""
        if channel.id in self.assistants:
            del self.assistants[channel.id]
        
        # Clean up conversation tracking data
        if channel.id in self.ongoing_conversations:
            del self.ongoing_conversations[channel.id]
        if channel.id in self.last_activity:
            del self.last_activity[channel.id]

async def setup(bot):
    await bot.add_cog(TicketAIAssistant(bot))
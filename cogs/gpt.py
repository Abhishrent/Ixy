import discord
from discord.ext import commands
import os
import asyncio
from openai import OpenAI
import re
import json
from typing import List, Dict, Any, Literal
from datetime import datetime, timedelta
from utils.knowledge_base import get_system_prompt

# Path to store token usage data
TOKEN_DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../bot_memory/api_tokens.json")

class TokenManager:
    """Manages API tokens with rotation for rate limit handling"""
    
    def __init__(self):
        self.tokens = [
            "***REMOVED***",
            "***REMOVED***"
            # Add more tokens as needed
        ]
        self.token_data = self.load_token_data()
        self.current_token_index = self.get_next_available_token_index()
        
    def load_token_data(self) -> Dict[str, Any]:
        """Load token usage data from file or create if doesn't exist"""
        if os.path.exists(TOKEN_DATA_PATH):
            try:
                with open(TOKEN_DATA_PATH, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        
        # Initialize with default data if file doesn't exist or is invalid
        data = {"tokens": {}}
        for token in self.tokens:
            data["tokens"][token] = {
                "last_used": None,
                "rate_limited": False,
                "rate_limit_until": None
            }
        
        # Save the initial data
        self.save_token_data(data)
        return data
    
    def save_token_data(self, data=None):
        """Save token usage data to file"""
        if data is None:
            data = self.token_data
            
        os.makedirs(os.path.dirname(TOKEN_DATA_PATH), exist_ok=True)
        with open(TOKEN_DATA_PATH, 'w') as f:
            json.dump(data, f, indent=2)
    
    def get_next_available_token_index(self) -> int:
        """Find the next available token that isn't rate limited"""
        now = datetime.now().isoformat()
        
        # First, check if any rate-limited tokens need to be refreshed
        self.refresh_tokens()
        
        # Try to find a non-rate-limited token
        for i, token in enumerate(self.tokens):
            token_info = self.token_data["tokens"].get(token, {
                "last_used": None,
                "rate_limited": False,
                "rate_limit_until": None
            })
            
            if not token_info["rate_limited"]:
                # Update last used time
                token_info["last_used"] = now
                self.token_data["tokens"][token] = token_info
                self.save_token_data()
                return i
        
        # If all tokens are rate limited, use the first one
        # (it might work again if enough time has passed)
        return 0
    
    def refresh_tokens(self):
        """Check if any rate-limited tokens can be used again"""
        now = datetime.now()
        updated = False
        
        for token in self.tokens:
            token_info = self.token_data["tokens"].get(token, {})
            
            # Skip tokens that aren't rate limited
            if not token_info.get("rate_limited", False):
                continue
            
            # Check if the rate limit has expired
            rate_limit_until = token_info.get("rate_limit_until")
            if rate_limit_until:
                limit_time = datetime.fromisoformat(rate_limit_until)
                if now >= limit_time:
                    # Reset rate limit
                    token_info["rate_limited"] = False
                    token_info["rate_limit_until"] = None
                    self.token_data["tokens"][token] = token_info
                    updated = True
        
        if updated:
            self.save_token_data()
    
    def get_current_token(self) -> str:
        """Get the current token to use"""
        return self.tokens[self.current_token_index]
    
    def mark_token_rate_limited(self, token: str, hours: int = 24):
        """Mark a token as rate limited until specified hours later"""
        if token in self.tokens:
            rate_limit_until = (datetime.now() + timedelta(hours=hours)).isoformat()
            
            self.token_data["tokens"][token] = {
                "last_used": datetime.now().isoformat(),
                "rate_limited": True,
                "rate_limit_until": rate_limit_until
            }
            
            self.save_token_data()
            
            # Move to the next token
            self.current_token_index = self.get_next_available_token_index()
    
    def rotate_token(self):
        """Move to the next available token"""
        self.current_token_index = self.get_next_available_token_index()
        return self.tokens[self.current_token_index]

class AIAssistant:
    """Handle AI-powered interactions using Azure-based OpenAI API"""
    
    def __init__(self):
        # Set up token manager for API access
        self.token_manager = TokenManager()
        self._setup_client()
        
        self.model = "gpt-4o"
        # REMOVE cached system prompt; will fetch dynamically via property
        # self.system_prompt = get_system_prompt()
        self.context_window = []  # Store recent conversation history
        self.max_context_messages = 10  # Maximum number of messages to keep in context
        # NEW: Track event config file for real-time updates / context reset
        self._event_config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "event_config.json")
        self._last_config_mtime = self._get_config_mtime()
    
    def _get_config_mtime(self):
        try:
            return os.path.getmtime(self._event_config_path)
        except OSError:
            return None
    
    @property
    def system_prompt(self):
        """Always fetch the latest system prompt; reset context if config changed."""
        current_mtime = self._get_config_mtime()
        if current_mtime and current_mtime != self._last_config_mtime:
            self.context_window.clear()
            self._last_config_mtime = current_mtime
        return get_system_prompt()
    
    def _setup_client(self):
        """Set up the OpenAI client with the current token"""
        token = self.token_manager.get_current_token()
        os.environ["GITHUB_TOKEN"] = token
        self.client = OpenAI(
            base_url="https://models.inference.ai.azure.com",
            api_key=token
        )
    
    def update_context(self, role: str, content: str):
        """Update conversation context window"""
        self.context_window.append({"role": role, "content": content})
        
        # Trim context if it's too long, keeping the system prompt
        if len(self.context_window) > self.max_context_messages:
            # Remove oldest message (but never the system prompt)
            self.context_window.pop(1)  # Index 0 is system prompt
    
    async def get_response(self, query: str, max_retries: int = 3) -> str:
        """Get AI response to user query with token rotation support"""
        retries = 0
        
        while retries < max_retries:
            try:
                # Prepare messages with system prompt and context
                messages = [{"role": "system", "content": self.system_prompt}]
                messages.extend(self.context_window)
                messages.append({"role": "user", "content": query})
                
                response = self.client.chat.completions.create(
                    messages=messages,
                    model=self.model,
                    temperature=0.7,
                    max_tokens=500
                )
                
                ai_response = response.choices[0].message.content
                
                # Update context with this interaction
                self.update_context("user", query)
                self.update_context("assistant", ai_response)
                
                return ai_response
            
            except Exception as e:
                error_msg = str(e).lower()
                
                # Check for rate limit in error message
                if "rate" in error_msg and "limit" in error_msg:
                    # Handle rate limit by switching tokens
                    current_token = self.token_manager.get_current_token()
                    print(f"Token {current_token[:10]}... hit rate limit. Rotating to next token.")
                    self.token_manager.mark_token_rate_limited(current_token)
                    self._setup_client()  # Reinitialize client with new token
                    retries += 1
                    
                # Check for authentication errors
                elif "auth" in error_msg or "invalid" in error_msg or "key" in error_msg:
                    # Authentication issues - token might be invalid
                    current_token = self.token_manager.get_current_token()
                    print(f"Token {current_token[:10]}... authentication failed. Rotating to next token.")
                    self.token_manager.mark_token_rate_limited(current_token)
                    self._setup_client()  # Reinitialize client with new token
                    retries += 1
                    
                else:
                    print(f"Error in AI response generation: {str(e)}")
                    return "I'm having trouble processing your request. Please try again or contact the organizing committee for assistance."
        
        return "I've reached my usage limits for now. Please contact the organizing committee for assistance."

class TicketAIAssistant(commands.Cog):
    """Cog to provide AI assistance in ticket channels and reply-on-mention in public channels"""
    
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
        self.enabled = True  # NEW: Global toggle for AI responses

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
    
    # Remove group-based ai_assist commands and revert to single command with a choice parameter
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
            # Don't respond to commands
            if message.content.startswith(tuple(self.bot.command_prefix)):
                return

            # Update conversation tracking
            is_staff = self.is_staff(message.author)
            self.update_conversation_state(message.channel.id, message.author.id, is_staff)

            # Check if we should respond
            if not self.should_ai_respond(message.channel.id, message):
                return

            # Process the message with AI
            async with message.channel.typing():
                await asyncio.sleep(1.5)
                assistant = self.get_assistant(message.channel.id)
                response = await assistant.get_response(message.content)
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
            return

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

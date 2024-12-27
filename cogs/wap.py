import discord
from discord.ext import commands
from discord.ext.commands import HybridCommand
import os
from openai import OpenAI

class WapCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # List of API keys to manage
        self.api_keys = [
            "***REDACTED_GITHUB_TOKEN***",
            "***REDACTED_GITHUB_TOKEN***",
        ]
        self.current_key_index = 0

        # Ensure at least one API key is available
        if not self.api_keys:
            raise ValueError("No API keys provided.")

        # Set the first API key
        self.set_api_key(self.api_keys[self.current_key_index])

    def set_api_key(self, api_key):
        """Set the API key and initialize the OpenAI client."""
        self.api_key = api_key
        os.environ["GITHUB_TOKEN"] = self.api_key
        self.client = OpenAI(
            base_url="https://models.inference.ai.azure.com",
            api_key=self.api_key,
        )

    def switch_to_next_key(self):
        """Switch to the next available API key."""
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        self.set_api_key(self.api_keys[self.current_key_index])
        print(f"Switched to API key: {self.api_keys[self.current_key_index]}")

    @commands.hybrid_command()
    async def wap(self, ctx, *, to: str):
        """Generates code based on the user's input."""
        
        # Start typing indicator
        async with ctx.typing():
            while True:
                try:
                    # Send the user prompt to the AI model
                    response = self.client.chat.completions.create(
                        messages=[{"role": "system", "content": "Generate ready-to-run code with detailed comments."},
                                  {"role": "user", "content": to + "\nsend the code only without explanation"}],
                        model="gpt-4o",
                        temperature=1,
                        max_tokens=4096,
                        top_p=1,
                    )

                    # Extract the response content
                    generated_code = response.choices[0].message.content

                    # Send the generated code back to the user
                    if len(generated_code) > 2000:  # Discord message limit
                        await ctx.send("The generated code is too long to send in one message. Sending as a file.")
                        with open("generated_code.py", "w") as f:
                            f.write(generated_code)
                        await ctx.send(file=discord.File("generated_code.py"))
                    else:
                        await ctx.send(f"{generated_code}")
                    
                    # Break the loop if successful
                    break

                except Exception as e:
                    if "rate limit" in str(e).lower():
                        await ctx.send("Rate limit reached. Switching API keys...")
                        self.switch_to_next_key()
                    else:
                        await ctx.send(f"An error occurred: {e}")
                        break

# Setup function to add the cog to the bot
async def setup(bot):
    await bot.add_cog(WapCog(bot))

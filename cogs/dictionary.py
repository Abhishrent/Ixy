import discord
from discord.ext import commands
import requests
import re  # Import the regular expression module

class CollegiateDictionary(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_url = "https://dictionaryapi.com/api/v3/references/collegiate/json/"
        self.api_key = "***REMOVED***"  # Replace with your actual API key

    @commands.hybrid_command(name="define", help="Get the definition of a word using Merriam-Webster's Collegiate Dictionary.")
    async def define(self, ctx, word: str):
        """
        Fetch the definition of a word using Merriam-Webster's API with a detailed embed.
        """
        if not word:
            embed = discord.Embed(
                title="❌ Word Missing",
                description="Please provide a word to define. Usage: `/define <word>` or `!define <word>`",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        async with ctx.typing():
            try:
                response = requests.get(
                    f"{self.api_url}{word}?key={self.api_key}",
                    timeout=10
                )
                
                if response.status_code != 200:
                    embed = discord.Embed(
                        title="🚨 API Error",
                        description=f"Received status code {response.status_code}.",
                        color=discord.Color.dark_red()
                    )
                    await ctx.send(embed=embed)
                    return

                data = response.json()
                
                if not data:
                    embed = discord.Embed(
                        title="🔍 No Results",
                        description=f"No definitions found for the word '{word}'.",
                        color=discord.Color.orange()
                    )
                    await ctx.send(embed=embed)
                    return

                if isinstance(data[0], str):
                    suggestions = ', '.join(data[:5])
                    embed = discord.Embed(
                        title="🤔 Did You Mean?",
                        description=f"No exact match found. Suggestions: {suggestions}",
                        color=discord.Color.gold()
                    )
                    await ctx.send(embed=embed)
                    return

                # Create a rich embed with more details
                embed = discord.Embed(
                    title=f"📘 Definition of '{word.capitalize()}'",
                    color=discord.Color.blue()
                )

                # Add primary definitions
                definitions = data[0].get("shortdef", [])
                if definitions:
                    definition_text = "\n".join([f"{i+1}. {defn}" for i, defn in enumerate(definitions)])
                    embed.description = definition_text

                # Add additional metadata if available
                if 'meta' in data[0]:
                    # Add pronunciation if available
                    if 'pronunciation' in data[0]['meta']:
                        pron = data[0]['meta'].get('pronunciation', {}).get('mw', 'Not available')
                        embed.add_field(name="🔊 Pronunciation", value=f"`{pron}`", inline=False)

                    # Add word type
                    if 'fl' in data[0]:
                        embed.add_field(name="📝 Part of Speech", value=data[0]['fl'], inline=True)

                # Add etymology if available and clean it up
                if 'et' in data[0]:
                    etymology = ' '.join(data[0]['et'][0]) if data[0]['et'] else "Not available"
                    # Use regular expression to remove {it} and {/it} tags
                    etymology_cleaned = re.sub(r'\{it\}(.*?)\{\/it\}', r'\1', etymology)
                    embed.add_field(name="📜 Etymology", value=etymology_cleaned, inline=False)

                # Set footer and thumbnail
                embed.set_footer(
                    text='Powered by Merriam-Webster Dictionary', 
                    icon_url='https://dictionaryapi.com/images/MWLogo_120x120.png'
                )
                embed.set_thumbnail(url='https://dictionaryapi.com/images/MWLogo_120x120.png')

                await ctx.send(embed=embed)

            except requests.RequestException as e:
                embed = discord.Embed(
                    title="🌐 Network Error",
                    description=f"Could not connect to the dictionary service: {e}",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
            except Exception as e:
                embed = discord.Embed(
                    title="❗ Unexpected Error",
                    description=f"An error occurred: {e}",
                    color=discord.Color.dark_red()
                )
                await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(CollegiateDictionary(bot))

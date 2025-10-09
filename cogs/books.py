import discord
from discord.ext import commands
import aiohttp
import os

class Books(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.base_url = "https://openlibrary.org"

    async def get_work_description(self, work_key):
        """Fetch detailed description from the works API."""
        if not work_key:
            return "No description available."
        
        work_url = f"{self.base_url}{work_key}.json"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(work_url) as response:
                    if response.status == 200:
                        work_data = await response.json()
                        description = work_data.get("description")
                        if isinstance(description, dict):
                            description = description.get("value", "No description available.")
                        elif isinstance(description, str):
                            description = description
                        else:
                            description = "No description available."
                        
                        # Return full description without limiting length
                        return description
        except:
            pass
        return "No description available."

    @commands.hybrid_group(name="book", description="Book-related commands")
    async def book(self, ctx):
        """Book command group for searching and discovering books."""
        if ctx.invoked_subcommand is None:
            await ctx.send("Please use a subcommand. Available: `search`, `author`")

    @book.command(name="search", description="Search for a book by title.")
    async def search_book(self, ctx, *, book_title: str):
        """Search for a book by title."""
        url = f"{self.base_url}/search.json"
        params = {"title": book_title, "limit": 1}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    await ctx.send("Failed to fetch book data.", ephemeral=True)
                    return

                data = await response.json()
                docs = data.get("docs", [])

                if not docs:
                    await ctx.send("No books found with that title.", ephemeral=True)
                    return

                # Display the first result
                book = docs[0]
                title = book.get("title", "N/A")
                authors = ", ".join(book.get("author_name", ["Unknown author"]))
                first_publish_year = book.get("first_publish_year", "Unknown")
                publisher = ", ".join(book.get("publisher", ["Unknown publisher"])[:3])
                language = ", ".join(book.get("language", ["Unknown"])[:3])
                
                # Get description from works API
                work_key = book.get("key")
                description = await self.get_work_description(work_key)
                
                # Get cover image if available
                cover_id = book.get("cover_i")
                cover_url = f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg" if cover_id else None

                embed = discord.Embed(
                    title=title,
                    description=f"**First Published:** {first_publish_year}\n\n{description}",
                    color=discord.Color.blue()
                )
                embed.add_field(name="Authors", value=authors, inline=True)
                embed.add_field(name="Publisher(s)", value=publisher, inline=True)
                embed.add_field(name="Language(s)", value=language.upper(), inline=True)
                
                if cover_url:
                    embed.set_image(url=cover_url)

                await ctx.send(embed=embed)

    @book.command(name="author", description="Search for author information.")
    async def search_author(self, ctx, *, author_name: str):
        """Search for author information by name."""
        url = f"{self.base_url}/search.json"
        params = {"author": author_name, "limit": 1}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    await ctx.send("Failed to fetch author data.", ephemeral=True)
                    return

                data = await response.json()
                docs = data.get("docs", [])

                if not docs:
                    await ctx.send("No books found by that author.", ephemeral=True)
                    return

                # Get author information from the first book result
                book = docs[0]
                authors = book.get("author_name", [])
                author_keys = book.get("author_key", [])
                
                if not authors:
                    await ctx.send("No author information available.", ephemeral=True)
                    return

                # Use the first author
                author_name_result = authors[0]
                author_key = author_keys[0] if author_keys else None
                
                bio = "No biography available."
                birth_date = "Unknown"
                death_date = "Unknown"
                
                if author_key:
                    # Fetch detailed author information using author key
                    author_url = f"{self.base_url}/authors/{author_key}.json"
                    async with session.get(author_url) as author_response:
                        if author_response.status == 200:
                            author_data = await author_response.json()
                            
                            # Get biography
                            bio_data = author_data.get("bio")
                            if isinstance(bio_data, dict):
                                bio = bio_data.get("value", "No biography available.")
                            elif isinstance(bio_data, str):
                                bio = bio_data

                            # Get birth and death dates
                            birth_date = author_data.get("birth_date", "Unknown")
                            death_date = author_data.get("death_date", "Unknown")

                embed = discord.Embed(
                    title=author_name_result,
                    description=bio,
                    color=discord.Color.green()
                )
                
                # Format life span
                life_span = f"{birth_date}"
                if death_date != "Unknown":
                    life_span += f" - {death_date}"
                elif birth_date != "Unknown":
                    life_span += " - Present"
                else:
                    life_span = "Unknown"
                
                embed.add_field(name="Life Span", value=life_span, inline=True)

                await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Books(bot))
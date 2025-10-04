import discord
from discord.ext import commands
import aiohttp

class TMDB(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_key = "7f292712169d8c5a751e6f5a188001cc"
        self.api_token = "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI3ZjI5MjcxMjE2OWQ4YzVhNzUxZTZmNWExODgwMDFjYyIsIm5iZiI6MTc1OTU4MzI4OS45NjEsInN1YiI6IjY4ZTExYzM5NjVhZWNjOThhOTljYTNhMCIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.EsE9dy_NNqma4WjgTm_iXxhSIIvE6Ni2lc5I_RcZrmc"
        self.base_url = "https://api.themoviedb.org/3"

    @commands.hybrid_command(name="search_movie", description="Search for a movie by title.")
    async def search_movie(self, ctx, *, movie_title: str):
        """Search for a movie by title."""
        url = f"{self.base_url}/search/movie"
        headers = {"Authorization": self.api_token}
        params = {"query": movie_title}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                if response.status != 200:
                    await ctx.interaction.response.send_message(
                        "Failed to fetch data from TMDB.", ephemeral=True
                    )
                    return

                data = await response.json()
                results = data.get("results", [])

                if not results:
                    await ctx.interaction.response.send_message(
                        "No movies found with that title.", ephemeral=True
                    )
                    return

                # Display the first result
                movie = results[0]
                title = movie.get("title", "N/A")
                overview = movie.get("overview", "No description available.")
                release_date = movie.get("release_date", "Unknown release date.")
                rating = movie.get("vote_average", "N/A")
                vote_count = movie.get("vote_count", "N/A")
                popularity = movie.get("popularity", "N/A")
                language = movie.get("original_language", "N/A").upper()
                poster_path = movie.get("poster_path")
                poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None
                backdrop_path = movie.get("backdrop_path")
                backdrop_url = f"https://image.tmdb.org/t/p/w1280{backdrop_path}" if backdrop_path else None
                is_adult = "Yes" if movie.get("adult", False) else "No"

                embed = discord.Embed(
                    title=title,
                    description=overview,
                    color=discord.Color.blue()
                )
                embed.add_field(name="Release Date", value=release_date, inline=True)
                embed.add_field(name="Rating", value=f"{rating}/10", inline=True)
                embed.add_field(name="Number of Ratings", value=vote_count, inline=True)
                embed.add_field(name="Popularity", value=popularity, inline=True)
                embed.add_field(name="Language", value=language, inline=True)
                embed.add_field(name="18+ Movie", value=is_adult, inline=True)
                if poster_url:
                    embed.set_thumbnail(url=poster_url)
                if backdrop_url:
                    embed.set_image(url=backdrop_url)

                # embed.set_footer(text="Powered by TMDB")
                await ctx.send(embed=embed)

    @commands.hybrid_command(name="recommend_movie", description="Get movie recommendations based on a movie title.")
    async def recommend_movie(self, ctx, *, movie_title: str):
        """Get movie recommendations based on a movie title."""
        # Search for the movie to get its ID
        search_url = f"{self.base_url}/search/movie"
        headers = {"Authorization": self.api_token}
        search_params = {"query": movie_title}

        async with aiohttp.ClientSession() as session:
            async with session.get(search_url, headers=headers, params=search_params) as search_response:
                if search_response.status != 200:
                    await ctx.interaction.response.send_message(
                        "Failed to fetch data from TMDB.", ephemeral=True
                    )
                    return

                search_data = await search_response.json()
                search_results = search_data.get("results", [])

                if not search_results:
                    await ctx.interaction.response.send_message(
                        "No movies found with that title.", ephemeral=True
                    )
                    return

                # Get the ID of the first matching movie
                movie_id = search_results[0].get("id")

                if not movie_id:
                    await ctx.send("Could not find recommendations for the given movie.")
                    return

            # Fetch recommendations based on the movie ID
            recommend_url = f"{self.base_url}/movie/{movie_id}/recommendations"
            async with session.get(recommend_url, headers=headers) as recommend_response:
                if recommend_response.status != 200:
                    await ctx.interaction.response.send_message(
                        "Failed to fetch recommendations from TMDB.", ephemeral=True
                    )
                    return

                recommend_data = await recommend_response.json()
                recommendations = recommend_data.get("results", [])

                if not recommendations:
                    await ctx.interaction.response.send_message(
                        "No recommendations found for this movie.", ephemeral=True
                    )
                    return

                # Create an embed with the list of recommended titles
                embed = discord.Embed(
                    title=f"Recommendations based on '{movie_title}':",
                    color=discord.Color.green()
                )
                for index, movie in enumerate(recommendations[:10], start=1):  # Show up to 10 titles
                    title = movie.get("title", "N/A")
                    release_date = movie.get("release_date", "Unknown release date.")
                    embed.add_field(
                        name=f"{index}. {title}",
                        value=f"Release Date: {release_date}",
                        inline=False
                    )

                # Create a dropdown for the recommendations
                class RecommendationDropdown(discord.ui.Select):
                    def __init__(self, movies):
                        options = [
                            discord.SelectOption(
                                label=movie.get("title", "N/A"),
                                description=movie.get("release_date", "Unknown release date."),
                                value=str(index)
                            )
                            for index, movie in enumerate(movies[:25])  # Discord allows up to 25 options
                        ]
                        super().__init__(placeholder="Select a movie to view details...", options=options)

                        self.movies = movies

                    async def callback(self, interaction: discord.Interaction):
                        index = int(self.values[0])
                        movie = self.movies[index]

                        # Create a detailed embed for the selected movie
                        title = movie.get("title", "N/A")
                        overview = movie.get("overview", "No description available.")
                        release_date = movie.get("release_date", "Unknown release date.")
                        rating = movie.get("vote_average", "N/A")
                        vote_count = movie.get("vote_count", "N/A")
                        popularity = movie.get("popularity", "N/A")
                        language = movie.get("original_language", "N/A").upper()
                        poster_path = movie.get("poster_path")
                        poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None
                        backdrop_path = movie.get("backdrop_path")
                        backdrop_url = f"https://image.tmdb.org/t/p/w1280{backdrop_path}" if backdrop_path else None
                        is_adult = "Yes" if movie.get("adult", False) else "No"

                        embed = discord.Embed(
                            title=title,
                            description=overview,
                            color=discord.Color.blue()
                        )
                        embed.add_field(name="Release Date", value=release_date, inline=True)
                        embed.add_field(name="Rating", value=f"{rating}/10", inline=True)
                        embed.add_field(name="Number of Ratings", value=vote_count, inline=True)
                        embed.add_field(name="Popularity", value=popularity, inline=True)
                        embed.add_field(name="Language", value=language, inline=True)
                        embed.add_field(name="18+ Movie", value=is_adult, inline=True)
                        if poster_url:
                            embed.set_thumbnail(url=poster_url)
                        if backdrop_url:
                            embed.set_image(url=backdrop_url)

                        await interaction.response.edit_message(embed=embed, view=self.view)

                class RecommendationView(discord.ui.View):
                    def __init__(self, movies):
                        super().__init__()
                        self.add_item(RecommendationDropdown(movies))

                # Send the embed and dropdown to the user
                await ctx.send(
                    embed=embed,
                    view=RecommendationView(recommendations)
                )

async def setup(bot):
    await bot.add_cog(TMDB(bot))

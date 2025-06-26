import discord
from discord.ext import commands
from config import EMBED_THUMBNAIL, EMBED_FOOTER, EMBED_IMAGE

class TestEmbed(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="testembed", description="Preview a sample embed with the standard logo.")
    async def test_embed(self, ctx):
        embed = discord.Embed(
            title="Sample Embed Title",
            description="This is a preview of how embeds will look with the standard logo.",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=EMBED_THUMBNAIL)
        embed.set_image(url=EMBED_IMAGE)
        embed.add_field(name="Field 1", value="Some value here", inline=True)
        embed.add_field(name="Field 2", value="Another value here", inline=True)
        embed.set_footer(text="Embed Footer Example", icon_url=EMBED_FOOTER)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(TestEmbed(bot))

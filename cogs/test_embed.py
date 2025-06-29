import discord
from discord.ext import commands
from config import EMBED_THUMBNAIL, EMBED_FOOTER, EMBED_IMAGE

class AdvancedEmbedView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)

    @discord.ui.select(
        placeholder="Choose an option...",
        min_values=1,
        max_values=1,
        options=[
            discord.SelectOption(label="Option 1", description="Shows Option 1 details", emoji="🟢"),
            discord.SelectOption(label="Option 2", description="Shows Option 2 details", emoji="🔵"),
            discord.SelectOption(label="Option 3", description="Shows Option 3 details", emoji="🟣"),
        ]
    )
    async def select_callback(self, select: discord.ui.Select, interaction: discord.Interaction):
        value = select.values[0]
        embed = discord.Embed(
            title=f"You selected: {value}",
            description=f"Details for **{value}**.",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=EMBED_THUMBNAIL)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Surprise!", style=discord.ButtonStyle.primary, emoji="🎉")
    async def surprise_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🎉 Surprise!",
            description="You clicked the button!",
            color=discord.Color.gold()
        )
        embed.set_image(url=EMBED_IMAGE)
        embed.set_footer(text="Enjoy your surprise!", icon_url=EMBED_FOOTER)
        await interaction.response.edit_message(embed=embed, view=self)

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
        embed.set_image(url="https://cdn.discordapp.com/attachments/1386734833761390642/1388505211621867551/Untitled_design2.gif?ex=686139bf&is=685fe83f&hm=67aecc5ca2607193c75bf891cb47a7f40e3947eb1216181791aa7df8ea291117&")
        embed.add_field(name="Field 1", value="Some value here", inline=True)
        embed.add_field(name="Field 2", value="Another value here", inline=True)
        embed.set_footer(text="Embed Footer Example", icon_url=EMBED_FOOTER)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="testembed2", description="Preview an advanced embed with dropdowns and buttons.")
    async def test_embed2(self, ctx):
        embed = discord.Embed(
            title="Advanced Embed Demo",
            description="This embed shows off advanced Discord UI features:\n- Dropdown (Select menu)\n- Button\n- Thumbnail, Image, Footer, Fields",
            color=discord.Color.purple()
        )
        embed.set_thumbnail(url=EMBED_THUMBNAIL)
        embed.set_image(url=EMBED_IMAGE)
        embed.add_field(name="Dropdown", value="Try selecting an option below!", inline=False)
        embed.add_field(name="Button", value="Or click the button for a surprise.", inline=False)
        embed.set_footer(text="Advanced Embed Footer", icon_url=EMBED_FOOTER)
        view = AdvancedEmbedView()
        await ctx.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(TestEmbed(bot))

import discord
from discord.ext import commands
import requests
from config import EMBED_THUMBNAIL

class Astro(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.nepali_signs = {
            'aries': 'मेष',
            'taurus': 'वृष',
            'gemini': 'मिथुन',
            'cancer': 'कर्कट',
            'leo': 'सिंह',
            'virgo': 'कन्या',
            'libra': 'तुला',
            'scorpio': 'वृश्चिक',
            'sagittarius': 'धनु',
            'capricorn': 'मकर',
            'aquarius': 'कुम्भ',
            'pisces': 'मीन'
        }

    def create_rashi_view(self):
        """Create a view with a dropdown for all rashis"""
        view = discord.ui.View()
        options = [
            discord.SelectOption(label=rashi_value, value=rashi_key)
            for rashi_key, rashi_value in self.nepali_signs.items()
        ]
        select = RashiDropdown(options, self)
        view.add_item(select)
        return view

    async def rashi_button_callback(self, interaction: discord.Interaction):
        """Callback for rashi buttons"""
        sign = interaction.data['custom_id']
        await self.send_horoscope(sign, interaction=interaction)

    async def send_horoscope(self, sign: str, ctx=None, interaction=None):
        """Generic method to send horoscope for a given sign"""
        # Validate sign
        if sign.lower() not in self.nepali_signs:
            # Prepare error embed with rashi selection view
            error_embed = discord.Embed(
                title=f"Invalid rashi: '{sign}'",
                color=discord.Color.red()
            )
            error_embed.set_thumbnail(url=EMBED_THUMBNAIL)
            view = self.create_rashi_view()
            
            # Send error message based on context
            if ctx:
                await ctx.send(embed=error_embed, view=view)
            elif interaction:
                await interaction.response.send_message(embed=error_embed, view=view, ephemeral=True)
            return

        try:
            # Fetch horoscope data
            api_url = 'https://nepalipatro.com.np/rashifal/getv5/type/D?lang=np'
            response = requests.get(api_url)
            data = response.json()
            horoscope_data = data['np'][0]
            
            # Extract horoscope details
            horoscope_message = horoscope_data.get(sign.lower(), "Sorry, I couldn't find a horoscope for that sign.")
            current_date = horoscope_data.get('todate')
            nepali_sign = self.nepali_signs.get(sign.lower(), sign.capitalize())

            # Create horoscope embed
            horoscope_embed = discord.Embed(
                title=f'{nepali_sign}',
                description=f'मिती: {current_date} \n{horoscope_message}',
                color=discord.Color.blue()
            )
            horoscope_embed.set_thumbnail(url=EMBED_THUMBNAIL)
            horoscope_embed.set_footer(text='Powered by Nepali Patro', icon_url='https://imgs.search.brave.com/Czd9eg6t12aqBY8yELbNiMfkijeQUDujIdxTAgNqyWE/rs:fit:860:0:0:0/g:ce/aHR0cHM6Ly9wbGF5/LWxoLmdvb2dsZXVz/ZXJjb250ZW50LmNv/bS9HQWx6angwSFZf/OUtWYWZQcnRjT1I5/NGZZYk00U1Z6OFdh/WENFc2Njb1V6eVlP/dThLOUlIMVVZSHZm/TUhOUFRnU1NRPXcy/NDAtaDQ4MC1ydw')
            
            # Create view with rashi buttons
            view = self.create_rashi_view()
            
            # Send message based on context
            if ctx:
                await ctx.send(embed=horoscope_embed, view=view)
            elif interaction:
                await interaction.response.send_message(embed=horoscope_embed, view=view)

        except requests.exceptions.RequestException as e:
            error_msg = "Error fetching horoscope data. Please try again later."
            if ctx:
                await ctx.send(error_msg)
            elif interaction:
                await interaction.response.send_message(error_msg, ephemeral=True)
            print(f"Request error: {e}")

    @commands.hybrid_command(name='rashi', description='Get your daily horoscope')
    @discord.app_commands.describe(sign='Select your zodiac sign')
    @discord.app_commands.choices(sign=[
        discord.app_commands.Choice(name='Aries (मेष)', value='aries'),
        discord.app_commands.Choice(name='Taurus (वृष)', value='taurus'),
        discord.app_commands.Choice(name='Gemini (मिथुन)', value='gemini'),
        discord.app_commands.Choice(name='Cancer (कर्कट)', value='cancer'),
        discord.app_commands.Choice(name='Leo (सिंह)', value='leo'),
        discord.app_commands.Choice(name='Virgo (कन्या)', value='virgo'),
        discord.app_commands.Choice(name='Libra (तुला)', value='libra'),
        discord.app_commands.Choice(name='Scorpio (वृश्चिक)', value='scorpio'),
        discord.app_commands.Choice(name='Sagittarius (धनु)', value='sagittarius'),
        discord.app_commands.Choice(name='Capricorn (मकर)', value='capricorn'),
        discord.app_commands.Choice(name='Aquarius (कुम्भ)', value='aquarius'),
        discord.app_commands.Choice(name='Pisces (मीन)', value='pisces')
    ])
    async def rashi(self, ctx, sign: str):
        # If no sign provided, show selection view
        if not sign:
            no_sign_embed = discord.Embed(
                title="Choose Your Rashi",
                color=discord.Color.blue()
            )
            no_sign_embed.set_thumbnail(url=EMBED_THUMBNAIL)
            view = self.create_rashi_view()
            await ctx.send(embed=no_sign_embed, view=view)
            return

        # Use the centralized send_horoscope method
        await self.send_horoscope(sign, ctx=ctx)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        if message.content.strip().lower() == "cutu rashi":
            embed = discord.Embed(
                title="Reminder 🔔",
                description="You forgot to include your rashi!",
                color=discord.Color.orange()
            )
            embed.set_thumbnail(url=EMBED_THUMBNAIL)
            await message.channel.send(embed=embed)

# Dropdown (Select) class for rashi selection
class RashiDropdown(discord.ui.Select):
    def __init__(self, options, astro_cog):
        super().__init__(placeholder="राशि छान्नुहोस्...", min_values=1, max_values=1, options=options)
        self.astro_cog = astro_cog

    async def callback(self, interaction: discord.Interaction):
        sign = self.values[0]
        await self.astro_cog.send_horoscope(sign, interaction=interaction)

# Add the bot instance to the command prefix and load the cog
async def setup(bot):
    await bot.add_cog(Astro(bot))
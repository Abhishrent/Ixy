import discord
from discord.ext import commands
from discord.ui import Button, View
import requests
import json
import os
from typing import List
from config import EMBED_THUMBNAIL

def load_currency_codes():
    """Load currency codes from JSON file"""
    try:
        currency_codes_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'bot_memory', 'currency_codes.json')
        with open(currency_codes_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("Warning: currency_codes.json not found, using empty dict")
        return {}
    except json.JSONDecodeError:
        print("Warning: Invalid JSON in currency_codes.json, using empty dict")
        return {}

# Load currency codes at module level
CURRENCY_CODES = load_currency_codes()

# Country Codes View with "View Country Codes" button
class CountryCodesView(View):
    def __init__(self):
        super().__init__()
        self.add_item(Button(label="View Country Codes", style=discord.ButtonStyle.primary, custom_id="view_codes"))

    async def interaction_check(self, interaction: discord.Interaction):
        # When the "View Country Codes" button is clicked, show the letter buttons
        letter_buttons = []
        for letter in CURRENCY_CODES.keys():
            button = Button(label=letter, style=discord.ButtonStyle.secondary, custom_id=f"letter_{letter}")
            letter_buttons.append(button)
            button.callback = self.create_letter_button_callback(letter)  # Attach callback for each letter

        # Create a new view with letter buttons
        view = View()
        for button in letter_buttons:
            view.add_item(button)

        # Send an ephemeral message with the letter buttons
        await interaction.response.send_message(
            content="**Select Option:**",
            view=view,
            ephemeral=True
        )

    def create_letter_button_callback(self, letter: str):
        """Generate callback for each letter button."""
        async def letter_button_callback(interaction: discord.Interaction):
            # Get the list of countries and their codes that start with the letter
            countries = CURRENCY_CODES.get(letter, [])
            country_list = "\n".join([f"{name} - {code}" for name, code in countries]) if countries else "No countries available."

            # Create the embed for the selected letter
            embed = discord.Embed(
                title=f"Countries starting with '{letter}'",
                description=country_list,
                color=discord.Color.green(),
            )
            embed.set_thumbnail(url=EMBED_THUMBNAIL)

            # Send the embed as an ephemeral message
            await interaction.response.send_message(embed=embed, ephemeral=True)
        return letter_button_callback

# Currency Converter Cog
class CurrencyConverterCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.country_currency_map = self._build_country_currency_map()

    def _build_country_currency_map(self) -> dict:
        """Build a comprehensive map of countries to their currencies."""
        country_map = {}
        for letter_group in CURRENCY_CODES.values():
            for country, currency in letter_group:
                # Handle cases with multiple entries for same country
                if country not in country_map:
                    country_map[country] = currency
        return country_map

    def get_country_choices(self) -> List[str]:
        """Generate country name choices"""
        return sorted(list(self.country_currency_map.keys()))

    def get_currency_for_country(self, country_name: str) -> str:
        """Get currency code for a given country name"""
        # Exact match first
        if country_name in self.country_currency_map:
            return self.country_currency_map[country_name]
        
        # Case-insensitive partial match
        for country, currency in self.country_currency_map.items():
            if country_name.lower() in country.lower():
                return currency
        
        return ""

    @commands.hybrid_command(name='kati', description="Convert currency amounts")
    async def convert_currency(
        self, 
        ctx, 
        amount: float, 
        from_country: str, 
        to_country: str = "Nepal"
    ):
        # Get currency codes for countries
        from_currency = self.get_currency_for_country(from_country)
        to_currency = self.get_currency_for_country(to_country)

        # Validate currency codes
        if not from_currency or not to_currency:
            await ctx.send("Could not find currency for one or both countries.")
            return

        from_currency = from_currency.upper()
        to_currency = to_currency.upper()

        # Fetch exchange rate data
        url = f"https://api.exchangerate-api.com/v4/latest/{from_currency}"
        try:
            response = requests.get(url)
            data = response.json()
            if response.status_code != 200 or "error" in data:
                await ctx.send(f"Error: Unable to fetch exchange rates for {from_currency}.")
                return

            # Check if the target currency is valid
            if to_currency not in data['rates']:
                await ctx.send(f"Error: {to_currency} is not a supported currency.")
                return

            # Calculate converted amount
            conversion_rate = data['rates'][to_currency]
            converted_amount = amount * conversion_rate

            # Format numbers for better readability
            amount_formatted = "{:,.2f}".format(amount)
            converted_amount_formatted = "{:,.2f}".format(converted_amount)

            # Create the embed for the conversion result
            embed = discord.Embed(
                title=f"**{from_currency}** to **{to_currency}**",
                description="",
                color=discord.Color.blue()
            )
            embed.set_thumbnail(url=EMBED_THUMBNAIL)
            embed.add_field(name="Given Amount:", value=f"{amount_formatted} {from_currency}", inline=True)
            embed.add_field(name="Amounts to:", value=f"{converted_amount_formatted} {to_currency}", inline=True)
            embed.set_footer(text=f"Conversion Rate: 1 {from_currency} = {conversion_rate:.4f} {to_currency}")

            # Add the "View Country Codes" button
            view = CountryCodesView()
            await ctx.send(embed=embed, view=view)

        except requests.exceptions.RequestException as e:
            await ctx.send(f"Error: Could not connect to the exchange rate API. ({e})")

    @convert_currency.autocomplete('from_country')
    async def from_country_autocomplete(self, interaction: discord.Interaction, current: str):
        """Autocomplete for from_country"""
        choices = self.get_country_choices()
        return [
            discord.app_commands.Choice(name=country, value=country)
            for country in choices 
            if current.lower() in country.lower()
        ][:25]  # Discord allows max 25 choices

    @convert_currency.autocomplete('to_country')
    async def to_country_autocomplete(self, interaction: discord.Interaction, current: str):
        """Autocomplete for to_country"""
        choices = self.get_country_choices()
        return [
            discord.app_commands.Choice(name=country, value=country)
            for country in choices 
            if current.lower() in country.lower()
        ][:25]  # Discord allows max 25 choices

# Setup function to add the cog to the bot
async def setup(bot):
    await bot.add_cog(CurrencyConverterCog(bot))
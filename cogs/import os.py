import pycountry
import os
import json

# country_dict = {country.alpha_2.lower(): country.name for country in pycountry.countries}

# with open("bot_memory/country_codes.json", "w") as f:
#     json.dump(country_dict, f, indent=2)

print(pycountry.countries)
for country in pycountry.countries:
    print(country.name)
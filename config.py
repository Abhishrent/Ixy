from dotenv import load_dotenv

BOT_NAME = 'Cutu'
PREFIX = ('cutu ', 'Cutu ')
SPECIAL_DATES = {
    (11, 24): "Statistics I Exam",  # Example date: November 24
    (11, 29): "Semester Exams Begin",    # Example: Add more dates here
    (12, 25): "Siri ko Birthday",
    (4, 29): "Hmmmmmmmmm"
}

#Channel ID Settings
WELCOME_CHANNEL_ID = 1301495713753993226
ROLES_CHANNEL_ID = 1301505201223503892
GENERAL_CHANNEL_ID = 1295939872581750839

#Google Drive settings for the photo command
SERVICE_ACCOUNT_JSON = r'C:\Users\User\Desktop\Discord Bot\google_drive.json'
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
FOLDER_ID = '1TZTkvxRlQWaBe1SDgbLxbIz4mW5mXjxS'

#Logos and Banners
IDEAX_LOGO = 'https://cdn.discordapp.com/attachments/1303620918454779914/1303621095571591218/ideax_logo_white.png?ex=672c6b41&is=672b19c1&hm=e5bd4447cf9d51d30d06710962d1cc50ac64ff82e0ab851e6be2672504033e64&'
IDEAX_LOGO_X ='https://imgs.search.brave.com/YcCbxifteKyjMmobJVixxW_RiNUYr0DAFiGmdsGqKb0/rs:fit:860:0:0:0/g:ce/aHR0cHM6Ly93d3cu/aWRlYXgubWJtYy5l/ZHUubnAvaW1hZ2Vz/L2lkZWF4X3hfb25s/eS5zdmc' 
IDEAX_BANNER = 'https://i.giphy.com/media/v1.Y2lkPTc5MGI3NjExbGk1c243M2x2b2k2djZpdnZtOWMzemk2djAxdHYyZHlpdDZkMXBxOSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/3Otqo8qv0LkmdUDe7w/giphy.gif'
WELCOME_BANNER = 'https://i.giphy.com/media/v1.Y2lkPTc5MGI3NjExaG9tNjk1ZnBscGhhcTNmMGFoZTZpM3JtNzFuenk3NXl5NjdweTVycyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/xUPGGDNsLvqsBOhuU0/giphy.gif'


ABOUT_DESCRIPTION = f"""{BOT_NAME} started as a hobby project in the form of a no-code discord bot back in 2021 when the popularity of Among Us gained traction. With having discord as the main form of communication among friends, it became a fun little project for our server but was soon discarded due to limited flexibility. 

The development process started again in October of 2024 when I felt comfortable enough to work in python after I had learned the basics of the language and developed a decent enough knowledge to write and navigate around the code.

IdeaX 2025 is the first time Petu Bot is being hosted and running on this server for your help and entertainment. 

Thank you.
"""


#ISO 4217 codes for currency conversion
COUNTRY_CODES = {
"A": [
    ("Afghanistan", "AFN"),
    ("Albania", "ALL"),
    ("Algeria", "DZD"),
    ("American Samoa", "USD"),
    ("Andorra", "EUR"),
    ("Angola", "AOA"),
    ("Anguilla", "XCD"),
    ("Antarctica", "No universal currency"),
    ("Antigua and Barbuda", "XCD"),
    ("Argentina", "ARS"),
    ("Armenia", "AMD"),
    ("Aruba", "AWG"),
    ("Australia", "AUD"),
    ("Austria", "EUR"),
    ("Azerbaijan", "AZN")
],
"B": [
    ("Bahamas (The)", "BSD"),
    ("Bahrain", "BHD"),
    ("Bangladesh", "BDT"),
    ("Barbados", "BBD"),
    ("Belarus", "BYN"),
    ("Belgium", "EUR"),
    ("Belize", "BZD"),
    ("Benin", "XOF"),
    ("Bermuda", "BMD"),
    ("Bhutan", "BTN"),
    ("Bhutan (Indian Rupee)", "INR"),
    ("Bolivia (Plurinational State of)", "BOB"),
    ("Bolivia (Plurinational State of, Mvdol)", "BOV"),
    ("Bonaire, Sint Eustatius and Saba", "USD"),
    ("Bosnia and Herzegovina", "BAM"),
    ("Botswana", "BWP"),
    ("Bouvet Island", "NOK"),
    ("Brazil", "BRL"),
    ("British Indian Ocean Territory (The)", "USD"),
    ("Brunei Darussalam", "BND"),
    ("Bulgaria", "BGN"),
    ("Burkina Faso", "XOF"),
    ("Burundi", "BIF")
],
"C": [
    ("Cabo Verde", "CVE"),
    ("Cambodia", "KHR"),
    ("Cameroon", "XAF"),
    ("Canada", "CAD"),
    ("Cayman Islands (The)", "KYD"),
    ("Central African Republic (The)", "XAF"),
    ("Chad", "XAF"),
    ("Chile (Unidad de Fomento)", "CLF"),
    ("Chile", "CLP"),
    ("China", "CNY"),
    ("Christmas Island", "AUD"),
    ("Cocos (Keeling) Islands (The)", "AUD"),
    ("Colombia", "COP"),
    ("Colombia (Unidad de Valor Real)", "COU"),
    ("Comoros (The)", "KMF"),
    ("Congo (The Democratic Republic of the)", "CDF"),
    ("Congo (The)", "XAF"),
    ("Cook Islands (The)", "NZD"),
    ("Costa Rica", "CRC"),
    ("Croatia", "HRK"),
    ("Cuba (Peso Convertible)", "CUC"),
    ("Cuba", "CUP"),
    ("Curaçao", "ANG"),
    ("Cyprus", "EUR"),
    ("Czech Republic (The)", "CZK")
],
"D": [
    ("Côte d'Ivoire", "XOF"),
    ("Denmark", "DKK"),
    ("Djibouti", "DJF"),
    ("Dominica", "XCD"),
    ("Dominican Republic (The)", "DOP")
],
"E": [
    ("Ecuador", "USD"),
    ("Egypt", "EGP"),
    ("El Salvador", "SVC"),
    ("El Salvador (USD)", "USD"),
    ("Equatorial Guinea", "XAF"),
    ("Eritrea", "ERN"),
    ("Estonia", "EUR"),
    ("Ethiopia", "ETB"),
    ("European Union", "EUR"),
],
"F": [
    ("Falkland Islands (The)", "FKP"),
    ("Faroe Islands (The)", "DKK"),
    ("Fiji", "FJD"),
    ("Finland", "EUR"),
    ("France", "EUR"),
    ("French Guiana", "EUR"),
    ("French Polynesia", "XPF"),
    ("French Southern Territories (The)", "EUR")
],
"G": [
    ("Gabon", "XAF"),
    ("Gambia (The)", "GMD"),
    ("Georgia", "GEL"),
    ("Germany", "EUR"),
    ("Ghana", "GHS"),
    ("Gibraltar", "GIP"),
    ("Greece", "EUR"),
    ("Greenland", "DKK"),
    ("Grenada", "XCD"),
    ("Guadeloupe", "EUR"),
    ("Guam", "USD"),
    ("Guatemala", "GTQ"),
    ("Guernsey", "GBP"),
    ("Guinea", "GNF"),
    ("Guinea-Bissau", "XOF"),
    ("Guyana", "GYD")
],
"H": [
    ("Haiti", "HTG"),
    ("Haiti (USD)", "USD"),
    ("Heard Island and McDonald Islands", "AUD"),
    ("Holy See (The)", "EUR"),
    ("Honduras", "HNL"),
    ("Hong Kong", "HKD"),
    ("Hungary", "HUF")
],
"I": [
    ("Iceland", "ISK"),
    ("India", "INR"),
    ("Indonesia", "IDR"),
    ("International Monetary Fund (IMF)", "XDR"),
    ("Iran (Islamic Republic of)", "IRR"),
    ("Iraq", "IQD"),
    ("Ireland", "EUR"),
    ("Isle of Man", "GBP"),
    ("Israel", "ILS"),
    ("Italy", "EUR")
],
"J": [
    ("Jamaica", "JMD"),
    ("Japan", "JPY"),
    ("Jersey", "GBP"),
    ("Jordan", "JOD")
],
"K": [
    ("Kazakhstan", "KZT"),
    ("Kenya", "KES"),
    ("Kiribati", "AUD"),
    ("Korea (The Democratic People's Republic of)", "KPW"),
    ("Korea (The Republic of)", "KRW"),
    ("Kuwait", "KWD"),
    ("Kyrgyzstan", "KGS")
],
"L": [
    ("Lao People's Democratic Republic (The)", "LAK"),
    ("Latvia", "EUR"),
    ("Lebanon", "LBP"),
    ("Lesotho", "LSL"),
    ("Lesotho (Rand)", "ZAR"),
    ("Liberia", "LRD"),
    ("Libya", "LYD"),
    ("Liechtenstein", "CHF"),
    ("Lithuania", "EUR"),
    ("Luxembourg", "EUR")
],
"M": [
    ("Macao", "MOP"),
    ("Madagascar", "MGA"),
    ("Malawi", "MWK"),
    ("Malaysia", "MYR"),
    ("Maldives", "MVR"),
    ("Mali", "XOF"),
    ("Malta", "EUR"),
    ("Marshall Islands (The)", "USD"),
    ("Martinique", "EUR"),
    ("Mauritania", "MRU"),
    ("Mauritius", "MUR"),
    ("Mayotte", "EUR"),
    ("Mexico", "MXN"),
    ("Mexico (Mexican Unidad de Inversion)", "MXV"),
    ("Micronesia (Federated States of)", "USD"),
    ("Moldova (The Republic of)", "MDL"),
    ("Monaco", "EUR"),
    ("Mongolia", "MNT"),
    ("Montenegro", "EUR"),
    ("Montserrat", "XCD"),
    ("Morocco", "MAD"),
    ("Mozambique", "MZN"),
    ("Myanmar", "MMK"),
],
"N": [
    ("Namibia", "NAD"),
    ("Namibia (Rand)", "ZAR"),
    ("Nauru", "AUD"),
    ("Nepal", "NPR"),
    ("Netherlands (The)", "EUR"),
    ("New Caledonia", "XPF"),
    ("New Zealand", "NZD"),
    ("Nicaragua", "NIO"),
    ("Niger (The)", "XOF"),
    ("Nigeria", "NGN"),
    ("Niue", "NZD")
],
"O": [
    ("Oman", "OMR")
],
"P": [
    ("Pakistan", "PKR"),
    ("Palau", "USD"),
    ("Panama", "PAB"),
    ("Papua New Guinea", "PGK"),
    ("Paraguay", "PYG"),
    ("Peru", "PEN"),
    ("Philippines (The)", "PHP"),
    ("Pitcairn", "NZD"),
    ("Poland", "PLN"),
    ("Portugal", "EUR"),
    ("Puerto Rico", "USD"),
    ("Qatar", "QAR")
],
"Q": [
    ("Qatar", "QAR")
],
"R": [
    ("Romania", "RON"),
    ("Russian Federation (The)", "RUB"),
    ("Rwanda", "RWF")
],
"S": [
    ("Saint Barthélemy", "EUR"),
    ("Saint Helena, Ascension and Tristan da Cunha", "SHP"),
    ("Saint Kitts and Nevis", "XCD"),
    ("Saint Lucia", "XCD"),
    ("Saint Martin (French part)", "EUR"),
    ("Saint Pierre and Miquelon", "EUR"),
    ("Saint Vincent and the Grenadines", "VCT"),
    ("Samoa", "WST"),
    ("San Marino", "EUR"),
    ("Sao Tome and Principe", "STN"),
    ("Saudi Arabia", "SAR"),
    ("Senegal", "CFA"),
    ("Serbia", "RSD"),
    ("Seychelles", "SCR"),
    ("Sierra Leone", "SLL"),
    ("Singapore", "SGD"),
    ("Sint Maarten (Dutch part)", "ANG"),
    ("Slovakia", "EUR"),
    ("Slovenia", "EUR"),
    ("Solomon Islands", "SBD"),
    ("Somalia", "SOS"),
    ("South Africa", "ZAR"),
    ("South Georgia and the South Sandwich Islands", "GBP"),
    ("South Sudan", "SSP"),
    ("Spain", "EUR"),
    ("Sri Lanka", "LKR"),
    ("Sudan (The)", "SDG"),
    ("Suriname", "SRD"),
    ("Svalbard and Jan Mayen", "NOK"),
    ("Sweden", "SEK"),
    ("Switzerland", "CHF")
],
"T": [
    ("Taiwan", "TWD"),
    ("Tajikistan", "TJS"),
    ("Tanzania (United Republic of)", "TZS"),
    ("Thailand", "THB"),
    ("Timor-Leste", "USD"),
    ("Togo", "TGO"),
    ("Tokelau", "NZD"),
    ("Tonga", "TOP"),
    ("Trinidad and Tobago", "TTD"),
    ("Tunisia", "TND"),
    ("Turkey", "TRY"),
    ("Turkmenistan", "TMT"),
    ("Tuvalu", "AUD")
],
"U": [
    ("Uganda", "UGX"),
    ("Ukraine", "UAH"),
    ("United Arab Emirates (The)", "AED"),
    ("United Kingdom of Great Britain and Northern Ireland (The)", "GBP"),
    ("United States of America (The)", "USD"),
    ("Uruguay", "UYU"),
    ("Uzbekistan", "UZS")
],
"V": [
    ("Vanuatu", "VUV"),
    ("Venezuela (Bolivarian Republic of)", "VES"),
    ("Viet Nam", "VND"),
    ("Western Sahara", "MAD")
],
"W": [
    ("Wallis and Futuna", "CFP")
],
"Y": [
    ("Yemen", "YER")
],
"Z": [
    ("Zambia", "ZMW"),
    ("Zimbabwe", "ZWL")
]
}

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")  # This will read from environment variable
if BOT_TOKEN is None:
    raise ValueError("Bot token not found in environment variables. Please check your .env file.")

"""
BOT_TOKEN = 'your token' #replace lines 10 to 12 with this if you don't want to set environment variables.
"""
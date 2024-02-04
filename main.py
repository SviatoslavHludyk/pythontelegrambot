import datetime
import requests
import geocoder
from typing import Final
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# Define constants
token: Final = "6846468287:AAEx4N19Ox1_RhhoD-gBzunZR2pShCX01pM"
bot_username: Final = "https://t.me/sv1testpy_bot"
exchange_rate_api_key: Final = 'YOUR_API_KEY'

# Open-Meteo API
base_meteo_url: Final = "https://api.open-meteo.com/v1/forecast"

# DataMuse API
datamuse_base_url: Final = 'https://api.datamuse.com/words'

# Construct exchange rate API URL
base_currency = 'EUR'
target_currency = 'UAH'
exchange_rate_api_url = f"https://open.er-api.com/v6/latest/{base_currency}?apikey={exchange_rate_api_key}"

# Command to start the bot
async def start_func(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Create inline keyboard with options
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Time", callback_data='time'),
         InlineKeyboardButton("Exchange rate", callback_data='exchange rate')],
        [InlineKeyboardButton("Weather", callback_data='weather'),
         InlineKeyboardButton("Dictionary", callback_data='dictionary')]
    ])
    await update.message.reply_text("Click an option:", reply_markup=keyboard)


# Handler for the 'time' option
async def handle_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Send the current time to the chat
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text=str(f'Actual time (UTC+3): {datetime.datetime.now()}'))


# Handler for the 'exchange rate' option
async def handle_exchange_rate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Retrieve and send the exchange rate for a specified currency pair
        response = requests.get(exchange_rate_api_url)
        response.raise_for_status()
        exchange_rate_data = response.json()

        if 'rates' in exchange_rate_data:
            rate = exchange_rate_data['rates'].get(target_currency)
            if rate is not None:
                await context.bot.send_message(chat_id=update.effective_chat.id,
                                               text=f"Exchange rate: 1 {base_currency} = {rate:.2f} {target_currency}")
            else:
                await context.bot.send_message(chat_id=update.effective_chat.id,
                                               text=f"Exchange rate data for {target_currency} not available.")
        else:
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text="Unable to retrieve exchange rate data.")

    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="Error fetching exchange rate. Please try again later.")

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="An unexpected error occurred. Please try again later.")



# Handler for the 'weather' option
async def handle_weather(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Function to get the current location
    def get_location():
        try:
            location = geocoder.ip('me')
            latitude, longitude = location.latlng
            city = location.city
            return latitude, longitude, city

        except Exception as e:
            print(f"Error getting location: {e}")
            return None, None, None


    # Function to get the current weather based on location
    def get_weather(latitude, longitude, city):
        params = {
            "forecast": "now",
            "daily": "temperature_2m_max",
            "timezone": "Europe/London",
            "current_weather": True,
            "latitude": latitude,
            "longitude": longitude,
        }

        # Weather code mapping for descriptions
        weather_dictionary = {
                0: "Clear sky",
                1: "Mainly clear",
                2: "Partly cloudy",
                3: "Overcast",
                45: "Fog",
                48: "Depositing rime fog",
                51: "Light drizzle",
                52: "Moderate drizzle",
                53: "Intensive drizzle",
                56: "Light freezing drizzle",
                57: "Intensive freezing drizzle",
                61: "Slight rain",
                63: "Moderate rain",
                65: "Heavy rain",
                66: "Light freezing rain",
                67: "Heavy freezing rain",
                71: "Slight snow",
                73: "Moderate snow",
                75: "Heavy snow",
                77: "Snow grains",
                80: "Slight rain showers",
                81: "Moderate rain showers",
                82: "Violent rain showers",
                85: "Slight snow showers",
                86: "Heavy snow showers",
                95: "Thunderstorm",
                96: "Thunderstorm with slight hail",
                99: "Thunderstorm with heavy hail",
            }

        # Retrieve weather data and parse information
        response = requests.get(base_meteo_url, params=params)
        response.raise_for_status()
        weather_data = response.json()

        temperature = weather_data["current_weather"]["temperature"]
        description = float(weather_data["current_weather"]["weathercode"])

        weather = weather_dictionary.get(description, "Unknown")
        return temperature, weather

    # Get location, weather, and send the information to the chat
    latitude, longitude, city = get_location()
    temperature, weather = get_weather(latitude, longitude, city)
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text=f"Current weather in {city}:\n"
                                        f"Temperature: {temperature} degrees\n"
                                        f"Weather: {weather}")


# Handler for the 'dictionary' option
async def handle_dictionary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Send a prompt to enter an English word
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text="Enter an English word: ")


# Handler to get synonyms for a word
async def get_synonyms(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Retrieve word from the user's message
        word = update.message.text.lower()
        params = {'rel_syn': word}
        response = requests.get(datamuse_base_url, params=params)
        response.raise_for_status()
        data = response.json()

        # Process and send synonyms or a message if none found
        if data:
            synonyms = [result['word'] for result in data]
            if synonyms:
                reply_message = f"Synonyms to word {word}: {', '.join(synonyms)}"
                await update.message.reply_text(reply_message)
            else:
                await update.message.reply_text(f"No synonyms found for '{word}'")
        else:
            await update.message.reply_text(f"No synonyms found for '{word}'")

    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        await update.message.reply_text("Error fetching synonyms. Please try again later.")

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        await update.message.reply_text("An unexpected error occurred. Please try again later.")


async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Error handler
    print(f'Update {update} caused error {context.error}')


# Main entry point for the bot
if __name__ == "__main__":
    print("Starting bot")
    # Create and configure the bot application
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start_func))
    app.add_handler(MessageHandler(filters.TEXT, get_synonyms))
    app.add_handler(CallbackQueryHandler(handle_time, pattern='^time$'))
    app.add_handler(CallbackQueryHandler(handle_exchange_rate, pattern='^exchange rate$'))
    app.add_handler(CallbackQueryHandler(handle_weather, pattern='^weather$'))
    app.add_handler(CallbackQueryHandler(handle_dictionary, pattern='^dictionary$'))
    app.add_error_handler(error)

    # Run the bot with polling
    print("Running...")
    app.run_polling(poll_interval=3)




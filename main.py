import requests
import asyncio
import json
import logging
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- Configuration for Cloud Deployment ---
# The bot token and Ollama host are now read from environment variables.
# This is a best practice for security and flexibility in cloud environments like Render.com.
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN")
OLLAMA_HOST = os.environ.get("OLLAMA_HOST")
OLLAMA_GENERATE_ENDPOINT = f"{OLLAMA_HOST}/api/generate"

# Choose a model that you have pulled on your remote Ollama server.
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3")

# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)

# --- Instructions for Render.com Deployment ---
#
# Before running this script on Render, you must:
# 1.  Upload this code to a GitHub repository.
#
# 2.  Go to the Render Dashboard and create a new Web Service.
#
# 3.  Connect your GitHub repository to Render.
#
# 4.  In the service configuration, set the following environment variables:
#     - TELEGRAM_BOT_TOKEN: Your bot token from BotFather.
#     - OLLAMA_HOST: The URL of your remote Ollama server.
#     - OLLAMA_MODEL (optional): The name of the model you want to use.
#
# 5.  Configure the build and start commands for your Python bot.
#
# 6.  Ensure your remote Ollama server is running and publicly accessible.
#


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        f"Hi {user.mention_html()}! I'm a bot powered by a local Ollama model. "
        "Just send me a message and I'll respond.",
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends the user's message to Ollama and replies with the response."""
    user_message = update.message.text
    chat_id = update.effective_chat.id

    if not OLLAMA_HOST:
        await update.message.reply_text(
            "Ollama host is not configured. Please set the OLLAMA_HOST environment variable."
        )
        return

    await context.bot.send_chat_action(
        chat_id=chat_id, action="typing"
    )

    try:
        # Create the payload for the Ollama API
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": user_message,
            "stream": False,
        }
        
        # Send a POST request to the Ollama API
        response = requests.post(OLLAMA_GENERATE_ENDPOINT, json=payload)
        response.raise_for_status()  # Raise an exception for bad status codes

        # The response is a single JSON object (because stream=False)
        data = response.json()
        ollama_response = data.get("response", "No response from model.")

        await update.message.reply_text(ollama_response)

    except requests.exceptions.ConnectionError:
        error_message = (
            f"Could not connect to the Ollama server at {OLLAMA_HOST}. "
            "Please make sure it is running and accessible."
        )
        logging.error(error_message)
        await update.message.reply_text(error_message)

    except requests.exceptions.HTTPError as e:
        error_message = f"HTTP error from Ollama server: {e}"
        logging.error(error_message)
        await update.message.reply_text(error_message)

    except Exception as e:
        error_message = f"An unexpected error occurred: {e}"
        logging.error(error_message)
        await update.message.reply_text(error_message)


def main() -> None:
    """Start the bot."""
    # Build the Application and add handlers
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Register command and message handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

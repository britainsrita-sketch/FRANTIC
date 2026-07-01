import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import pyshorteners

# Enable logging to easily monitor your background worker in Render dashboard
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- CONFIGURATION ---
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# --- TELEGRAM BOT HANDLERS ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a welcoming message."""
    await update.message.reply_text(
        "👋 Welcome to the Background Link Shortener Bot!\n\n"
        "Send me any long URL (starting with http:// or https://), "
        "and I will instantly generate a shortened link for you using free APIs."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processes incoming text and shortens URLs using free providers."""
    user_text = update.message.text.strip()

    # Basic link validation
    if not (user_text.startswith("http://") or user_text.startswith("https://")):
        await update.message.reply_text("❌ Please send a valid link starting with http:// or https://")
        return

    # Send a placeholder message while processing
    status_message = await update.message.reply_text("⚡ Shortening your link...")

    try:
        # Initialize the free shortener engine
        s = pyshorteners.Shortener()
        
        # We use TinyURL API here because it is free, unlimited, and requires no API keys/software setup
        short_url = s.tinyurl.short(user_text)

        # Update the status message with the shortened URL
        await status_message.edit_text(
            f"🔗 **Your Shortened Link:**\n{short_url}"
        )
        logger.info(f"Successfully shortened link for user.")

    except Exception as e:
        logger.error(f"Error while shortening URL: {e}")
        await status_message.edit_text("❌ Failed to shorten the link. Please try again later.")

# --- MAIN EXECUTION ---
def main():
    print("🤖 Starting Background Worker Telegram Bot...")
    
    # Initialize the polling app (Perfect for Background Workers)
    application = Application.builder().token(BOT_TOKEN).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Run the bot permanently using polling (No ports needed, will never time out)
    application.run_polling()

if __name__ == "__main__":
    main()

import os
import random
import string
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- CONFIGURATION ---
# Replace with your actual bot token or set it as an environment variable
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
# Render provides a PORT environment variable automatically. Default to 8080 locally.
PORT = int(os.getenv("PORT", 8080))
# Your deployed app's base URL (e.g., "https://your-app-name.onrender.com")
BASE_URL = os.getenv("BASE_URL", f"http://localhost:{PORT}")

# Global in-memory database to store urls: { short_token: long_url }
url_database = {}

# --- LINK SHORTENING LOGIC ---
def generate_short_token(length=6):
    """Generates a random alphanumeric string."""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

# --- TELEGRAM BOT HANDLERS ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a welcoming message."""
    await update.message.reply_text(
        "👋 Welcome to the Link Shortener Bot!\n\n"
        "Simply send me any long URL (starting with http:// or https://), "
        "and I will create a short redirect link for you instantly."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processes incoming text and shortens URLs."""
    user_text = update.message.text.strip()

    # Basic validation for URL
    if not (user_text.startswith("http://") or user_text.startswith("https://")):
        await update.message.reply_text("❌ Please send a valid link starting with http:// or https://")
        return

    # Generate a unique token
    token = generate_short_token()
    while token in url_database:
        token = generate_short_token()

    # Save to local in-memory DB
    url_database[token] = user_text

    # Construct the final shortened link
    short_link = f"{BASE_URL.rstrip('/')}/{token}"

    await update.message.reply_text(
        f"🔗 **Your Shortened Link:**\n{short_link}"
    )

# --- REDIRECT WEB SERVER ---
class RedirectHandler(BaseHTTPRequestHandler):
    """Handles incoming HTTP requests and redirects short tokens to the long URL."""
    def do_GET(self):
        # Extract token from path (e.g., "/abc123" -> "abc123")
        token = self.path.lstrip("/")

        if token in url_database:
            long_url = url_database[token]
            # Send 302 Found redirect status code
            self.send_response(302)
            self.send_header("Location", long_url)
            self.end_headers()
        else:
            # Token not found
            self.send_response(404)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"<h1>404 Link Not Found</h1><p>The shortened link is invalid or has expired.</p>")

    def log_message(self, format, *args):
        # Override to suppress flood of HTTP server logs in your console
        return

def run_web_server():
    """Starts the native HTTP redirect server."""
    server = HTTPServer(("0.0.0.0", PORT), RedirectHandler)
    print(f"🌍 Redirect server running on port {PORT}...")
    server.serve_forever()

# --- MAIN EXECUTION ---
def main():
    # 1. Start the HTTP Redirect Server in a background thread
    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()

    # 2. Initialize and start the Telegram Bot Application
    print("🤖 Starting Telegram Bot...")
    application = Application.builder().token(BOT_TOKEN).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Run the bot polling
    application.run_polling()

if __name__ == "__main__":
    main()

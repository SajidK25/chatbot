import asyncio
import logging
import os
import time
from collections import defaultdict
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from starlette.requests import Request
from starlette.responses import Response

from src.config import settings
from src.services.chat_handler import chat_handler

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class RateLimiter:
    """In-memory rate limiter: 10 searches per minute per user"""

    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, user_id: str) -> bool:
        now = time.time()
        self._cleanup(user_id, now)
        return len(self._requests[user_id]) < self.max_requests

    def record_search(self, user_id: str) -> bool:
        now = time.time()
        self._cleanup(user_id, now)
        if len(self._requests[user_id]) >= self.max_requests:
            return False
        self._requests[user_id].append(now)
        return True

    def _cleanup(self, user_id: str, now: float):
        cutoff = now - self.window_seconds
        self._requests[user_id] = [t for t in self._requests[user_id] if t > cutoff]


rate_limiter = RateLimiter()


async def with_retry(
    func, *args, max_attempts: int = 3, base_delay: float = 0.5, **kwargs
):
    """Execute function with exponential backoff retry"""
    last_exception = None
    for attempt in range(max_attempts):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            if attempt < max_attempts - 1:
                delay = base_delay * (2**attempt)
                logger.warning(
                    f"Attempt {attempt + 1} failed: {e}. Retrying in {delay:.2f}s..."
                )
                await asyncio.sleep(delay)
    raise last_exception


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hi! I'm *OpenClaw*, your personal shopping assistant!\n\n"
        "I can help you find amazing products just by describing what you're looking for.\n\n"
        "Try saying things like:\n"
        '• "men\'s shoes under $100"\n'
        '• "red wireless headphones"\n'
        '• "best moisturizer for dry skin"\n\n'
        "What are you looking for today?",
        parse_mode="Markdown",
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🛍️ *OpenClaw Shopping Assistant*\n\n"
        "I help you find products using natural language!\n\n"
        "*Examples:*\n"
        '• "women\'s running shoes"\n'
        '• "headphones under $50"\n'
        '• "best face moisturizer"\n\n'
        "Just tell me what you're looking for!",
        parse_mode="Markdown",
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    user_id = str(update.effective_user.id)

    start_time = time.time()
    logger.info(f"User {user_id} sent: {user_message}")

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, action="typing"
    )

    if not rate_limiter.is_allowed(user_id):
        logger.warning(f"Rate limit exceeded for user {user_id}")
        await update.message.reply_text(
            "⚠️ Too many requests. Please try again in a minute.", parse_mode="Markdown"
        )
        return

    try:
        response = await with_retry(
            chat_handler.handle_message,
            user_message,
            platform="telegram",
            max_attempts=3,
            base_delay=0.5,
        )
    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
        response = "😕 Something went wrong. Please try again later."

    elapsed = time.time() - start_time
    logger.info(f"Response completed in {elapsed:.2f}s")

    await update.message.reply_text(
        response, parse_mode="Markdown", disable_web_page_preview=False
    )


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} caused error {context.error}", exc_info=True)


async def scrape_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /scrape command - extract URL and trigger scraping"""
    message = update.message or update.edited_message
    if not message:
        return
    logger.info(f"Received /scrape command with args: {context.args}")

    args = context.args
    if not args:
        await message.reply_text(
            "Usage: /scrape <URL>\nExample: /scrape https://outopia.com/collections/men"
        )
        return

    url = " ".join(args)

    if not url.startswith(("http://", "https://")):
        await message.reply_text(
            "Invalid URL format. Use: https://outopia.com/collections/..."
        )
        return

    await message.reply_text(f"Scraping {url}...")

    try:
        import requests

        api_url = os.environ.get("SCRAPE_API_URL", "https://chatbot-bny4.onrender.com")
        logger.info(f"Calling API: {api_url}/api/scrape with URL: {url}")
        response = requests.post(
            f"{api_url}/api/scrape", json={"url": url}, timeout=300
        )
        logger.info(f"API response status: {response.status_code}")
        response.raise_for_status()
        data = response.json()
        logger.info(f"API response data: {data}")
        await message.reply_text(
            f"Scraped {data['total']} products. {data['inserted']} new, {data['updated']} updated."
        )
    except Exception as e:
        logger.error(f"Scrape error: {e}", exc_info=True)
        await message.reply_text(f"Error: {str(e)}")


async def webhook_handler(request: Request):
    """Handle incoming Telegram updates via webhook"""
    logger.info(f"Webhook called! Method: {request.method}, Path: {request.url.path}")
    try:
        body = await request.json()
        logger.info(f"Request body: {body}")
        update = Update.de_json(body, application.bot)
        logger.info(f"Parsed update: {update}")
        await application.process_update(update)
        logger.info(f"Processed update successfully")
    except Exception as e:
        logger.error(f"Error processing update: {e}", exc_info=True)
    return Response(content="OK", status_code=200)


async def health_handler(request: Request):
    """Health check endpoint"""
    return Response(content="OK")


def run_telegram_bot():
    application = Application.builder().token(settings.telegram_bot_token).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("scrape", scrape_command))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )
    application.add_error_handler(error_handler)

    return application


def run_polling():
    """Run bot with polling (for local/worker)"""
    application = run_telegram_bot()
    logger.info("Starting Telegram bot (polling mode)...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


def run_webhook():
    """Run bot with webhook (for web service)"""
    from fastapi import FastAPI

    global application
    application = run_telegram_bot()

    app = FastAPI()
    app.add_route("/health", health_handler)
    app.add_route("/webhook", webhook_handler)

    return app


if __name__ == "__main__":
    mode = os.environ.get("BOT_MODE", "polling")
    if mode == "webhook":
        import uvicorn

        port = int(os.environ.get("PORT", "8000"))
        app = run_webhook()
        uvicorn.run(app, host="0.0.0.0", port=port)
    else:
        run_polling()

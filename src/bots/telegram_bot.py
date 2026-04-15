import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

from src.config import settings
from src.services.chat_handler import chat_handler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
    user_id = update.effective_user.id
    logger.info(f"User {user_id} sent: {user_message}")

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, action="typing"
    )

    response = await chat_handler.handle_message(user_message, platform="telegram")

    await update.message.reply_text(
        response, parse_mode="Markdown", disable_web_page_preview=False
    )


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} caused error {context.error}")


def run_telegram_bot():
    application = Application.builder().token(settings.telegram_bot_token).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )
    application.add_error_handler(error_handler)

    logger.info("Starting Telegram bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    run_telegram_bot()

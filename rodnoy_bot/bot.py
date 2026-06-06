from __future__ import annotations

import logging

from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, MessageHandler, filters

from rodnoy_bot.config import Config
from rodnoy_bot.database import Database
from rodnoy_bot.handlers.photo import handle_photo, handle_photo_callback
from rodnoy_bot.handlers.reminders import add_reminder, handle_reminder_callback, my_reminders
from rodnoy_bot.handlers.start import cancel, help_command, menu, start
from rodnoy_bot.handlers.text import handle_text
from rodnoy_bot.handlers.voice import handle_voice
from rodnoy_bot.services.notification_service import NotificationService
from rodnoy_bot.services.openai_service import OpenAIService
from rodnoy_bot.services.reminder_service import ReminderService
from rodnoy_bot.services.speech_service import SpeechService
from rodnoy_bot.services.vision_service import VisionService

logging.basicConfig(format="%(asctime)s %(levelname)s %(name)s: %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


def build_application():
    config = Config.from_env()
    db = Database(config.sqlite_path)
    db.init()

    application = ApplicationBuilder().token(config.telegram_bot_token).build()
    application.bot_data["config"] = config
    application.bot_data["db"] = db
    application.bot_data["openai"] = OpenAIService(config.openai_api_key, config.openai_text_model)
    application.bot_data["vision"] = VisionService(config.openai_api_key, config.openai_vision_model)
    application.bot_data["speech"] = SpeechService(config.openai_api_key, config.openai_transcribe_model)
    application.bot_data["notifier"] = NotificationService(config.child_telegram_id, config.admin_telegram_id)
    reminder_service = ReminderService(db)
    application.bot_data["reminder_service"] = reminder_service
    reminder_service.schedule_existing(application)

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("menu", menu))
    application.add_handler(CommandHandler("cancel", cancel))
    application.add_handler(CommandHandler("add_reminder", add_reminder))
    application.add_handler(CommandHandler("my_reminders", my_reminders))
    application.add_handler(CallbackQueryHandler(handle_photo_callback, pattern=r"^photo:"))
    application.add_handler(CallbackQueryHandler(handle_reminder_callback, pattern=r"^reminder:"))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    return application


def main() -> None:
    application = build_application()
    logger.info("РОДНОЙ started")
    application.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    main()

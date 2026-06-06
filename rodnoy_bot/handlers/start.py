from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from rodnoy_bot.keyboards import main_menu_keyboard

WELCOME = (
    "Здравствуйте. Я РОДНОЙ — помощник, который рядом.\n\n"
    "Могу помочь поговорить, разобраться с техникой, садом, документами, продуктами, фото и подозрительными сообщениями.\n"
    "Выберите кнопку ниже или просто напишите мне."
)

HELP = (
    "Команды:\n"
    "/start — начать\n"
    "/menu — показать меню\n"
    "/help — помощь\n"
    "/add_reminder — добавить напоминание\n"
    "/my_reminders — мои напоминания\n"
    "/voice — включить или выключить голосовые ответы\n"
    "/cancel — отменить текущее действие"
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if user:
        db = context.application.bot_data["db"]
        db.upsert_user(user.id, user.full_name)
    await update.effective_message.reply_text(WELCOME, reply_markup=main_menu_keyboard())


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(HELP, reply_markup=main_menu_keyboard())


async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text("Вот меню. Выберите, чем помочь:", reply_markup=main_menu_keyboard())


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data.clear()
    await update.effective_message.reply_text("Хорошо, отменил. Можно выбрать другое действие.", reply_markup=main_menu_keyboard())


async def voice_mode(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user:
        return
    db = context.application.bot_data["db"]
    db.upsert_user(user.id, user.full_name)
    config = context.application.bot_data["config"]
    enabled = db.toggle_voice_reply(user.id)
    if enabled and not config.enable_tts:
        await update.effective_message.reply_text(
            "Голосовой режим включён для вас, но генерация голоса выключена на сервере. "
            "Администратор может включить ENABLE_TTS=true.",
            reply_markup=main_menu_keyboard(),
        )
        return
    status = "включён" if enabled else "выключен"
    await update.effective_message.reply_text(f"Голосовой режим {status}.", reply_markup=main_menu_keyboard())

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

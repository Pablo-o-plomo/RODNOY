from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from rodnoy_bot.keyboards import main_menu_keyboard


async def add_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data["awaiting_reminder"] = True
    await update.effective_message.reply_text(
        "Напишите напоминание простыми словами.\nНапример: Каждый день в 9:00 напомни принять таблетки.",
        reply_markup=main_menu_keyboard(),
    )


async def my_reminders(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    db = context.application.bot_data["db"]
    rows = db.list_reminders(user.id)
    if not rows:
        await update.effective_message.reply_text("Активных напоминаний пока нет.", reply_markup=main_menu_keyboard())
        return
    lines = ["Ваши напоминания:"]
    for row in rows:
        repeat = "каждый день" if row["repeat_rule"] == "daily" else "один раз"
        lines.append(f"• {row['title']} — {row['time']}, {repeat}")
    await update.effective_message.reply_text("\n".join(lines), reply_markup=main_menu_keyboard())


async def handle_reminder_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query or not query.data or not query.data.startswith("reminder:"):
        return
    await query.answer()
    action = query.data.split(":", 1)[1]
    if action == "taken":
        await query.edit_message_text("Хорошо. Отметил. Берегите себя ❤️")
    elif action == "snooze":
        context.job_queue.run_once(send_snoozed_reminder, 15 * 60, data={"chat_id": query.message.chat_id})
        await query.edit_message_text("Хорошо, напомню через 15 минут.")
    elif action == "notify_child":
        notifier = context.application.bot_data["notifier"]
        sent = await notifier.notify_child(context, "Родитель просит помочь с напоминанием.")
        await query.edit_message_text("Сообщил детям." if sent else "Контакт ребёнка пока не настроен.")


async def send_snoozed_reminder(context: ContextTypes.DEFAULT_TYPE) -> None:
    await context.bot.send_message(chat_id=context.job.data["chat_id"], text="Напоминаю ещё раз: пора принять.")

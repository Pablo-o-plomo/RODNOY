from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from rodnoy_bot.handlers.safety import (
    distress_warning,
    has_dangerous_repair_risk,
    has_distress_risk,
    has_scam_risk,
    repair_warning,
    scam_warning,
)
from rodnoy_bot.keyboards import main_menu_keyboard

MENU_PROMPTS = {
    "❤️ Поговорить": "Конечно. Расскажите, как прошёл день?",
    "😊 Мне грустно": "Я рядом. Расскажите, что случилось?",
    "💊 Лекарства": "Напишите название лекарства или пришлите фото упаковки. Я объясню простыми словами, но лечение не назначаю.",
    "🌱 Сад / огород": "Расскажите, что растёт и что случилось. Можно прислать фото листьев или грядки.",
    "🔧 Ремонт / техника": "Опишите поломку: что за техника, модель, что слышно или видно. Если есть электричество — сначала отключите питание.",
    "❄️ Кондиционеры / холодильники": "Напишите модель, симптомы, температуру, есть ли лёд, запускается ли компрессор или наружный блок. Можно прислать фото шильдика.",
    "🍲 Что приготовить": "Напишите, какие продукты есть дома. Я предложу простой рецепт.",
    "📄 Документы / квитанции": "Пришлите фото документа или квитанции. Я помогу прочитать и объяснить простыми словами.",
    "⚠️ Проверить на мошенников": "Перешлите подозрительный текст, фото или голосовое. Коды, пароли и данные карты никому не сообщайте.",
    "📷 Отправить фото": "Пришлите фото. Я сначала спрошу, что вы хотите узнать по нему.",
}


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    user = update.effective_user
    if not message or not user or not message.text:
        return
    await process_text(update, context, message.text.strip())


async def process_text(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> None:
    message = update.effective_message
    user = update.effective_user
    if not message or not user:
        return
    db = context.application.bot_data["db"]
    db.upsert_user(user.id, user.full_name)
    db.add_message(user.id, "in", text)

    if context.user_data.get("awaiting_reminder"):
        await _handle_reminder_text(update, context, text)
        return

    photo_context = db.get_photo_context(user.id)
    if photo_context and photo_context["pending_question"] == "custom":
        vision = context.application.bot_data["vision"]
        await message.chat.send_action("typing")
        answer = await vision.answer_photo_question(photo_context["image_base64"], text, photo_context["detected_type"])
        db.clear_photo_pending_question(user.id)
        db.add_message(user.id, "out", answer)
        await message.reply_text(answer, reply_markup=main_menu_keyboard())
        return

    if text == "📞 Связаться с детьми":
        notifier = context.application.bot_data["notifier"]
        await message.reply_text(notifier.unavailable_message(), reply_markup=main_menu_keyboard())
        return

    if text in MENU_PROMPTS:
        await message.reply_text(MENU_PROMPTS[text], reply_markup=main_menu_keyboard())
        return

    prefix = ""
    if has_scam_risk(text):
        prefix += scam_warning() + "\n\n"
    if has_distress_risk(text):
        prefix += distress_warning() + "\n\n"
    if has_dangerous_repair_risk(text):
        prefix += repair_warning()

    openai_service = context.application.bot_data["openai"]
    await message.chat.send_action("typing")
    answer = await openai_service.answer_text(text)
    answer = prefix + answer
    db.add_message(user.id, "out", answer)
    await message.reply_text(answer, reply_markup=main_menu_keyboard())


async def _handle_reminder_text(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> None:
    message = update.effective_message
    user = update.effective_user
    reminder_service = context.application.bot_data["reminder_service"]
    parsed = reminder_service.parse_reminder(text)
    if not parsed:
        await message.reply_text("Не понял время. Напишите так: Каждый день в 9:00 напомни принять таблетки.")
        return
    title, at_time, repeat_rule = parsed
    db = context.application.bot_data["db"]
    reminder_id = db.add_reminder(user.id, title, at_time, repeat_rule)
    reminder_service.schedule_reminder(context.application, reminder_id, user.id, title, at_time, repeat_rule)
    context.user_data.pop("awaiting_reminder", None)
    repeat = "каждый день" if repeat_rule == "daily" else "один раз"
    await message.reply_text(f"Готово. Напомню: {title} в {at_time}, {repeat}.", reply_markup=main_menu_keyboard())

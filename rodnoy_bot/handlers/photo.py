from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from rodnoy_bot.keyboards import main_menu_keyboard, photo_keyboard
from rodnoy_bot.services.reply_service import reply_text_with_optional_voice, send_optional_voice_reply

CALLBACK_QUESTIONS = {
    "photo:what": "Что это?",
    "photo:explain": "Объяснить простыми словами",
    "photo:danger": "Это опасно?",
    "photo:read_text": "Прочитать текст",
    "photo:food_safe": "Можно ли это есть?",
    "photo:cook": "Что приготовить?",
    "photo:expiry": "Проверить срок годности",
    "photo:ingredients": "Посмотреть состав",
    "photo:medicine_name": "Что это за лекарство?",
    "photo:instruction": "Прочитать инструкцию",
    "photo:medicine_risks": "Есть ли риски?",
    "photo:doctor": "Когда обратиться к врачу?",
    "photo:plant_problem": "Что с растением?",
    "photo:pests": "Есть ли вредители?",
    "photo:watering": "Как поливать?",
    "photo:fertilize": "Чем подкормить?",
    "photo:prune": "Нужно ли обрезать?",
    "photo:part": "Что это за деталь?",
    "photo:check": "Что проверить?",
    "photo:repair_steps": "Как чинить по шагам?",
    "photo:how_to_use": "Как пользоваться?",
    "photo:appliance_danger": "Есть ли опасность?",
    "photo:fridge_reason": "Возможная причина поломки холодильника",
    "photo:ac_reason": "Возможная причина поломки кондиционера",
    "photo:diagnostics": "Диагностика по шагам",
    "photo:multimeter": "Что проверить мультиметром",
    "photo:error_code": "Код ошибки",
    "photo:more_photo": "Нужна ли ещё фотография",
    "photo:read": "Прочитать документ",
    "photo:amount": "Сколько платить?",
    "photo:due_date": "До какого числа?",
    "photo:scam": "Это мошенники?",
    "photo:simple": "Объяснить простыми словами",
}


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    user = update.effective_user
    if not message or not user or not message.photo:
        return
    await message.chat.send_action("typing")
    photo = message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    image_bytes = bytes(await file.download_as_bytearray())
    vision = context.application.bot_data["vision"]
    image_base64 = vision.bytes_to_base64(image_bytes)
    detected_type, label = await vision.detect_photo_type(image_base64)
    db = context.application.bot_data["db"]
    db.upsert_user(user.id, user.full_name)
    db.save_photo_context(user.id, photo.file_id, detected_type, image_base64)
    db.add_message(user.id, "in", f"[photo:{detected_type}]")
    await reply_text_with_optional_voice(
        message,
        context,
        f"Я вижу фото: {label}.\nЧто вы хотите узнать по нему?",
        reply_markup=photo_keyboard(detected_type),
    )


async def handle_photo_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user = update.effective_user
    if not query or not user or not query.data or not query.data.startswith("photo:"):
        return
    await query.answer()
    db = context.application.bot_data["db"]
    photo_context = db.get_photo_context(user.id)
    if not photo_context:
        await query.edit_message_text("Я не нашёл последнее фото. Пожалуйста, пришлите фото ещё раз.")
        return
    if query.data == "photo:custom":
        db.set_photo_pending_question(user.id, "custom")
        await query.edit_message_text("Хорошо. Напишите свой вопрос по этому фото.")
        return
    question = CALLBACK_QUESTIONS.get(query.data, "Объяснить фото")
    await query.edit_message_text("Сейчас посмотрю и отвечу простыми словами...")
    vision = context.application.bot_data["vision"]
    answer = await vision.answer_photo_question(
        photo_context["image_base64"],
        question,
        photo_context["detected_type"],
        conversation_context=_conversation_context(db.list_recent_messages(user.id, limit=30)),
    )
    db.add_message(user.id, "out", answer)
    await query.message.reply_text(answer, reply_markup=main_menu_keyboard())
    await send_optional_voice_reply(query.message.chat_id, user.id, context, answer)


def _conversation_context(history) -> str:
    if not history:
        return "Истории пока мало."
    lines = []
    for item in history:
        speaker = "Пользователь" if item["direction"] == "in" else "РОДНОЙ"
        lines.append(f"{speaker}: {item['text']}")
    return "\n".join(lines[-30:])

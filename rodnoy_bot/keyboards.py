from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup

MAIN_MENU = [
    ["❤️ Поговорить", "😊 Мне грустно"],
    ["💊 Лекарства", "🌱 Сад / огород"],
    ["🔧 Ремонт / техника", "❄️ Кондиционеры / холодильники"],
    ["🍲 Что приготовить", "📄 Документы / квитанции"],
    ["⚠️ Проверить на мошенников", "📞 Связаться с детьми"],
    ["📷 Отправить фото"],
]

PHOTO_UNIVERSAL = [
    ("🔍 Что это?", "photo:what"),
    ("📖 Объяснить простыми словами", "photo:explain"),
    ("⚠️ Это опасно?", "photo:danger"),
    ("📄 Прочитать текст", "photo:read_text"),
    ("✍️ Задать свой вопрос", "photo:custom"),
]

PHOTO_BY_TYPE = {
    "product": [
        ("⏳ Можно ли это есть?", "photo:food_safe"),
        ("🍲 Что приготовить?", "photo:cook"),
        ("📅 Проверить срок годности", "photo:expiry"),
        ("🧂 Посмотреть состав", "photo:ingredients"),
    ],
    "medicine": [
        ("💊 Что это за лекарство?", "photo:medicine_name"),
        ("📄 Прочитать инструкцию", "photo:instruction"),
        ("⚠️ Есть ли риски?", "photo:medicine_risks"),
        ("👨‍⚕️ Когда обратиться к врачу?", "photo:doctor"),
    ],
    "plant": [
        ("🌱 Что с растением?", "photo:plant_problem"),
        ("🐛 Есть ли вредители?", "photo:pests"),
        ("💧 Как поливать?", "photo:watering"),
        ("🧪 Чем подкормить?", "photo:fertilize"),
        ("✂️ Нужно ли обрезать?", "photo:prune"),
    ],
    "appliance": [
        ("🔧 Что это за деталь?", "photo:part"),
        ("⚡ Что проверить?", "photo:check"),
        ("🛠️ Как чинить по шагам?", "photo:repair_steps"),
        ("📖 Как пользоваться?", "photo:how_to_use"),
        ("⚠️ Есть ли опасность?", "photo:appliance_danger"),
    ],
    "fridge": [
        ("❄️ Возможная причина поломки", "photo:fridge_reason"),
        ("🔧 Диагностика по шагам", "photo:diagnostics"),
        ("⚡ Что проверить мультиметром", "photo:multimeter"),
        ("📋 Код ошибки", "photo:error_code"),
        ("📸 Нужна ли ещё фотография", "photo:more_photo"),
    ],
    "air_conditioner": [
        ("❄️ Возможная причина поломки", "photo:ac_reason"),
        ("🔧 Диагностика по шагам", "photo:diagnostics"),
        ("⚡ Что проверить мультиметром", "photo:multimeter"),
        ("📋 Код ошибки", "photo:error_code"),
        ("📸 Нужна ли ещё фотография", "photo:more_photo"),
    ],
    "document": [
        ("📖 Прочитать", "photo:read"),
        ("💰 Сколько платить?", "photo:amount"),
        ("📅 До какого числа?", "photo:due_date"),
        ("⚠️ Это мошенники?", "photo:scam"),
        ("📝 Объяснить простыми словами", "photo:simple"),
    ],
    "receipt": [
        ("📖 Прочитать", "photo:read"),
        ("💰 Сколько платить?", "photo:amount"),
        ("📅 До какого числа?", "photo:due_date"),
        ("⚠️ Это мошенники?", "photo:scam"),
        ("📝 Объяснить простыми словами", "photo:simple"),
    ],
}

REMINDER_KEYBOARD = InlineKeyboardMarkup([
    [InlineKeyboardButton("✅ Принял", callback_data="reminder:taken")],
    [InlineKeyboardButton("⏰ Напомнить через 15 минут", callback_data="reminder:snooze")],
    [InlineKeyboardButton("📞 Сообщить детям", callback_data="reminder:notify_child")],
])


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True, one_time_keyboard=False)


def photo_keyboard(detected_type: str) -> InlineKeyboardMarkup:
    buttons = PHOTO_UNIVERSAL + PHOTO_BY_TYPE.get(detected_type, [])
    rows = [[InlineKeyboardButton(text, callback_data=data)] for text, data in buttons]
    return InlineKeyboardMarkup(rows)

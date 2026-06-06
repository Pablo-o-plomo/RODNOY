from __future__ import annotations

SCAM_MARKERS = [
    "код из смс", "код из sms", "сообщите код", "назовите код", "данные карты", "номер карты",
    "cvc", "cvv", "срочно перевести", "переведите деньги", "блокировка счета", "госуслуг",
    "служба безопасности", "полиция", "центробанк", "подтвердите вход", "пароль", "одноразовый код",
]

DISTRESS_MARKERS = [
    "мне плохо", "умираю", "не хочу жить", "покончить", "суицид", "сильная боль", "задыхаюсь",
    "давит в груди", "инсульт", "потерял сознание", "потеряла сознание",
]

DANGEROUS_REPAIR_MARKERS = [
    "220", "электр", "газ", "хладагент", "фреон", "пайка", "давление", "компрессор", "плата", "мультиметр",
]


def has_scam_risk(text: str) -> bool:
    low = text.lower()
    return any(marker in low for marker in SCAM_MARKERS) or "http://" in low or "https://" in low


def has_distress_risk(text: str) -> bool:
    low = text.lower()
    return any(marker in low for marker in DISTRESS_MARKERS)


def has_dangerous_repair_risk(text: str) -> bool:
    low = text.lower()
    return any(marker in low for marker in DANGEROUS_REPAIR_MARKERS)


def scam_warning() -> str:
    return (
        "Похоже на мошенничество.\n\n"
        "Пожалуйста:\n"
        "1. Не сообщайте коды, пароли и данные карты.\n"
        "2. Не переводите деньги по просьбе из сообщения.\n"
        "3. Позвоните детям или в официальный номер организации."
    )


def distress_warning() -> str:
    return (
        "Я рядом, но я не могу заменить врача или близкого человека.\n\n"
        "Пожалуйста, позвоните родным или в экстренную службу. "
        "Если есть сильная боль, нехватка воздуха или опасность для жизни — звоните 112."
    )


def repair_warning() -> str:
    return (
        "Осторожно. Это может быть опасно. Отключите питание. "
        "Если нет опыта — лучше вызвать специалиста.\n\n"
    )

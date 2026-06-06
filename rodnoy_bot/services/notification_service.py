from __future__ import annotations

from telegram.ext import ContextTypes


NOT_CONFIGURED_MESSAGE = "Пока связь с родственником не настроена."


class NotificationService:
    """Soft notification stub for the first MVP.

    CHILD_TELEGRAM_ID and ADMIN_TELEGRAM_ID are accepted as optional config values,
    but family notifications are deliberately disabled in the simple MVP so the bot
    remains a standalone Telegram assistant.
    """

    def __init__(self, child_telegram_id: int | None = None, admin_telegram_id: int | None = None):
        self.child_telegram_id = child_telegram_id
        self.admin_telegram_id = admin_telegram_id

    async def notify_child(self, context: ContextTypes.DEFAULT_TYPE, message: str) -> bool:
        return False

    async def notify_admin(self, context: ContextTypes.DEFAULT_TYPE, message: str) -> bool:
        return False

    def unavailable_message(self) -> str:
        return NOT_CONFIGURED_MESSAGE

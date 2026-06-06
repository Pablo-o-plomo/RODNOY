from __future__ import annotations

from telegram.ext import ContextTypes


class NotificationService:
    def __init__(self, child_telegram_id: int | None, admin_telegram_id: int | None):
        self.child_telegram_id = child_telegram_id
        self.admin_telegram_id = admin_telegram_id

    async def notify_child(self, context: ContextTypes.DEFAULT_TYPE, message: str) -> bool:
        if not self.child_telegram_id:
            return False
        await context.bot.send_message(chat_id=self.child_telegram_id, text=message)
        return True

    async def notify_admin(self, context: ContextTypes.DEFAULT_TYPE, message: str) -> bool:
        if not self.admin_telegram_id:
            return False
        await context.bot.send_message(chat_id=self.admin_telegram_id, text=message)
        return True

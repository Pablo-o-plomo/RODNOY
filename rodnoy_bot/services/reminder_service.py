from __future__ import annotations

from datetime import datetime, time, timedelta
import re

from telegram.ext import ContextTypes

from rodnoy_bot.database import Database
from rodnoy_bot.keyboards import REMINDER_KEYBOARD

TIME_RE = re.compile(r"\b(\d{1,2})[:.](\d{2})\b")


class ReminderService:
    def __init__(self, db: Database):
        self.db = db

    @staticmethod
    def parse_reminder(text: str) -> tuple[str, str, str] | None:
        match = TIME_RE.search(text)
        if not match:
            return None
        hour = int(match.group(1))
        minute = int(match.group(2))
        if hour > 23 or minute > 59:
            return None
        repeat_rule = "daily" if "каждый день" in text.lower() or "ежеднев" in text.lower() else "once"
        title = text
        for prefix in ["каждый день", "ежедневно", "разово", "напомни", "напомнить"]:
            title = re.sub(prefix, "", title, flags=re.IGNORECASE).strip()
        title = TIME_RE.sub("", title).strip(" .,:—-") or "напоминание"
        return title, f"{hour:02d}:{minute:02d}", repeat_rule

    def schedule_existing(self, application) -> None:
        for row in self.db.list_all_active_reminders():
            self.schedule_reminder(
                application,
                int(row["id"]),
                int(row["telegram_id"]),
                row["title"],
                row["time"],
                row["repeat_rule"],
            )

    def schedule_reminder(self, application, reminder_id: int, telegram_id: int, title: str, at_time: str, repeat_rule: str) -> None:
        hour, minute = [int(part) for part in at_time.split(":")]
        target = time(hour=hour, minute=minute)
        data = {"reminder_id": reminder_id, "telegram_id": telegram_id, "title": title, "repeat_rule": repeat_rule}
        if repeat_rule == "daily":
            application.job_queue.run_daily(send_reminder, target, data=data, name=f"reminder:{reminder_id}")
        else:
            now = datetime.now()
            when = datetime.combine(now.date(), target)
            if when <= now:
                when += timedelta(days=1)
            application.job_queue.run_once(send_reminder, when - now, data=data, name=f"reminder:{reminder_id}")


async def send_reminder(context: ContextTypes.DEFAULT_TYPE) -> None:
    data = context.job.data
    await context.bot.send_message(
        chat_id=data["telegram_id"],
        text=f"Пора принять: {data['title']}",
        reply_markup=REMINDER_KEYBOARD,
    )
    if data.get("repeat_rule") == "once":
        db: Database = context.application.bot_data["db"]
        db.deactivate_reminder(int(data["reminder_id"]))

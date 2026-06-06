from __future__ import annotations

import asyncio
from collections.abc import Sequence
from datetime import datetime, timezone
import sqlite3

from openai import OpenAI

from rodnoy_bot.prompts import SYSTEM_PROMPT


class OpenAIService:
    def __init__(self, api_key: str, text_model: str):
        self.client = OpenAI(api_key=api_key)
        self.text_model = text_model

    async def answer_text(
        self,
        user_text: str,
        context: str | None = None,
        history: Sequence[sqlite3.Row] | None = None,
        user_description: str | None = None,
        last_message_at: datetime | None = None,
    ) -> str:
        return await asyncio.to_thread(
            self._answer_text_sync,
            user_text,
            context,
            list(history or []),
            user_description,
            last_message_at,
        )

    def _answer_text_sync(
        self,
        user_text: str,
        context: str | None,
        history: list[sqlite3.Row],
        user_description: str | None,
        last_message_at: datetime | None,
    ) -> str:
        response = self.client.responses.create(
            model=self.text_model,
            instructions=SYSTEM_PROMPT,
            input=_build_input(user_text, context, history, user_description, last_message_at),
            max_output_tokens=700,
        )
        return (response.output_text or "Простите, я не смог ответить. Попробуйте написать ещё раз.").strip()


def _build_input(
    user_text: str,
    context: str | None,
    history: list[sqlite3.Row],
    user_description: str | None,
    last_message_at: datetime | None,
) -> list[dict[str, str]]:
    continuation_note = _continuation_note(last_message_at)
    setup_parts = [
        user_description or "Пользователь Telegram-бота РОДНОЙ.",
        continuation_note,
        "Используй историю ниже как непрерывный диалог. Не начинай заново, если это продолжение.",
    ]
    if context:
        setup_parts.append(f"Дополнительный контекст: {context}")
    messages: list[dict[str, str]] = [{"role": "user", "content": "\n".join(setup_parts)}]

    for item in history:
        text = (item["text"] or "").strip()
        if not text:
            continue
        role = "assistant" if item["direction"] == "out" else "user"
        messages.append({"role": role, "content": text})

    if not history or (history[-1]["direction"] != "in" or history[-1]["text"] != user_text):
        messages.append({"role": "user", "content": user_text})
    return messages


def _continuation_note(last_message_at: datetime | None) -> str:
    if not last_message_at:
        return "Это первый сохранённый обмен или истории пока мало. Можно начать спокойно, но без лишнего представления."
    now = datetime.now(timezone.utc)
    if last_message_at.tzinfo is None:
        last_message_at = last_message_at.replace(tzinfo=timezone.utc)
    hours = (now - last_message_at).total_seconds() / 3600
    if hours < 12:
        return (
            "С прошлого сообщения прошло меньше 12 часов. Это активный диалог: не здоровайся, "
            "не представляйся, не пиши 'давайте разберёмся', а продолжай с предыдущего шага."
        )
    return "С прошлого сообщения прошло больше 12 часов. Можно коротко сказать: 'Добрый день! Рад снова вас слышать.'"

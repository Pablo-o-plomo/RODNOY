from __future__ import annotations

import asyncio
from openai import OpenAI

from rodnoy_bot.prompts import SYSTEM_PROMPT


class OpenAIService:
    def __init__(self, api_key: str, text_model: str):
        self.client = OpenAI(api_key=api_key)
        self.text_model = text_model

    async def answer_text(self, user_text: str, context: str | None = None) -> str:
        prompt = user_text if not context else f"Контекст: {context}\n\nВопрос пользователя: {user_text}"
        return await asyncio.to_thread(self._answer_text_sync, prompt)

    def _answer_text_sync(self, prompt: str) -> str:
        response = self.client.responses.create(
            model=self.text_model,
            instructions=SYSTEM_PROMPT,
            input=prompt,
            max_output_tokens=700,
        )
        return (response.output_text or "Простите, я не смог ответить. Попробуйте написать ещё раз.").strip()

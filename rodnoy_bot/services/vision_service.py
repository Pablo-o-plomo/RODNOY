from __future__ import annotations

import asyncio
import base64
import json

from openai import OpenAI

from rodnoy_bot.prompts import PHOTO_DETECTION_PROMPT, SYSTEM_PROMPT


class VisionService:
    def __init__(self, api_key: str, vision_model: str):
        self.client = OpenAI(api_key=api_key)
        self.vision_model = vision_model

    @staticmethod
    def bytes_to_base64(image_bytes: bytes) -> str:
        return base64.b64encode(image_bytes).decode("utf-8")

    async def detect_photo_type(self, image_base64: str) -> tuple[str, str]:
        return await asyncio.to_thread(self._detect_photo_type_sync, image_base64)

    def _detect_photo_type_sync(self, image_base64: str) -> tuple[str, str]:
        response = self.client.responses.create(
            model=self.vision_model,
            instructions=PHOTO_DETECTION_PROMPT,
            input=[{
                "role": "user",
                "content": [
                    {"type": "input_text", "text": "Определи тип этого фото."},
                    {"type": "input_image", "image_url": f"data:image/jpeg;base64,{image_base64}"},
                ],
            }],
            max_output_tokens=120,
        )
        text = response.output_text or "{}"
        try:
            data = json.loads(text)
            return data.get("detected_type", "unknown"), data.get("short_label", "фото")
        except json.JSONDecodeError:
            return "unknown", "фото"

    async def answer_photo_question(
        self,
        image_base64: str,
        question: str,
        detected_type: str,
        conversation_context: str | None = None,
    ) -> str:
        return await asyncio.to_thread(
            self._answer_photo_question_sync,
            image_base64,
            question,
            detected_type,
            conversation_context,
        )

    def _answer_photo_question_sync(
        self,
        image_base64: str,
        question: str,
        detected_type: str,
        conversation_context: str | None,
    ) -> str:
        response = self.client.responses.create(
            model=self.vision_model,
            instructions=SYSTEM_PROMPT,
            input=[{
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": (
                            f"Тип фото: {detected_type}. Вопрос: {question}\n"
                            f"Контекст диалога: {conversation_context or 'Истории мало.'}\n"
                            "Ответь коротко, простыми словами, по шагам. Не здоровайся повторно и не начинай разговор заново. Если есть риск для здоровья, денег или безопасности — предупреди."
                        ),
                    },
                    {"type": "input_image", "image_url": f"data:image/jpeg;base64,{image_base64}"},
                ],
            }],
            max_output_tokens=700,
        )
        return (response.output_text or "Не получилось разобрать фото. Попробуйте прислать фото ближе и ярче.").strip()

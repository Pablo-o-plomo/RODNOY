from __future__ import annotations

import asyncio
from pathlib import Path

from openai import OpenAI


class SpeechService:
    def __init__(self, api_key: str, transcribe_model: str):
        self.client = OpenAI(api_key=api_key)
        self.transcribe_model = transcribe_model

    async def transcribe(self, audio_path: Path) -> str:
        return await asyncio.to_thread(self._transcribe_sync, audio_path)

    def _transcribe_sync(self, audio_path: Path) -> str:
        with audio_path.open("rb") as audio_file:
            transcription = self.client.audio.transcriptions.create(
                model=self.transcribe_model,
                file=audio_file,
                language="ru",
                prompt="Пожилой человек говорит по-русски с Telegram-ботом РОДНОЙ.",
            )
        return (getattr(transcription, "text", None) or "").strip()

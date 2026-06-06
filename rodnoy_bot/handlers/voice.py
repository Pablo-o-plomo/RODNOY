from __future__ import annotations

import tempfile
from pathlib import Path

from telegram import Update
from telegram.ext import ContextTypes

from rodnoy_bot.handlers.text import process_text


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    if not message or not message.voice:
        return
    await message.chat.send_action("typing")
    voice_file = await context.bot.get_file(message.voice.file_id)
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "voice.ogg"
        await voice_file.download_to_drive(path)
        speech = context.application.bot_data["speech"]
        text = await speech.transcribe(path)
    if not text:
        await message.reply_text("Не смог разобрать голосовое. Попробуйте сказать чуть громче или написать текстом.")
        return
    await message.reply_text(f"Я услышал: {text}")
    await process_text(update, context, text)

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from telegram import InputFile, Message
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


async def reply_text_with_optional_voice(
    message: Message,
    context: ContextTypes.DEFAULT_TYPE,
    text: str,
    reply_markup=None,
) -> None:
    await message.reply_text(text, reply_markup=reply_markup)
    await send_optional_voice_reply(message.chat_id, message.from_user.id if message.from_user else None, context, text)


async def send_optional_voice_reply(
    chat_id: int,
    telegram_id: int | None,
    context: ContextTypes.DEFAULT_TYPE,
    text: str,
) -> None:
    config = context.application.bot_data["config"]
    if not config.enable_tts or telegram_id is None:
        return
    db = context.application.bot_data["db"]
    if not db.is_voice_reply_enabled(telegram_id):
        return
    tts = context.application.bot_data["tts"]
    voice_path: Path | None = None
    try:
        voice_path = Path(await asyncio.to_thread(tts.generate_voice, text))
        with voice_path.open("rb") as voice_file:
            if voice_path.suffix.lower() == ".ogg":
                await context.bot.send_voice(chat_id=chat_id, voice=InputFile(voice_file, filename=voice_path.name))
            else:
                await context.bot.send_audio(chat_id=chat_id, audio=InputFile(voice_file, filename=voice_path.name))
    except Exception:
        logger.exception("TTS voice reply failed; text response was already sent")
    finally:
        if voice_path:
            _safe_unlink(voice_path)
            if voice_path.suffix.lower() == ".ogg":
                _safe_unlink(voice_path.with_suffix(".mp3"))


def _safe_unlink(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except OSError:
        logger.warning("Could not remove temporary TTS file: %s", path)

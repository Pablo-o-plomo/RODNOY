from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import tempfile
from uuid import uuid4

from openai import OpenAI


class TTSService:
    def __init__(self, api_key: str, model: str, voice: str):
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.voice = voice
        self.output_dir = Path(tempfile.gettempdir()) / "rodnoy_tts"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_voice(self, text: str) -> str:
        text = _shorten_for_tts(text)
        mp3_path = self.output_dir / f"rodnoy-{uuid4().hex}.mp3"
        response = self.client.audio.speech.create(
            model=self.model,
            voice=self.voice,
            input=text,
            response_format="mp3",
        )
        _write_speech_response(response, mp3_path)
        ogg_path = _convert_to_ogg_if_possible(mp3_path)
        return str(ogg_path or mp3_path)


def _shorten_for_tts(text: str, limit: int = 500) -> str:
    clean = " ".join(text.split())
    if len(clean) <= limit:
        return clean
    suffix = "... Полный ответ я написал текстом."
    shortened = clean[: limit - len(suffix)].rsplit(" ", 1)[0].strip()
    return f"{shortened}{suffix}"


def _write_speech_response(response, path: Path) -> None:
    if hasattr(response, "write_to_file"):
        response.write_to_file(str(path))
        return
    if hasattr(response, "stream_to_file"):
        response.stream_to_file(str(path))
        return
    content = getattr(response, "content", None)
    if content is not None:
        path.write_bytes(content)
        return
    path.write_bytes(bytes(response))


def _convert_to_ogg_if_possible(mp3_path: Path) -> Path | None:
    if not shutil.which("ffmpeg"):
        return None
    ogg_path = mp3_path.with_suffix(".ogg")
    try:
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(mp3_path),
                "-c:a",
                "libopus",
                "-b:a",
                "32k",
                str(ogg_path),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return ogg_path if ogg_path.exists() else None

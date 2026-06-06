from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Config:
    telegram_bot_token: str
    openai_api_key: str
    database_url: str
    child_telegram_id: int | None
    admin_telegram_id: int | None
    openai_text_model: str = "gpt-4o-mini"
    openai_vision_model: str = "gpt-4o-mini"
    openai_transcribe_model: str = "gpt-4o-mini-transcribe"

    @classmethod
    def from_env(cls) -> "Config":
        load_dotenv()
        token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        database_url = os.getenv("DATABASE_URL", "sqlite:///rodnoy.sqlite3").strip()
        if not token:
            raise RuntimeError("TELEGRAM_BOT_TOKEN is required")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is required")
        return cls(
            telegram_bot_token=token,
            openai_api_key=api_key,
            database_url=database_url,
            child_telegram_id=_optional_int(os.getenv("CHILD_TELEGRAM_ID")),
            admin_telegram_id=_optional_int(os.getenv("ADMIN_TELEGRAM_ID")),
            openai_text_model=os.getenv("OPENAI_TEXT_MODEL", "gpt-4o-mini"),
            openai_vision_model=os.getenv("OPENAI_VISION_MODEL", "gpt-4o-mini"),
            openai_transcribe_model=os.getenv("OPENAI_TRANSCRIBE_MODEL", "gpt-4o-mini-transcribe"),
        )

    @property
    def sqlite_path(self) -> Path:
        if self.database_url.startswith("sqlite:///"):
            return Path(self.database_url.replace("sqlite:///", "", 1))
        if self.database_url == ":memory:":
            return Path(":memory:")
        raise RuntimeError("MVP supports SQLite DATABASE_URL, for example sqlite:///rodnoy.sqlite3")


def _optional_int(value: str | None) -> int | None:
    """Return a Telegram ID or None for empty, zero, or invalid MVP values."""
    if not value or not value.strip():
        return None
    try:
        parsed = int(value)
    except ValueError:
        return None
    return parsed if parsed > 0 else None

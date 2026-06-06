from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import sqlite3
from pathlib import Path
from typing import Iterator


class Database:
    def __init__(self, sqlite_path: Path):
        self.sqlite_path = sqlite_path
        if str(sqlite_path) != ":memory:":
            sqlite_path.parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.sqlite_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def init(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER NOT NULL UNIQUE,
                    name TEXT,
                    role TEXT NOT NULL DEFAULT 'parent',
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    direction TEXT NOT NULL,
                    text TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                );

                CREATE TABLE IF NOT EXISTS reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    time TEXT NOT NULL,
                    repeat_rule TEXT NOT NULL DEFAULT 'once',
                    active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                );

                CREATE TABLE IF NOT EXISTS photo_context (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    file_id TEXT NOT NULL,
                    detected_type TEXT NOT NULL,
                    pending_question TEXT,
                    image_base64 TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                );
                """
            )

    def upsert_user(self, telegram_id: int, name: str | None, role: str = "parent") -> int:
        now = _now()
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO users (telegram_id, name, role, created_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(telegram_id) DO UPDATE SET name=excluded.name
                """,
                (telegram_id, name, role, now),
            )
            row = conn.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,)).fetchone()
            return int(row["id"])

    def get_user_id(self, telegram_id: int) -> int | None:
        with self.connect() as conn:
            row = conn.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,)).fetchone()
            return int(row["id"]) if row else None

    def add_message(self, telegram_id: int, direction: str, text: str | None) -> None:
        user_id = self.get_user_id(telegram_id) or self.upsert_user(telegram_id, None)
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO messages (user_id, direction, text, created_at) VALUES (?, ?, ?, ?)",
                (user_id, direction, text, _now()),
            )

    def save_photo_context(self, telegram_id: int, file_id: str, detected_type: str, image_base64: str) -> None:
        user_id = self.get_user_id(telegram_id) or self.upsert_user(telegram_id, None)
        with self.connect() as conn:
            conn.execute("DELETE FROM photo_context WHERE user_id = ?", (user_id,))
            conn.execute(
                """
                INSERT INTO photo_context (user_id, file_id, detected_type, pending_question, image_base64, created_at)
                VALUES (?, ?, ?, NULL, ?, ?)
                """,
                (user_id, file_id, detected_type, image_base64, _now()),
            )

    def set_photo_pending_question(self, telegram_id: int, question: str) -> None:
        user_id = self.get_user_id(telegram_id)
        if not user_id:
            return
        with self.connect() as conn:
            conn.execute("UPDATE photo_context SET pending_question = ? WHERE user_id = ?", (question, user_id))

    def get_photo_context(self, telegram_id: int) -> sqlite3.Row | None:
        user_id = self.get_user_id(telegram_id)
        if not user_id:
            return None
        with self.connect() as conn:
            return conn.execute(
                "SELECT * FROM photo_context WHERE user_id = ? ORDER BY created_at DESC LIMIT 1", (user_id,)
            ).fetchone()

    def clear_photo_pending_question(self, telegram_id: int) -> None:
        user_id = self.get_user_id(telegram_id)
        if not user_id:
            return
        with self.connect() as conn:
            conn.execute("UPDATE photo_context SET pending_question = NULL WHERE user_id = ?", (user_id,))

    def add_reminder(self, telegram_id: int, title: str, time: str, repeat_rule: str) -> int:
        user_id = self.get_user_id(telegram_id) or self.upsert_user(telegram_id, None)
        with self.connect() as conn:
            cur = conn.execute(
                "INSERT INTO reminders (user_id, title, time, repeat_rule, active, created_at) VALUES (?, ?, ?, ?, 1, ?)",
                (user_id, title, time, repeat_rule, _now()),
            )
            return int(cur.lastrowid)

    def list_reminders(self, telegram_id: int) -> list[sqlite3.Row]:
        user_id = self.get_user_id(telegram_id)
        if not user_id:
            return []
        with self.connect() as conn:
            return list(conn.execute("SELECT * FROM reminders WHERE user_id = ? AND active = 1 ORDER BY time", (user_id,)))

    def list_all_active_reminders(self) -> list[sqlite3.Row]:
        with self.connect() as conn:
            return list(conn.execute(
                """
                SELECT reminders.*, users.telegram_id
                FROM reminders
                JOIN users ON users.id = reminders.user_id
                WHERE reminders.active = 1
                """
            ))

    def deactivate_reminder(self, reminder_id: int) -> None:
        with self.connect() as conn:
            conn.execute("UPDATE reminders SET active = 0 WHERE id = ?", (reminder_id,))


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

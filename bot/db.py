"""SQLite with numbered migrations.

Add a migration by appending to MIGRATIONS. Never edit one that has shipped:
the database remembers which ones already ran and will not run them again.
"""

from __future__ import annotations

import logging
from pathlib import Path

import aiosqlite

log = logging.getLogger(__name__)

MIGRATIONS: list[str] = [
    # 1: reminders
    """
    CREATE TABLE reminders (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id     INTEGER NOT NULL,
        channel_id  INTEGER,
        guild_id    INTEGER,
        message     TEXT NOT NULL,
        due_at      REAL NOT NULL,
        created_at  REAL NOT NULL
    );
    CREATE INDEX reminders_due ON reminders (due_at);
    CREATE INDEX reminders_user ON reminders (user_id);
    """,
    # 2: per-guild settings as simple key/value pairs
    """
    CREATE TABLE guild_settings (
        guild_id INTEGER NOT NULL,
        key      TEXT NOT NULL,
        value    TEXT NOT NULL,
        PRIMARY KEY (guild_id, key)
    );
    """,
]


class Database:
    def __init__(self, path: Path | str):
        self.path = Path(path) if str(path) != ":memory:" else path
        self._conn: aiosqlite.Connection | None = None

    @property
    def conn(self) -> aiosqlite.Connection:
        if self._conn is None:
            raise RuntimeError("database is not connected")
        return self._conn

    async def connect(self) -> None:
        if isinstance(self.path, Path):
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = await aiosqlite.connect(self.path)
        self._conn.row_factory = aiosqlite.Row
        # WAL lets reads continue while a write is in progress.
        await self._conn.execute("PRAGMA journal_mode=WAL")
        await self._conn.execute("PRAGMA foreign_keys=ON")
        await self.migrate()

    async def close(self) -> None:
        if self._conn is not None:
            await self._conn.close()
            self._conn = None

    async def migrate(self) -> int:
        cur = await self.conn.execute("PRAGMA user_version")
        (current,) = await cur.fetchone()
        for version, sql in enumerate(MIGRATIONS[current:], start=current + 1):
            log.info("applying database migration %d", version)
            await self.conn.executescript(f"BEGIN;\n{sql}\nPRAGMA user_version = {version};\nCOMMIT;")
        return len(MIGRATIONS) - current

    async def get_setting(self, guild_id: int, key: str, default: str | None = None) -> str | None:
        cur = await self.conn.execute(
            "SELECT value FROM guild_settings WHERE guild_id = ? AND key = ?", (guild_id, key)
        )
        row = await cur.fetchone()
        return row["value"] if row else default

    async def set_setting(self, guild_id: int, key: str, value: str) -> None:
        await self.conn.execute(
            "INSERT INTO guild_settings (guild_id, key, value) VALUES (?, ?, ?) "
            "ON CONFLICT (guild_id, key) DO UPDATE SET value = excluded.value",
            (guild_id, key, value),
        )
        await self.conn.commit()

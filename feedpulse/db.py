import aiosqlite
import os
from pathlib import Path

DB_PATH = os.environ.get("FEEDPULSE_DB_PATH", "data/feedpulse.db")


async def get_db() -> aiosqlite.Connection:
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    return db


async def init_db() -> None:
    db = await get_db()
    try:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS feeds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL UNIQUE,
                title TEXT,
                last_checked_at TEXT,
                last_entry_id TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                feed_id INTEGER NOT NULL,
                chat_id INTEGER NOT NULL,
                chat_type TEXT DEFAULT 'private',
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (feed_id) REFERENCES feeds(id) ON DELETE CASCADE,
                UNIQUE(feed_id, chat_id)
            );

            CREATE TABLE IF NOT EXISTS entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                feed_id INTEGER NOT NULL,
                entry_id TEXT NOT NULL,
                title TEXT,
                link TEXT,
                published_at TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (feed_id) REFERENCES feeds(id) ON DELETE CASCADE,
                UNIQUE(feed_id, entry_id)
            );
        """)
        await db.commit()
    finally:
        await db.close()

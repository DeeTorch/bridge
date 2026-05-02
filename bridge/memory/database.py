"""SQLite database – hot cache for messages, summaries, knowledge, and profile."""
import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

import aiosqlite

logger = logging.getLogger(__name__)


class Database:
    """Async SQLite wrapper with WAL mode and schema management."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.conn: Optional[aiosqlite.Connection] = None

    async def initialize(self) -> None:
        """Create DB directory, enable WAL, and run migrations."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = await aiosqlite.connect(self.db_path)
        await self.conn.execute("PRAGMA journal_mode=WAL;")
        await self.conn.execute("PRAGMA synchronous=NORMAL;")
        await self._migrate()
        logger.info(f"Database initialized at {self.db_path}")

    async def _migrate(self) -> None:
        """Create all tables if they don't exist."""
        schema = """
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp DATETIME NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            summary_text TEXT NOT NULL,
            token_count INTEGER NOT NULL,
            created_at DATETIME NOT NULL DEFAULT (datetime('now')),
            UNIQUE(user_id)
        );

        CREATE TABLE IF NOT EXISTS knowledge_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT NOT NULL UNIQUE,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            last_updated DATETIME NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS knowledge_index (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_id INTEGER NOT NULL,
            user_id INTEGER,
            message_id INTEGER,
            FOREIGN KEY(entry_id) REFERENCES knowledge_entries(id)
        );

        CREATE TABLE IF NOT EXISTS user_profile (
            user_id INTEGER PRIMARY KEY,
            profile_text TEXT NOT NULL,
            last_updated DATETIME NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS sync_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_type TEXT NOT NULL,
            entity_id TEXT NOT NULL,
            action TEXT NOT NULL,
            payload TEXT NOT NULL,
            retries INTEGER DEFAULT 0,
            created_at DATETIME NOT NULL DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS idx_messages_user ON messages(user_id);
        CREATE INDEX IF NOT EXISTS idx_sync_queue ON sync_queue(entity_type, entity_id);
        """
        await self.conn.executescript(schema)
        await self.conn.commit()

    async def close(self) -> None:
        if self.conn:
            await self.conn.close()
            self.conn = None

    # Message operations
    async def append_message(self, user_id: int, role: str, content: str) -> int:
        """Insert a message and return its ID."""
        async with self.conn.execute(
            "INSERT INTO messages (user_id, role, content) VALUES (?, ?, ?)",
            (user_id, role, content),
        ) as cursor:
            await self.conn.commit()
            return cursor.lastrowid

    async def get_messages(self, user_id: int, limit: int = 50) -> list[dict]:
        """Retrieve recent messages for context window."""
        cursor = await self.conn.execute(
            """
            SELECT role, content, timestamp
            FROM messages
            WHERE user_id = ?
            ORDER BY timestamp ASC
            LIMIT ?
            """,
            (user_id, limit),
        )
        rows = await cursor.fetchall()
        return [{"role": r[0], "content": r[1], "timestamp": r[2]} for r in rows]

    async def count_messages(self, user_id: int) -> int:
        cursor = await self.conn.execute(
            "SELECT COUNT(*) FROM messages WHERE user_id = ?", (user_id,)
        )
        row = await cursor.fetchone()
        return row[0] if row else 0

    async def clear_messages(self, user_id: int) -> None:
        await self.conn.execute("DELETE FROM messages WHERE user_id = ?", (user_id,))
        await self.conn.commit()

    # Summary operations
    async def get_summary(self, user_id: int) -> Optional[tuple[str, int]]:
        cursor = await self.conn.execute(
            "SELECT summary_text, token_count FROM summaries WHERE user_id = ?",
            (user_id,),
        )
        row = await cursor.fetchone()
        return (row[0], row[1]) if row else None

    async def upsert_summary(self, user_id: int, summary: str, tokens: int) -> None:
        await self.conn.execute(
            """
            INSERT OR REPLACE INTO summaries (user_id, summary_text, token_count, created_at)
            VALUES (?, ?, ?, datetime('now'))
            """,
            (user_id, summary, tokens),
        )
        await self.conn.commit()

    # Knowledge operations
    async def upsert_knowledge(self, slug: str, title: str, content: str) -> int:
        """Insert or update a knowledge entry, return entry ID."""
        await self.conn.execute(
            """
            INSERT INTO knowledge_entries (slug, title, content, last_updated)
            VALUES (?, ?, ?, datetime('now'))
            ON CONFLICT(slug) DO UPDATE SET
                title = excluded.title,
                content = excluded.content,
                last_updated = datetime('now')
            """,
            (slug, title, content),
        )
        await self.conn.commit()
        cursor = await self.conn.execute("SELECT id FROM knowledge_entries WHERE slug = ?", (slug,))
        row = await cursor.fetchone()
        return row[0] if row else -1

    async def get_knowledge(self, slug: str) -> Optional[dict]:
        cursor = await self.conn.execute(
            "SELECT title, content, last_updated FROM knowledge_entries WHERE slug = ?",
            (slug,),
        )
        row = await cursor.fetchone()
        if row:
            return {"title": row[0], "content": row[1], "last_updated": row[2]}
        return None

    async def list_knowledge(self) -> list[dict]:
        cursor = await self.conn.execute(
            "SELECT slug, title, last_updated FROM knowledge_entries ORDER BY last_updated DESC"
        )
        rows = await cursor.fetchall()
        return [{"slug": r[0], "title": r[1], "last_updated": r[2]} for r in rows]

    # Profile operations
    async def get_profile(self, user_id: int) -> Optional[str]:
        cursor = await self.conn.execute(
            "SELECT profile_text FROM user_profile WHERE user_id = ?", (user_id,)
        )
        row = await cursor.fetchone()
        return row[0] if row else None

    async def upsert_profile(self, user_id: int, profile_text: str) -> None:
        await self.conn.execute(
            """
            INSERT INTO user_profile (user_id, profile_text, last_updated)
            VALUES (?, ?, datetime('now'))
            ON CONFLICT(user_id) DO UPDATE SET
                profile_text = excluded.profile_text,
                last_updated = datetime('now')
            """,
            (user_id, profile_text),
        )
        await self.conn.commit()

    # Sync queue operations
    async def enqueue_sync(self, entity_type: str, entity_id: str, action: str, payload: dict) -> None:
        """Add an item to the async sync queue."""
        await self.conn.execute(
            "INSERT INTO sync_queue (entity_type, entity_id, action, payload) VALUES (?, ?, ?, ?)",
            (entity_type, entity_id, action, json.dumps(payload)),
        )
        await self.conn.commit()

    async def dequeue_sync(self, batch_size: int = 10) -> list[dict]:
        """Pop up to batch_size queued sync items."""
        cursor = await self.conn.execute(
            """
            SELECT id, entity_type, entity_id, action, payload
            FROM sync_queue
            ORDER BY created_at ASC
            LIMIT ?
            """,
            (batch_size,),
        )
        rows = await cursor.fetchall()
        items = []
        for row in rows:
            items.append({
                "queue_id": row[0],
                "entity_type": row[1],
                "entity_id": row[2],
                "action": row[3],
                "payload": json.loads(row[4]),
            })
            await self.conn.execute("DELETE FROM sync_queue WHERE id = ?", (row[0],))
        await self.conn.commit()
        return items

    async def mark_sync_failed(self, queue_id: int) -> None:
        await self.conn.execute(
            "UPDATE sync_queue SET retries = retries + 1 WHERE id = ?", (queue_id,)
        )
        await self.conn.commit()

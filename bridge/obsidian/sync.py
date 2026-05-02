"""Async sync engine — orchestrates SQLite → Obsidian writes in background."""
import asyncio
import datetime
import json
import logging
from pathlib import Path
from typing import Optional

from .vault import Vault
from .formatter import ObsidianFormatter
from .rest import ObsidianRestClient

logger = logging.getLogger(__name__)


class SyncEngine:
    """
    Background sync: watches DB sync_queue, writes to Obsidian vault.
    Processes queue asynchronously without blocking bot responses.
    """

    def __init__(self, db, vault: Vault, config):
        self.db = db
        self.vault = vault
        self.config = config
        self.formatter = ObsidianFormatter(
            vault.vault_path,
            config.agent_name,
            config.agent_emoji,
        )
        self.rest_client: Optional[ObsidianRestClient] = None
        self.running = False
        self.task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Start background sync loop."""
        if self.config.obsidian_rest_url:
            self.rest_client = ObsidianRestClient(
                self.config.obsidian_rest_url,
                self.config.obsidian_rest_token,
            )
            await self.rest_client.__aenter__()

        self.running = True
        self.task = asyncio.create_task(self._sync_loop())
        logger.info("Sync engine started")

    async def stop(self) -> None:
        """Stop sync loop gracefully."""
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        if self.rest_client:
            await self.rest_client.close()
        logger.info("Sync engine stopped")

    async def _sync_loop(self) -> None:
        """Main background loop — processes sync queue continuously."""
        while self.running:
            try:
                await self._process_queue()
                await asyncio.sleep(self.config.sync_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Sync loop error: {e}", exc_info=True)
                await asyncio.sleep(self.config.sync_interval * 2)

    async def _process_queue(self) -> None:
        """Dequeue and process pending sync items."""
        items = await self.db.dequeue_sync(self.config.sync_interval)
        for item in items:
            try:
                await self._handle_sync_item(item)
            except Exception as e:
                logger.error(f"Sync item failed (id={item.get('queue_id')}): {e}")
                await self.db.mark_sync_failed(item["queue_id"])

    async def _handle_sync_item(self, item: dict) -> None:
        """Process a single sync queue entry."""
        entity_type = item["entity_type"]
        action = item["action"]
        payload = item["payload"]

        if entity_type == "daily_note":
            await self._sync_daily_note(action, payload)
        elif entity_type == "memory_summary":
            await self._sync_memory_summary(action, payload)
        elif entity_type == "knowledge":
            await self._sync_knowledge(action, payload)
        elif entity_type == "profile":
            await self._sync_profile(action, payload)
        elif entity_type == "agent_identity":
            await self._sync_agent_identity(action, payload)
        else:
            logger.warning(f"Unknown entity type: {entity_type}")

    async def _sync_daily_note(self, action: str, payload: dict) -> None:
        """Synchronize daily note updates."""
        path = "Daily Note/{}".format(payload["date"])
        if action == "append":
            content = payload.get("content", "")
            await self.vault.append_to_note(path, content)
            # Trigger REST refresh if available
            if self.rest_client:
                await self.rest_client.vault_refresh()

    async def _sync_memory_summary(self, action: str, payload: dict) -> None:
        """Sync MEMORY.md with updated summary."""
        path = "Memory/MEMORY.md"
        content = payload.get("content", "")
        await self.vault.write_note(path, self.formatter.format_memory_note(content))
        if self.rest_client:
            await self.rest_client.vault_refresh()

    async def _sync_knowledge(self, action: str, payload: dict) -> None:
        """Sync Knowledge/<slug>.md note."""
        slug = payload["slug"]
        title = payload["title"]
        content = payload["content"]
        path = f"Knowledge/{slug}.md"
        formatted = self.formatter.format_knowledge_note(slug, title, content)
        await self.vault.write_note(path, formatted, overwrite=True)
        if self.rest_client:
            await self.rest_client.vault_refresh()

    async def _sync_profile(self, action: str, payload: dict) -> None:
        """Sync People/USER.md profile."""
        content = payload.get("content", "")
        path = "People/USER.md"
        await self.vault.write_note(path, self.formatter.format_user_profile(content))
        if self.rest_client:
            await self.rest_client.vault_refresh()

    async def _sync_agent_identity(self, action: str, payload: dict) -> None:
        """Sync Agent identity files."""
        # IDENTITY.md
        identity_content = self.formatter.format_agent_identity(
            self.config.agent_name,
            self.config.agent_vibe,
            self.config.agent_emoji,
        )
        await self.vault.write_note("Agent/IDENTITY.md", identity_content)

        # SOUL.md (condensed)
        soul_content = self.formatter.format_agent_soul(self.config.agent_soul)
        await self.vault.write_note("Agent/SOUL.md", soul_content)

        if self.rest_client:
            await self.rest_client.vault_refresh()

    # Public API for enqueueing sync work
    async def queue_daily_append(self, user_id: int, content: str) -> None:
        today = datetime.date.today().strftime("%Y-%m-%d")
        await self.db.enqueue_sync(
            "daily_note",
            str(user_id),
            "append",
            {"date": today, "content": content},
        )

    async def queue_memory_update(self, user_id: int, summary: str) -> None:
        await self.db.enqueue_sync(
            "memory_summary",
            str(user_id),
            "upsert",
            {"content": summary},
        )

    async def queue_knowledge_create(self, slug: str, title: str, content: str) -> None:
        await self.db.enqueue_sync(
            "knowledge",
            slug,
            "upsert",
            {"slug": slug, "title": title, "content": content},
        )

    async def queue_profile_update(self, user_id: int, profile: str) -> None:
        await self.db.enqueue_sync(
            "profile",
            str(user_id),
            "upsert",
            {"content": profile},
        )

    async def queue_identity_update(self) -> None:
        await self.db.enqueue_sync(
            "agent_identity",
            "identity",
            "upsert",
            {},
        )

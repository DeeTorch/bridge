"""Knowledge Extractor — pulls topics/facts from conversation, queues Knowledge notes."""
import logging
from typing import Optional

from llm.client import LLMClient
from memory.database import Database
from obsidian.sync import SyncEngine
from obsidian.formatter import ObsidianFormatter

logger = logging.getLogger(__name__)


class KnowledgeManager:
    """Extracts atomic knowledge from conversation and syncs to vault."""

    def __init__(self, llm: LLMClient, db: Database, sync_engine: SyncEngine, formatter: ObsidianFormatter):
        self.llm = llm
        self.db = db
        self.sync_engine = sync_engine
        self.formatter = formatter

    async def extract_and_queue(self, user_id: int, messages: list[dict]) -> list[dict]:
        """
        After an exchange, extract knowledge nuggets and queue for sync.
        Returns list of extracted knowledge items.
        """
        # Use the summarizer's extraction method
        from memory.summarizer import Summarizer
        summarizer = Summarizer(self.llm)
        extracted = await summarizer.extract_knowledge(messages[-4:])

        queued = []
        for item in extracted:
            slug = item["slug"]
            title = item["title"]
            content = item["content"]

            # Store in DB (for deduplication/lookup)
            await self.db.upsert_knowledge(slug, title, content)

            # Queue sync to vault
            await self.sync_engine.queue_knowledge_create(slug, title, content)
            queued.append({"slug": slug, "title": title})
            logger.info(f"Queued knowledge: {slug}")

        return queued

    async def search_knowledge(self, query: str) -> list[dict]:
        """Search knowledge entries (by title/slug) — optional future full-text."""
        all_entries = await self.db.list_knowledge()
        # Simple substring match for now
        results = [
            e for e in all_entries
            if query.lower() in e["slug"].lower() or query.lower() in e["title"].lower()
        ]
        return results

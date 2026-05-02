"""Heartbeat Scheduler — proactive messaging and periodic jobs."""
import asyncio
import datetime
import logging
from typing import Optional

from memory.database import Database
from obsidian.sync import SyncEngine

logger = logging.getLogger(__name__)


class HeartbeatScheduler:
    """
    Runs periodic jobs in background:
    - Periodic summarization of old messages
    - Daily note creation at midnight
    - Optional proactive check-ins
    """

    def __init__(self, db: Database, sync_engine: SyncEngine, config):
        self.db = db
        self.sync_engine = sync_engine
        self.config = config
        self.running = False
        self.task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Start the background heartbeat loop."""
        self.running = True
        self.task = asyncio.create_task(self._run())
        logger.info("Heartbeat scheduler started")

    async def stop(self) -> None:
        """Stop heartbeat loop."""
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info("Heartbeat scheduler stopped")

    async def _run(self) -> None:
        """Main loop — runs periodic checks."""
        while self.running:
            try:
                now = datetime.datetime.now()
                # Check for daily note rollover
                await self._check_daily_note(now)
                # Optionally trigger summarization
                # await self._periodic_summarize()
                await asyncio.sleep(self.config.heartbeat_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
                await asyncio.sleep(self.config.heartbeat_interval)

    async def _check_daily_note(self, now: datetime.datetime) -> None:
        """If it's just past midnight, ensure today's daily note exists."""
        # Simple approach: create placeholder if missing
        today = now.date()
        from obsidian.vault import Vault
        expected_path = f"Daily Note/{today.strftime('%Y-%m-%d')}.md"
        exists = await self.sync_engine.vault.note_exists(expected_path)
        if not exists:
            # Create empty daily note with header
            content = f"""---
title: "{today.strftime('%Y-%m-%d')}"
type: daily-note
tags: [daily, conversation, bridge-agent]
created: {today.isoformat()}T00:00:00
agent: "{self.config.agent_name}"
---

# 📅 {today.strftime('%Y-%m-%d')} — {now.strftime('%A')}

## Conversations

*(first entry pending)*
"""
            await self.sync_engine.vault.write_note(expected_path, content)
            logger.info(f"Created daily note for {today}")

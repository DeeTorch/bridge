"""User Profile Manager — reads/writes People/USER.md, updates from conversation."""
import logging
from typing import Optional

from llm.client import LLMClient
from memory.database import Database
from obsidian.sync import SyncEngine

logger = logging.getLogger(__name__)


class ProfileManager:
    """Extracts and maintains user profile from conversations."""

    def __init__(self, llm: LLMClient, db: Database, sync_engine: SyncEngine):
        self.llm = llm
        self.db = db
        self.sync_engine = sync_engine

    async def maybe_update_profile(self, user_id: int, messages: list[dict]) -> Optional[str]:
        """
        After sufficient conversation, infer and update user profile.
        Returns the new profile text if changed.
        """
        current = await self.db.get_profile(user_id)
        recent = " ".join([m["content"] for m in messages[-10:]])

        prompt = f"""Based on this conversation, update the user profile.

Current profile:
{current or "(none yet)"}

Recent conversation:
{recent}

Extract or update:
- Name (if mentioned)
- Occupation / projects
- Preferences (communication style, interests)
- Goals / ongoing work
- Any new important context

Write as a structured markdown profile (2–4 paragraphs). If no updates needed, reply with exactly "NO-CHANGE".

Updated profile:"""

        try:
            result = await self.llm.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=500,
            )
            if result.strip() == "NO-CHANGE":
                return None

            await self.db.upsert_profile(user_id, result)
            await self.sync_engine.queue_profile_update(user_id, result)
            logger.info(f"Updated profile for user {user_id}")
            return result
        except Exception as e:
            logger.error(f"Profile update failed: {e}")
            return None

    async def get_profile(self, user_id: int) -> Optional[str]:
        return await self.db.get_profile(user_id)

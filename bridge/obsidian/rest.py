"""REST API client for Obsidian — triggers live refresh and opens notes."""
import json
import logging
from typing import Optional

import aiohttp

logger = logging.getLogger(__name__)


class ObsidianRestError(Exception):
    """REST API call failed."""


class ObsidianRestClient:
    """Client for Obsidian REST Plugin — optional but nice to have."""

    def __init__(self, base_url: str, token: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        self.session = aiohttp.ClientSession(headers=headers)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()

    async def vault_refresh(self) -> bool:
        """Trigger full vault refresh — returns success."""
        try:
            async with self.session.post(f"{self.base_url}/vault/refresh") as resp:
                resp.raise_for_status()
                logger.info("Obsidian vault refresh triggered via REST")
                return True
        except Exception as e:
            logger.warning(f"Vault refresh failed: {e}")
            return False

    async def open_note(self, path: str) -> bool:
        """
        Open a note in Obsidian (reveal in sidebar).
        Path is relative to vault root, e.g. "Daily Notes/2026-05-02.md".
        """
        try:
            payload = {"path": path}
            async with self.session.post(
                f"{self.base_url}/file/open",
                json=payload,
            ) as resp:
                resp.raise_for_status()
                logger.info(f"Opened note in Obsidian: {path}")
                return True
        except Exception as e:
            logger.warning(f"Failed to open note {path}: {e}")
            return False

    async def get_note_content(self, path: str) -> Optional[str]:
        """Fetch raw markdown of a note."""
        try:
            async with self.session.get(f"{self.base_url}/file/content?path={path}") as resp:
                resp.raise_for_status()
                return await resp.text()
        except Exception as e:
            logger.warning(f"Failed to fetch note {path}: {e}")
            return None

    async def create_note(self, path: str, content: str, overwrite: bool = False) -> bool:
        """Create a new note in the vault."""
        try:
            payload = {"path": path, "content": content, "overwrite": overwrite}
            async with self.session.post(
                f"{self.base_url}/file/write",
                json=payload,
            ) as resp:
                resp.raise_for_status()
                logger.info(f"Created note: {path}")
                return True
        except Exception as e:
            logger.warning(f"Failed to create note {path}: {e}")
            return False

"""Agent Identity — reads/writes Agent/IDENTITY.md (static metadata)."""
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class IdentityManager:
    """Manages agent identity files in the vault."""

    def __init__(self, vault, formatter, config):
        self.vault = vault
        self.formatter = formatter
        self.config = config

    async def ensure_identity_files(self) -> None:
        """Write IDENTITY.md and SOUL.md on startup (idempotent)."""
        await self._write_identity()
        await self._write_soul()

    async def _write_identity(self) -> None:
        content = self.formatter.format_agent_identity(
            self.config.agent_name,
            self.config.agent_vibe,
            self.config.agent_emoji,
        )
        await self.vault.write_note("Agent/IDENTITY.md", content, overwrite=True)

    async def _write_soul(self) -> None:
        content = self.formatter.format_agent_soul(self.config.agent_soul)
        await self.vault.write_note("Agent/SOUL.md", content, overwrite=True)

    async def get_identity(self) -> Optional[str]:
        """Read current identity note."""
        return await self.vault.read_note("Agent/IDENTITY.md")

    async def get_soul(self) -> Optional[str]:
        """Read current soul directive."""
        return await self.vault.read_note("Agent/SOUL.md")

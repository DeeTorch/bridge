"""
Configuration management with environment validation.
All env vars validated at startup — fail fast if missing.
"""
import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class Config:
    # Required fields first (no defaults)
    telegram_bot_token: str
    allowed_users: list[int]
    lm_studio_base_url: str
    lm_studio_model: str
    obsidian_vault_path: str

    # Optional fields with defaults
    lm_studio_timeout: int = 120
    lm_studio_max_retries: int = 3
    obsidian_rest_url: Optional[str] = None
    obsidian_rest_token: Optional[str] = None
    agent_name: str = "Bridge"
    agent_vibe: str = "helpful, concise, friendly"
    agent_emoji: str = "🌉"
    agent_soul: str = "You are Bridge, a personal AI assistant. You help your user think, remember, and create. Be direct, useful, and kind."
    heartbeat_interval: int = 300
    sync_interval: int = 10
    typing_indicator_interval: int = 4

    @classmethod
    def from_env(cls) -> "Config":
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not token:
            raise ValueError("TELEGRAM_BOT_TOKEN is required")

        allowed_raw = os.getenv("ALLOWED_USERS", "")
        allowed = [int(u.strip()) for u in allowed_raw.split(",") if u.strip()]

        lm_url = os.getenv("LM_STUDIO_BASE_URL", "http://localhost:1234/v1")
        lm_model = os.getenv("LM_STUDIO_MODEL", "local-model")

        vault_path = os.getenv("OBSIDIAN_VAULT_PATH", "./BrainVault")
        if not vault_path:
            raise ValueError("OBSIDIAN_VAULT_PATH is required")

        rest_url = os.getenv("OBSIDIAN_REST_URL")
        rest_token = os.getenv("OBSIDIAN_REST_TOKEN")

        agent_name = os.getenv("AGENT_NAME", "Bridge")
        agent_vibe = os.getenv("AGENT_VIBE", "helpful, concise, friendly")
        agent_emoji = os.getenv("AGENT_EMOJI", "🌉")
        agent_soul = os.getenv("AGENT_SOUL", cls.agent_soul)

        heartbeat = int(os.getenv("HEARTBEAT_INTERVAL", "300"))
        sync_int = int(os.getenv("SYNC_INTERVAL", "10"))
        typing_int = int(os.getenv("TYPING_INDICATOR_INTERVAL", "4"))

        return cls(
            telegram_bot_token=token,
            allowed_users=allowed,
            lm_studio_base_url=lm_url,
            lm_studio_model=lm_model,
            obsidian_vault_path=vault_path,
            obsidian_rest_url=rest_url,
            obsidian_rest_token=rest_token,
            agent_name=agent_name,
            agent_vibe=agent_vibe,
            agent_emoji=agent_emoji,
            agent_soul=agent_soul,
            heartbeat_interval=heartbeat,
            sync_interval=sync_int,
            typing_indicator_interval=typing_int,
        )

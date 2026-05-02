"""Main entry point — initializes all subsystems and starts the bot."""
import asyncio
import logging
import signal
import sys
from pathlib import Path

from config import Config
from bot.handlers import setup_bot
from memory.database import Database
from obsidian.vault import Vault
from obsidian.sync import SyncEngine
from agent.heartbeat import HeartbeatScheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


class BridgeApp:
    """Unified app coordinating bot, memory, sync, and agent subsystems."""

    def __init__(self, config: Config):
        self.config = config
        vault_path = Path(config.obsidian_vault_path)
        self.db: Database = Database(vault_path.parent / "bridge.db")
        self.vault: Vault = Vault(vault_path)
        self.sync_engine: SyncEngine = SyncEngine(self.db, self.vault, config)
        self.heartbeat: HeartbeatScheduler = HeartbeatScheduler(self.db, self.sync_engine, config)
        self.application = None
        self.running = False

    async def initialize(self) -> None:
        logger.info("Initializing Bridge...")
        await self.db.initialize()
        await self.vault.initialize()
        await self.sync_engine.start()
        # Ensure agent identity files exist
        from agent.identity import IdentityManager
        from obsidian.formatter import ObsidianFormatter
        formatter = ObsidianFormatter(
            self.vault.vault_path,
            self.config.agent_name,
            self.config.agent_emoji,
        )
        identity_mgr = IdentityManager(self.vault, formatter, self.config)
        await identity_mgr.ensure_identity_files()
        self.application = setup_bot(self.config, self.db, self.sync_engine)
        assert self.application is not None
        logger.info("Bridge initialized successfully")

    async def run(self) -> None:
        self.running = True
        await self.initialize()
        assert self.application is not None  # initialized in initialize()

        logger.info("Starting bot polling...")
        async with self.application:
            await self.application.start()
            await self.application.updater.start_polling(drop_pending_updates=True)
            logger.info("Bot is now running")

            try:
                while self.running:
                    await asyncio.sleep(1)
            except (KeyboardInterrupt, SystemExit):
                logger.info("Shutdown signal received")
            finally:
                await self.shutdown()

    async def shutdown(self) -> None:
        logger.info("Shutting down...")
        self.running = False
        await self.sync_engine.stop()
        await self.heartbeat.stop()
        assert self.application is not None
        await self.application.updater.stop()
        await self.application.stop()
        await self.db.close()
        logger.info("Shutdown complete")


async def main() -> None:
    config = Config.from_env()
    app = BridgeApp(config)

    # Handle graceful shutdown
    loop = asyncio.get_event_loop()
    stop_signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)
    for s in stop_signals:
        loop.add_signal_handler(s, lambda: asyncio.create_task(app.shutdown()))

    await app.run()


if __name__ == "__main__":
    asyncio.run(main())

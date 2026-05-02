"""Telegram bot handlers — thin wrappers that delegate to agent logic."""
import asyncio
import datetime
import logging
from typing import Optional

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)

from config import Config
from memory.database import Database
from llm.client import LLMClient
from obsidian.sync import SyncEngine
from agent.identity import IdentityManager
from agent.profile import ProfileManager
from agent.knowledge import KnowledgeManager

logger = logging.getLogger(__name__)


class BridgeBot:
    """Encapsulates bot logic with dependencies injected."""

    def __init__(
        self,
        config: Config,
        db: Database,
        llm: LLMClient,
        sync_engine: SyncEngine,
        identity_mgr: IdentityManager,
        profile_mgr: ProfileManager,
        knowledge_mgr: KnowledgeManager,
    ):
        self.config = config
        self.db = db
        self.llm = llm
        self.sync = sync_engine
        self.identity = identity_mgr
        self.profile = profile_mgr
        self.knowledge = knowledge_mgr
        self._typing_tasks: dict[int, asyncio.Task] = {}

    async def handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_user
        if user.id not in self.config.allowed_users:
            await update.message.reply_text("🚫 Access denied.")
            return

        # Ensure vault identity files exist
        await self.identity.ensure_identity_files()

        # Check if this is a returning user (has existing messages)
        count = await self.db.count_messages(user.id)
        if count == 0:
            welcome = (
                f"{self.config.agent_emoji} Welcome! I'm {self.config.agent_name}, your personal AI bridge to Obsidian.\n\n"
                f"Every conversation is saved, organized, and linked in your BrainVault.\n\n"
                f"Try asking me anything — I'll remember for next time."
            )
        else:
            summary = await self.db.get_summary(user.id)
            summary_preview = f"\n\n*Last memory:* {summary[0][:100]}..." if summary else ""
            welcome = (
                f"👋 Welcome back! I'm {self.config.agent_name}.{summary_preview}\n\n"
                f"Your memory is intact. What's on your mind?"
            )

        await update.message.reply_text(welcome, parse_mode="Markdown")

    async def handle_clear(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_user
        if user.id not in self.config.allowed_users:
            return

        await self.db.clear_messages(user.id)
        await update.message.reply_text("🧹 Session memory cleared. Fresh start.")

    async def handle_who(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_user
        if user.id not in self.config.allowed_users:
            return

        identity = await self.identity.get_identity() or "(not found)"
        soul = await self.identity.get_soul() or "(not found)"

        # Truncate for display
        identity_preview = identity[:200] + "..." if len(identity) > 200 else identity
        soul_preview = soul[:200] + "..." if len(soul) > 200 else soul

        response = (
            f"🤖 **{self.config.agent_name}** {self.config.agent_emoji}\n\n"
            f"**Vibe:** {self.config.agent_vibe}\n\n"
            f"**Identity Card:**\n{identity_preview}\n\n"
            f"**Soul Directive:**\n{soul_preview}"
        )
        await update.message.reply_text(response, parse_mode="Markdown")

    async def handle_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_user
        if user.id not in self.config.allowed_users:
            return

        msg_count = await self.db.count_messages(user.id)
        summary = await self.db.get_summary(user.id)
        summary_tokens = summary[1] if summary else 0
        profile = await self.db.get_profile(user.id)
        knowledge = await self.db.list_knowledge()

        status_lines = [
            "📊 **Bridge Status**",
            f"• Messages: {msg_count}",
            f"• Summary: {summary_tokens} tokens",
            f"• Profile: {'✅ set' if profile else '❌ empty'}",
            f"• Knowledge entries: {len(knowledge)}",
            f"• Vault: `{self.config.obsidian_vault_path}`",
            f"• LM Studio: `{self.config.lm_studio_base_url}`",
        ]
        await update.message.reply_text("\n".join(status_lines), parse_mode="Markdown")

    async def handle_remember(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_user
        if user.id not in self.config.allowed_users:
            return

        text = " ".join(context.args) if context.args else ""
        if not text:
            await update.message.reply_text("Usage: /remember <thing to remember>")
            return

        # Append to MEMORY.md directly
        entry = f"- {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}: {text}"
        await self.db.append_message(user.id, "user", text)  # regular message path also captures
        await self.sync.vault.append_to_note("Memory/MEMORY.md", entry)
        await update.message.reply_text(f"✅ Remembered: {text}")

    async def handle_open(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_user
        if user.id not in self.config.allowed_users:
            return

        if not context.args:
            await update.message.reply_text("Usage: /open <note-path>\nExample: /open Daily Note/2026-05-02.md")
            return

        note_path = context.args[0]
        if not await self.sync.vault.note_exists(note_path):
            await update.message.reply_text(f"❌ Note not found: {note_path}")
            return

        if self.sync.rest_client:
            success = await self.sync.rest_client.open_note(note_path)
            if success:
                await update.message.reply_text(f"📂 Opened: {note_path}")
            else:
                await update.message.reply_text(f"⚠️ Could not open note (REST error)")
        else:
            await update.message.reply_text("❌ REST plugin not configured. Set OBSIDIAN_REST_URL in .env")

    async def handle_sync(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_user
        if user.id not in self.config.allowed_users:
            return

        await update.message.reply_text("🔄 Syncing vault...")
        try:
            # Force a full job queue drain
            await self.sync._process_queue()
            await update.message.reply_text("✅ Sync complete")
        except Exception as e:
            logger.error(f"Manual sync failed: {e}")
            await update.message.reply_text(f"❌ Sync error: {e}")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Main message handler — full agent logic."""
        user = update.effective_user
        if user.id not in self.config.allowed_users:
            return

        message = update.message
        if not message or not message.text:
            return

        user_text = message.text.strip()
        if not user_text:
            return

        # 1. Save user message
        await self.db.append_message(user.id, "user", user_text)

        # 2. Build context
        recent_messages = await self.db.get_messages(user.id, limit=20)
        summary = await self.db.get_summary(user.id)
        profile = await self.db.get_profile(user.id)

        context_messages = []
        if summary:
            context_messages.append({"role": "system", "content": f"User summary: {summary[0]}"})
        if profile:
            context_messages.append({"role": "system", "content": f"User profile: {profile}"})
        context_messages.extend([{"role": m["role"], "content": m["content"]} for m in recent_messages])

        # 3. Prepare typing indicator
        status_msg = await message.reply_text(f"{self.config.agent_emoji} thinking...")

        # Start looping typing action
        typing_done = asyncio.Event()

        async def typing_loop() -> None:
            while not typing_done.is_set():
                try:
                    await context.bot.send_chat_action(chat_id=user.id, action="typing")
                except Exception:
                    pass
                try:
                    await asyncio.wait_for(typing_done.wait(), timeout=self.config.typing_indicator_interval)
                except asyncio.TimeoutError:
                    pass

        typing_task = asyncio.create_task(typing_loop())

        # 4. Call LLM (no callback needed)
        try:
            response = await self.llm.chat(
                messages=context_messages,
                system_prompt=self.config.agent_soul,
            )
        except Exception as e:
            typing_done.set()
            await typing_task
            logger.error(f"LLM error for user {user.id}: {e}")
            await status_msg.edit_text(f"❌ LLM error: {e}")
            return

        # Stop typing indicator
        typing_done.set()
        await typing_task

        # Update status to indicate response ready
        try:
            await status_msg.edit_text("✅ Response ready")
        except Exception:
            pass

        # 5. Save assistant response
        await self.db.append_message(user.id, "assistant", response)

        # 6. Format daily note entries
        now = datetime.datetime.now()
        user_entry = {
            "time": now,
            "speaker": user.first_name or "User",
            "text": user_text,
        }
        bot_entry = {
            "time": now,
            "speaker": f"{self.config.agent_emoji} {self.config.agent_name}",
            "text": response,
        }

        from obsidian.formatter import ObsidianFormatter
        formatter = ObsidianFormatter(
            self.sync.vault.vault_path,
            self.config.agent_name,
            self.config.agent_emoji,
        )

        # Append both to daily note
        daily_path = self.sync.vault.get_todays_note_path()
        user_block = formatter.format_daily_note_append(user_entry)
        bot_block = formatter.format_daily_note_append(bot_entry)
        await self.sync.vault.append_to_note(daily_path, user_block + "\n\n---\n\n" + bot_block)

        # 7. Queue knowledge extraction and profile update (async)
        recent_for_extract = [user_entry, bot_entry]
        asyncio.create_task(self._post_process(user.id, recent_for_extract))

        # 8. Send response to user
        await message.reply_text(response)

        # Update status
        try:
            await status_msg.delete()
        except Exception:
            pass

    async def _post_process(self, user_id: int, recent_exchange: list[dict]) -> None:
        """Async background tasks: knowledge extraction, profile updates, summarization."""
        try:
            # Extract knowledge
            await self.knowledge.extract_and_queue(user_id, recent_exchange)
            # Maybe update profile
            all_msgs = await self.db.get_messages(user_id, limit=50)
            await self.profile.maybe_update_profile(user_id, all_msgs)
            # Maybe summarize
            from memory.summarizer import Summarizer
            summarizer = Summarizer(self.llm)
            await summarizer.maybe_summarize(user_id, self.db)
        except Exception as e:
            logger.error(f"Post-processing error: {e}")


def setup_bot(
    config: Config,
    db: Database,
    sync_engine: SyncEngine,
) -> Application:
    """Construct and configure the python-telegram-bot Application."""
    # Create LLM client
    llm = LLMClient(
        base_url=config.lm_studio_base_url,
        model=config.lm_studio_model,
        timeout=config.lm_studio_timeout,
        max_retries=config.lm_studio_max_retries,
    )

    # Create formatter
    from obsidian.formatter import ObsidianFormatter
    formatter = ObsidianFormatter(
        sync_engine.vault.vault_path,
        config.agent_name,
        config.agent_emoji,
    )

    # Create agent managers
    identity_mgr = IdentityManager(sync_engine.vault, formatter, config)
    profile_mgr = ProfileManager(llm, db, sync_engine)
    knowledge_mgr = KnowledgeManager(llm, db, sync_engine, formatter)

    # Create BridgeBot
    bot = BridgeBot(
        config=config,
        db=db,
        llm=llm,
        sync_engine=sync_engine,
        identity_mgr=identity_mgr,
        profile_mgr=profile_mgr,
        knowledge_mgr=knowledge_mgr,
    )

    # Build Telegram application
    application = Application.builder().token(config.telegram_bot_token).build()

    # Register handlers
    application.add_handler(CommandHandler("start", bot.handle_start))
    application.add_handler(CommandHandler("clear", bot.handle_clear))
    application.add_handler(CommandHandler("status", bot.handle_status))
    application.add_handler(CommandHandler("who", bot.handle_who))
    application.add_handler(CommandHandler("remember", bot.handle_remember))
    application.add_handler(CommandHandler("open", bot.handle_open))
    application.add_handler(CommandHandler("sync", bot.handle_sync))

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_message))

    return application

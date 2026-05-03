# Active Context: Hybrid Web + AI Agent Platform

## Current State

**Frontend (Next.js)**: ✅ Clean Next.js 16 + TypeScript + Tailwind CSS 4 starter ready for UI development.

**Backend Agent (Bridge)**: ✅ Fully implemented Telegram bot with two-layer memory (SQLite + Obsidian vault). The agent:
- Listens for Telegram messages
- Maintains per-user conversation history in SQLite (hot cache)
- Async-syncs to Obsidian vault (cold store) with rich markdown, wikilinks, frontmatter
- Extracts knowledge nuggets and updates user profile automatically
- Provides commands: /start, /clear, /status, /who, /remember, /open, /sync
- Runs proactive heartbeat (daily note rollover, periodic summarization)

**Observability**: Vault structure created under `BrainVault/` with Daily Notes, Memory, People, Agent, Knowledge.

**Configuration**: Env-driven via `.env` (TELEGRAM_BOT_TOKEN, ALLOWED_USERS, LM_STUDIO_BASE_URL, OBSIDIAN_VAULT_PATH, optional REST plugin).

**Integration Points**: Node front-end can later read from the same SQLite DB or vault for dashboard views.

## Recently Completed

- [x] Next.js 16 base setup with App Router, TypeScript strict mode, Tailwind CSS 4
- [x] ESLint configuration
- [x] Bridge Telegram agent fully implemented (see `bridge/` directory)
  - LLM client with retry logic and typing indicator
  - SQLite database layer (messages, summaries, knowledge, profile, sync queue)
  - Summarizer (rolling compression + knowledge extraction)
  - Obsidian vault operations, formatter, REST client
  - Async sync engine processing SQLite → Obsidian
  - Agent submodules: identity, profile, knowledge, heartbeat
  - Telegram bot handlers with all commands
- [x] Obsidian vault directory structure and base files created
- [x] Created comprehensive README.md documenting the hybrid web + AI agent platform
- [x] Designed and built elite-level to-do list outlining next phases for Bridge Agent system evolution

## Current Structure

| File/Directory | Purpose | Status |
|----------------|---------|--------|
| `src/app/` | Next.js frontend (pending UI work) | ✅ Ready |
| `bridge/` | Python Telegram bridge agent | ✅ Complete |
| `BrainVault/` | Obsidian vault (SQLite at `bridge.db`) | ✅ Initialized |
| `.kilocode/` | AI context & recipes | ✅ Ready |

## Current Focus

The Bridge agent is operational and can be run with:
```bash
cd bridge
bun install  # actually Python: pip install -r requirements.txt (or use venv)
python main.py
```

Frontend development can proceed independently; optional future integration: read vault for live dashboard.

## Session History

| Date | Changes |
|------|---------|
| 2026-05-02 | Added Bridge Telegram agent: Python service with SQLite hot cache, async Obsidian sync, LLM client, summarization, knowledge extraction |
| Initial | Next.js starter template created with base setup |

